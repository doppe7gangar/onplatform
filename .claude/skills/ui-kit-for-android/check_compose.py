#!/usr/bin/env python3
"""Check Jetpack Compose code against Material 3 before it ships.

Reads Kotlin source and reports what can be decided from the code alone:
text under the 11 sp floor, colours written in instead of taken from the
theme's roles, icon-only buttons with nothing for TalkBack to read,
clickable things smaller than the 48 dp target, and Material 2 components
where Material 3 has its own. Each finding is one of three kinds, kept
apart because they are not equally serious:

  violation  the Material 3 kit records the number or the rule and the
             code breaks it
  guidance   Material 3 prefers otherwise, or the answer depends on
             something the code can't show; deviating can be right, with
             a reason
  api        not a design matter: the older library or API. Fix it, but
             don't file it under design.

The numbers are the ones in this skill's SKILL.md, measured from Google's
Material 3 Design Kit, and each finding links the Material page to read.
Whether a screen's hierarchy, colour or motion is right needs eyes, not a
regex; review those.

    python3 check_compose.py app/src/main/java/
    python3 check_compose.py HomeScreen.kt --json

Exit status is 1 if anything is a violation, 0 otherwise.
"""

import argparse
import json
import os
import re
import sys

TYPE = "https://m3.material.io/styles/typography/type-scale-tokens"
ROLES = "https://m3.material.io/styles/color/roles"
ICON_BUTTONS = "https://m3.material.io/components/icon-buttons/accessibility"
TARGETS = "https://m3.material.io/foundations/designing/structure"
COMPOSE_M3 = "https://developer.android.com/develop/ui/compose/designsystems/material2-material3"

# Colour constants that aren't a colour choice.
NEUTRAL = {"Transparent", "Unspecified"}
# Buttons whose only content is often an icon.
ICON_ONLY = ("IconButton", "FilledIconButton", "FilledTonalIconButton", "OutlinedIconButton",
             "IconToggleButton", "FilledIconToggleButton", "FilledTonalIconToggleButton",
             "OutlinedIconToggleButton", "FloatingActionButton", "SmallFloatingActionButton",
             "LargeFloatingActionButton")


def mask(src):
    """Blank comments and string contents, keeping every offset in place,
    so a comment or a string can't set a rule off."""
    out, i, n = list(src), 0, len(src)

    def blank(a, b):
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            blank(i, j)
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            blank(i, j)
            i = j
        elif src.startswith('"""', i):
            j = src.find('"""', i + 3)
            j = n if j < 0 else j + 3
            blank(i + 3, max(i + 3, j - 3))
            i = j
        elif src[i] == '"':
            j = i + 1
            while j < n and src[j] != '"' and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            blank(i + 1, min(j, n))
            i = j + 1
        elif src[i] == "'":
            j = i + 1
            while j < n and src[j] != "'" and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            blank(i + 1, min(j, n))
            i = j + 1
        else:
            i += 1
    return "".join(out)


def closing(code, open_at):
    """Index of the bracket that closes the one at open_at."""
    pairs = {"(": ")", "{": "}", "[": "]"}
    want, depth = pairs[code[open_at]], 0
    for k in range(open_at, len(code)):
        c = code[k]
        if c in pairs:
            depth += 1
        elif c in pairs.values():
            depth -= 1
            if depth == 0:
                return k
    return len(code)


def call_extent(code, name_end):
    """From just after a call's name: the end of its arguments and its
    trailing lambda, if any."""
    k = name_end
    while k < len(code) and code[k] in " \t":
        k += 1
    if k < len(code) and code[k] == "(":
        k = closing(code, k) + 1
        j = k
        while j < len(code) and code[j] in " \t\n":
            j += 1
        if j < len(code) and code[j] == "{":
            return closing(code, j) + 1
        return k
    if k < len(code) and code[k] == "{":
        return closing(code, k) + 1
    return k


class File:
    def __init__(self, path, src):
        self.path, self.src, self.code = path, src, mask(src)

    def line(self, offset):
        return self.src.count("\n", 0, offset) + 1


def finding(f, offset, kind, message, page=""):
    return {"path": f.path, "line": f.line(offset), "kind": kind, "message": message, "page": page}


def is_theme_file(f):
    """Where a scheme is defined, literal colours are the point."""
    name = os.path.basename(f.path)
    return (re.search(r"\b(light|dark)ColorScheme\s*\(", f.code) is not None
            or name in ("Color.kt", "Colors.kt", "Theme.kt"))


def check(f):
    out, code = [], f.code

    # Text sizes: the floor, then any literal size at all.
    for m in re.finditer(r"\bfontSize\s*=\s*(\d+(?:\.\d+)?)f?\s*\.\s*sp\b", code):
        size = float(m.group(1))
        if size < 11:
            out.append(finding(f, m.start(), "violation",
                f"{m.group(1)} sp text is under label-small's 11 sp, the smallest style in the "
                "Material 3 type scale.", TYPE))
        else:
            out.append(finding(f, m.start(), "guidance",
                f"A fixed {m.group(1)} sp: take the size from MaterialTheme.typography so it "
                "stays on the type scale.", TYPE))

    # Colours written into components instead of read from the scheme.
    if not is_theme_file(f):
        for m in re.finditer(r"\bColor\s*\(\s*(0x[0-9A-Fa-f]{6,8}|red\s*=|\d)", code):
            out.append(finding(f, m.start(), "violation",
                "A colour written into a component: use a role such as "
                "MaterialTheme.colorScheme.primary, so light, dark and the brand theme follow.",
                ROLES))
        for m in re.finditer(r"\bColor\.(\w+)\b", code):
            if m.group(1)[0].isupper() and m.group(1) not in NEUTRAL:
                out.append(finding(f, m.start(), "violation",
                    f"Color.{m.group(1)} in a component: use a colour role from "
                    "MaterialTheme.colorScheme instead.", ROLES))

    # Icon-only buttons with nothing for TalkBack to say.
    for m in re.finditer(r"\b(" + "|".join(ICON_ONLY) + r")\b(?=\s*[({])", code):
        end = call_extent(code, m.end())
        body = code[m.end():end]
        silent = re.search(r"\bcontentDescription\s*=\s*null\b", body)
        labelled = re.search(r"\bText\s*\(|\bsemantics\b|\bcontentDescription\s*=\s*(?!null\b)\S",
                             body)
        if silent and not labelled:
            out.append(finding(f, m.start(), "violation",
                f"{m.group(1)} with only an icon and contentDescription = null: TalkBack has "
                "nothing to read. Describe the action, e.g. contentDescription = \"Search\".",
                ICON_BUTTONS))

    # Clickable things smaller than the 48 dp target.
    for m in re.finditer(r"\.\s*clickable\b|\.\s*toggleable\b|\.\s*selectable\b", code):
        start = code.rfind("Modifier", 0, m.start())
        if start < 0 or "\n\n" in code[start:m.start()]:
            continue
        chain_end = m.end()
        nxt = re.compile(r"\s*\.\s*\w+").match(code, chain_end)
        while nxt:
            chain_end = nxt.end()
            k = chain_end
            while k < len(code) and code[k] in " \t":
                k += 1
            if k < len(code) and code[k] in "({":
                chain_end = closing(code, k) + 1
            nxt = re.compile(r"\s*\.\s*\w+").match(code, chain_end)
        chain = code[start:chain_end]
        if "minimumInteractiveComponentSize" in chain:
            continue
        for s in re.finditer(r"\.\s*(?:size|height|width|requiredSize)\s*\(\s*(\d+(?:\.\d+)?)\s*\.\s*dp",
                             chain):
            if float(s.group(1)) < 48:
                out.append(finding(f, start + s.start(), "violation",
                    f"A clickable {s.group(1)} dp element: Material 3 targets are 48 dp. "
                    "Keep the visible size and add Modifier.minimumInteractiveComponentSize(), "
                    "or pad it out to 48 dp.", TARGETS))
                break

    # Material 2 where Material 3 has its own.
    for m in re.finditer(r"^\s*import\s+androidx\.compose\.material\.(?!icons\b|ripple\b)(\w+)",
                         code, re.M):
        out.append(finding(f, m.start(), "api",
            f"androidx.compose.material.{m.group(1)} is Material 2: use "
            "androidx.compose.material3, or it won't take the Material 3 theme.", COMPOSE_M3))
    return out


def kotlin_files(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("build", "generated")]
                for name in sorted(files):
                    if name.endswith(".kt"):
                        yield os.path.join(root, name)
        else:
            yield p


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="+", help="Kotlin files or folders")
    ap.add_argument("--json", action="store_true", help="print findings as JSON")
    a = ap.parse_args()

    found = []
    for path in kotlin_files(a.paths):
        with open(path, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        if "androidx.compose" not in src and "@Composable" not in src:
            continue
        found += check(File(path, src))
    found.sort(key=lambda x: (x["path"], x["line"]))

    if a.json:
        print(json.dumps(found, indent=1))
    else:
        order = {"violation": 0, "guidance": 1, "api": 2}
        for kind in sorted({x["kind"] for x in found}, key=order.get):
            print(f"\n{kind.upper()}")
            for x in (y for y in found if y["kind"] == kind):
                where = f"  ({x['page']})" if x["page"] else ""
                print(f"  {x['path']}:{x['line']}  {x['message']}{where}")
        counts = {k: sum(x["kind"] == k for x in found) for k in order}
        print(f"\n{counts['violation']} violations, {counts['guidance']} guidance, "
              f"{counts['api']} API issues")
    return 1 if any(x["kind"] == "violation" for x in found) else 0


if __name__ == "__main__":
    sys.exit(main())

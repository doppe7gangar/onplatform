#!/usr/bin/env python3
"""Check every third-party file the repo ships against the licence NOTICE gives it.

    python3 scripts/check_licences.py                       # what CI runs on every push
    python3 scripts/check_licences.py --upstream            # also compare the icons with their source
    python3 scripts/check_licences.py --json licences.json  # the inventory, for a release

For each third-party component: its files are where NOTICE says; its
licence text sits beside them and is that licence word for word (the
official text, allowing only the variants found in the wild: "&" for
"AND" in the OFL, braces for brackets in Apache's appendix); each font's
own name table names the same family, copyright holder and licence; and
NOTICE mentions it. Every font, image and icon file git tracks belongs to
a component here or to the repo's own work, so nothing third-party
arrives without a line in NOTICE. Every skill folder carries the repo's
LICENSE, unchanged.

--upstream fetches Material Symbols from Iconify's icon-sets repository,
at the commit recorded below, and requires every outline and fill the
Android kit ships to match it path for path. Names in names.txt that the
set doesn't have are reported. It needs the network; CI runs it on
release.

This checks the files against their licences, not anyone's use of them.
"""

import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = ".claude/skills"

# The licence texts, normalised (whitespace collapsed, the known variants
# folded), as published: Apache 2.0 from apache.org, OFL 1.1 from
# openfontlicense.org, from "PREAMBLE" on.
APACHE_SHA = "0ffddef9e48f8a09aed5caf2d44f7ba1c1be2d9b8e0a6f693b1635b2d5566645"
OFL_SHA = "65a67a379d9157a5d3e26b95313206afe983db9743688fc98d9545c9f24bbe7d"
MIT_CLAUSES = ["Permission is hereby granted, free of charge, to any person obtaining a copy",
               "The above copyright notice and this permission notice shall be included in all",
               'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND']

ICONIFY_COMMIT = "38ad5fc347ddedc4db4ad66038009f920398a621"
ICONIFY_URL = ("https://raw.githubusercontent.com/iconify/icon-sets/"
               f"{ICONIFY_COMMIT}/json/material-symbols.json")

COMPONENTS = [
    {"name": "Inter", "licence": "OFL-1.1",
     "files": [f"{SKILLS}/ui-kit-for-apple-platforms/fonts/InterVariable.woff2",
               f"{SKILLS}/ui-kit-for-apple-platforms/fonts/InterVariable-Italic.woff2"],
     "licence_file": f"{SKILLS}/ui-kit-for-apple-platforms/fonts/LICENSE-Inter.txt",
     "holder": "The Inter Project Authors", "family": "Inter",
     "source": "https://github.com/rsms/inter"},
    {"name": "Roboto", "licence": "OFL-1.1",
     "files": [f"{SKILLS}/ui-kit-for-android/fonts/roboto-*.woff2"],
     "licence_file": f"{SKILLS}/ui-kit-for-android/fonts/LICENSE-Roboto.txt",
     "holder": "The Roboto Project Authors", "family": "Roboto",
     "source": "https://github.com/googlefonts/roboto-classic"},
    {"name": "Material Symbols", "licence": "Apache-2.0",
     "files": [f"{SKILLS}/ui-kit-for-android/icons/material-symbols.json",
               f"{SKILLS}/ui-kit-for-android/icons/names.txt"],
     "licence_file": f"{SKILLS}/ui-kit-for-android/icons/LICENSE-Material-Symbols.txt",
     "holder": "Google",
     "source": "https://github.com/google/material-design-icons, on a 24-unit grid as "
               f"packaged by Iconify (github.com/iconify/icon-sets at {ICONIFY_COMMIT[:7]})"},
    {"name": "motion-for-apple-platforms references", "licence": "MIT",
     "files": [f"{SKILLS}/motion-for-apple-platforms/references/*.md"],
     "licence_file": f"{SKILLS}/motion-for-apple-platforms/LICENSE.txt",
     "holder": "s1gmamale1", "source": "apple-design-skills (skills/apple-design-motion)"},
]

# The repo's own binary files: NOTICE lists them as original work.
ORIGINAL = [re.compile(r"^docs/(iphone|ipad|mac|android)\.png$"),
            re.compile(r"^\.claude-plugin/icon\.png$")]
BINARY = re.compile(r"\.(png|jpe?g|gif|webp|heic|tiff?|bmp|ico|pdf|psd|sketch|fig|svg|"
                    r"ttf|otf|woff2?|eot|mp4|mov)$", re.I)
LICENCE_NAME = re.compile(r"(^|/)(LICEN[CS]E|COPYING|NOTICE)([-._][^/]*)?$", re.I)

PROBLEMS, NOTES = [], []


def problem(msg):
    PROBLEMS.append(msg)


def norm(text, kind):
    t = re.sub(r"\s+", " ", text).strip()
    if kind == "OFL-1.1":
        t = t.replace("PERMISSION AND CONDITIONS", "PERMISSION & CONDITIONS")
        i = t.find("PREAMBLE")
        return t[i:] if i >= 0 else t
    if kind == "Apache-2.0":
        i = t.find("Apache License")
        t = t[i:] if i >= 0 else t
        return t.replace('"{}"', '"[]"').replace("{yyyy} {name of copyright owner}",
                                                  "[yyyy] [name of copyright owner]")
    return t


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tracked():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True,
                             check=True).stdout.splitlines()
        return [p for p in out if os.path.exists(os.path.join(REPO, p))]
    except (OSError, subprocess.CalledProcessError):
        found = []
        for root, dirs, names in os.walk(REPO):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "out")]
            found += [os.path.relpath(os.path.join(root, n), REPO) for n in names]
        return found


def read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8", errors="replace") as fh:
        return fh.read()


def check_text(rel, kind, holder):
    if not os.path.isfile(os.path.join(REPO, rel)):
        problem(f"{rel}: missing; NOTICE says the licence is there")
        return False
    text = read(rel)
    if kind == "Apache-2.0":
        ok = sha(norm(text, kind).encode()) == APACHE_SHA
    elif kind == "OFL-1.1":
        ok = sha(norm(text, kind).encode()) == OFL_SHA and holder.lower() in text.lower()
    else:
        ok = all(c.lower() in norm(text, kind).lower() for c in MIT_CLAUSES) and holder in text
    if not ok:
        problem(f"{rel}: not the {kind} text" + (f" naming {holder}" if kind != "Apache-2.0" else "")
                + ", word for word")
    return ok


def font_names(rel):
    from fontTools.ttLib import TTFont
    font = TTFont(os.path.join(REPO, rel), lazy=True)
    table = font["name"]
    return {i: table.getDebugName(i) or "" for i in (0, 1, 13, 14)}


def check_font(rel, comp):
    try:
        names = font_names(rel)
    except ImportError:
        problem("fonts need fontTools and brotli to read: pip install fonttools brotli")
        return False
    family, copyright_line = names[1], names[0]
    licence = f"{names[13]} {names[14]}"
    ok = True
    if not family.startswith(comp["family"]):
        problem(f"{rel}: its name table says {family!r}, not {comp['family']}")
        ok = False
    if comp["holder"].lower() not in copyright_line.lower():
        problem(f"{rel}: its copyright reads {copyright_line[:80]!r}, not {comp['holder']}")
        ok = False
    if not re.search(r"Open Font License|openfontlicense\.org|scripts\.sil\.org/OFL", licence, re.I):
        problem(f"{rel}: its name table doesn't give the SIL Open Font License")
        ok = False
    return ok


def check_upstream(comp, files):
    """Every outline and fill the kit ships, against Iconify's copy of Material Symbols."""
    try:
        with urllib.request.urlopen(ICONIFY_URL, timeout=120) as r:
            up = json.load(r)
    except Exception as exc:  # network, proxy, a moved file: say which
        problem(f"Material Symbols: couldn't fetch {ICONIFY_URL}: {exc}")
        return False
    info = up.get("info", {})
    if (info.get("license") or {}).get("spdx") != "Apache-2.0" or \
            "Google" not in (info.get("author") or {}).get("name", ""):
        problem(f"Material Symbols upstream no longer says Apache-2.0 by Google: {info}")
        return False
    icons = json.loads(read(f"{SKILLS}/ui-kit-for-android/icons/material-symbols.json"))
    names = set(up["icons"]) | set(up.get("aliases", {}))

    def paths(name):
        icon = up["icons"].get(name)
        if icon is None and name in up.get("aliases", {}):
            icon = up["icons"].get(up["aliases"][name].get("parent", ""))
        return re.findall(r'\bd="([^"]+)"', icon["body"]) if icon else None

    matched, ok = 0, True
    for name, variants in icons.items():
        n = name.replace("_", "-")
        for variant, upname in (("outline", f"{n}-outline"), ("fill", n)):
            got = paths(upname) or (paths(n) if variant == "outline" else None)
            if got is None:
                problem(f"Material Symbols: {name} ({variant}) isn't in the upstream set")
                ok = False
            elif variants[variant] not in got:
                problem(f"Material Symbols: {name} ({variant}) differs from the upstream path")
                ok = False
            else:
                matched += 1
    listed = [l.strip() for l in read(f"{SKILLS}/ui-kit-for-android/icons/names.txt").splitlines()
              if l.strip() and not l.startswith("#")]
    absent = [x for x in listed if x.replace("_", "-") not in names
              and x.replace("_", "-") + "-outline" not in names]
    NOTES.append(f"Material Symbols: {matched} paths match {ICONIFY_URL.split('/json')[0]}"
                 + (f"; {len(absent)} of {len(listed)} names in names.txt aren't in that set "
                    f"({', '.join(absent[:5])})" if absent else f"; all {len(listed)} names exist"))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--upstream", action="store_true",
                    help="also compare Material Symbols with their source (needs the network)")
    ap.add_argument("--json", metavar="FILE", help="write the inventory of third-party files")
    a = ap.parse_args()

    files = tracked()
    notice = read("NOTICE")
    owned = set()
    inventory = []
    for comp in COMPONENTS:
        matched = sorted({p for pat in comp["files"] for p in files
                          if glob.fnmatch.fnmatch(p, pat)})
        for pat in comp["files"]:
            if not any(glob.fnmatch.fnmatch(p, pat) for p in files):
                problem(f"{comp['name']}: nothing tracked matches {pat}")
        lic_ok = check_text(comp["licence_file"], comp["licence"], comp["holder"])
        owned.update(matched)
        owned.add(comp["licence_file"])
        fonts_ok = all(check_font(p, comp) for p in matched if p.endswith((".woff2", ".ttf", ".otf")))
        if comp["name"] not in notice:
            problem(f"NOTICE doesn't mention {comp['name']}")
        lic_dir = os.path.dirname(comp["licence_file"])
        if os.path.basename(comp["licence_file"]) not in notice and \
                os.path.basename(lic_dir) not in notice:
            problem(f"NOTICE doesn't say where {comp['name']}'s licence is")
        up_ok = None
        if a.upstream and comp["name"] == "Material Symbols":
            up_ok = check_upstream(comp, matched)
        inventory.append({
            "component": comp["name"], "licence": comp["licence"], "holder": comp["holder"],
            "source": comp["source"], "licence_file": comp["licence_file"],
            "files": [{"path": p, "sha256": sha(open(os.path.join(REPO, p), "rb").read())}
                      for p in matched],
            "checks": {"licence_text": lic_ok, "font_metadata": fonts_ok,
                       **({"matches_upstream": up_ok} if up_ok is not None else {})}})

    root_licence = read("LICENSE")
    if sha(norm(root_licence, "Apache-2.0").encode()) != APACHE_SHA:
        problem("LICENSE: not the Apache 2.0 text, word for word")
    skills = sorted(d for d in os.listdir(os.path.join(REPO, SKILLS))
                    if os.path.isdir(os.path.join(REPO, SKILLS, d)) and not d.startswith("."))
    for s in skills:
        rel = f"{SKILLS}/{s}/LICENSE"
        if not os.path.isfile(os.path.join(REPO, rel)):
            problem(f"{rel}: missing; every skill carries the licence so it travels with it")
        elif read(rel) != root_licence:
            problem(f"{rel}: differs from the repo's LICENSE")
        owned.add(rel)

    for p in files:
        if p in owned or p in ("LICENSE", "NOTICE"):
            continue
        if BINARY.search(p) and not any(rx.match(p) for rx in ORIGINAL):
            problem(f"{p}: a font, image or icon file that no component in NOTICE covers")
        elif LICENCE_NAME.search(p) and not p.startswith(".github/"):
            problem(f"{p}: a licence file for something NOTICE doesn't list")

    for n in NOTES:
        print(f"  {n}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"original_work": {"licence": "Apache-2.0", "licence_file": "LICENSE",
                                         "holder": "doppe7gangar", "notice": "NOTICE"},
                       "third_party": inventory}, fh, indent=1)
            fh.write("\n")
    total = sum(len(c["files"]) for c in inventory)
    print(f"licences: {len(COMPONENTS)} third-party components, {total} files, "
          f"{len(skills)} skill licences, {len(PROBLEMS)} problem(s)")
    for m in PROBLEMS:
        print(f"  FAIL {m}")
    return 1 if PROBLEMS else 0


if __name__ == "__main__":
    sys.exit(main())

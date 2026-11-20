#!/usr/bin/env python3
"""onplatform's status line for Claude Code.

Claude Code pipes the session as JSON on stdin and shows the first line
this prints under the prompt. It reads the design folder in the current
directory, if there is one, so the line says what you're designing:

    ◆ onplatform  iPhone · tab bar · Fern  ·  Opus

and, outside a design, just the product and the model:

    ◆ onplatform  ·  Opus

`/onplatform:setup` installs it; nothing here writes anything.
"""

import json
import os
import re
import sys

PLATFORMS = {"ios": "iPhone", "ipados": "iPad", "macos": "Mac", "android": "Android",
             "web": "Web", "marketing": "Site", "cross": "iPhone + Android"}
MODELS = {"tabs": "tab bar", "stack": "stack", "sidebar": "sidebar", "workspace": "workspace",
          "list-detail": "list and detail", "dashboard": "dashboard", "document": "documents"}

ACCENT = "\033[38;5;39m"   # close to the kit's #0088FF in 256 colours
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def design_folder(cwd):
    for d in (os.path.join(cwd, "design"), cwd):
        if os.path.isfile(os.path.join(d, "DESIGN.md")):
            return d
    return None


def section(text, heading):
    m = re.search(r"^## " + re.escape(heading) + r"\s*\n+\s*`([^`]+)`", text, re.M)
    return m.group(1).strip() if m else None


def product(folder):
    try:
        head = open(os.path.join(folder, "index.html"), encoding="utf-8").read(4000)
    except OSError:
        return None
    m = re.search(r"<title>\s*([^<]{1,40}?)\s*</title>", head, re.I)
    return m.group(1) if m else None


def line(session, colour=True):
    cwd = (session.get("workspace") or {}).get("current_dir") or session.get("cwd") or os.getcwd()
    model = (session.get("model") or {}).get("display_name") or ""
    a, d, b, r = (ACCENT, DIM, BOLD, RESET) if colour else ("", "", "", "")
    parts = []
    folder = design_folder(cwd)
    if folder:
        text = open(os.path.join(folder, "DESIGN.md"), encoding="utf-8").read()
        kind, spatial = section(text, "Platform mode"), section(text, "Spatial model")
        parts = [PLATFORMS.get(kind, kind), MODELS.get(spatial, spatial), product(folder)]
        parts = [p for p in parts if p]
    out = f"{a}◆{r} {b}onplatform{r}"
    if parts:
        out += "  " + f" {d}·{r} ".join(parts)
    if model:
        out += f"  {d}·  {model}{r}"
    return out


def main():
    try:
        session = json.load(sys.stdin)
    except ValueError:
        session = {}
    print(line(session, colour=not os.environ.get("NO_COLOR")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

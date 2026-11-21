#!/usr/bin/env python3
"""onplatform's status line for Claude Code.

Claude Code pipes the session as JSON on stdin and shows the first line
this prints under the prompt. It reads the design folder in the current
directory, if there is one, so the line says what you're designing:

    ◆ onplatform  ~/plants  ·  iPhone · tab bar · Thirsty  /onplatform:check
                                                                          Opus 5 · context: 5%

The diamond is filled while the onplatform output style is on. Outside a
design, the first line ends with /onplatform:start instead.

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


def visible(text):
    return len(re.sub(r"\033\[[0-9;]*m", "", text))


def lines(session, colour=True, width=None):
    """Two lines, the way a terminal tool's footer reads: where you are and
    what you're designing on the left, the model and context on the right."""
    cwd = (session.get("workspace") or {}).get("current_dir") or session.get("cwd") or os.getcwd()
    model = (session.get("model") or {}).get("display_name") or ""
    used = (session.get("context_window") or {}).get("used_percentage")
    style = (session.get("output_style") or {}).get("name", "")
    a, d, b, r = (ACCENT, DIM, BOLD, RESET) if colour else ("", "", "", "")

    home = os.path.expanduser("~")
    where = "~" + cwd[len(home):] if home != "/" and (cwd == home or cwd.startswith(home + "/")) else cwd
    mark = "◆" if "onplatform" in style else "◇"
    first = f"{a}{mark}{r} {b}onplatform{r}  {where}"

    folder = design_folder(cwd)
    if folder:
        text = open(os.path.join(folder, "DESIGN.md"), encoding="utf-8").read()
        kind, spatial = section(text, "Platform mode"), section(text, "Spatial model")
        parts = [p for p in (PLATFORMS.get(kind, kind), MODELS.get(spatial, spatial), product(folder)) if p]
        if parts:
            first += f"  {d}·{r}  " + f" {d}·{r} ".join(parts)
        first += f"  {d}/onplatform:check{r}"
    else:
        first += f"  {d}/onplatform:start{r}"

    right = [x for x in (model, f"context: {used}%" if used is not None else "") if x]
    second = f"{d}" + " · ".join(right) + f"{r}" if right else ""
    if second and width:
        second = " " * max(0, width - visible(second) - 2) + second
    return [first, second] if second else [first]


def line(session, colour=True):
    return lines(session, colour)[0]


def terminal_width():
    """COLUMNS if the shell exported it, else the terminal's own size."""
    try:
        return int(os.environ["COLUMNS"])
    except (KeyError, ValueError):
        pass
    try:
        fd = os.open("/dev/tty", os.O_RDONLY)
        try:
            return os.get_terminal_size(fd).columns
        finally:
            os.close(fd)
    except OSError:
        return None


def main():
    try:
        session = json.load(sys.stdin)
    except ValueError:
        session = {}
    width = terminal_width()
    print("\n".join(lines(session, colour=not os.environ.get("NO_COLOR"), width=width)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

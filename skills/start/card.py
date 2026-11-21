#!/usr/bin/env python3
"""The welcome card /onplatform:start shows.

Prints a box with what onplatform is, where you are, the design in this
folder if there is one, whether setup and the output style are on, and
three things to try. It only reads.

    python3 card.py [folder]
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "skills", "setup"))
import statusline  # noqa: E402

WIDTH = 66
# The onplatform logo, a monitor on its stand and the word in pixel
# letters, drawn two pixels to a character with half blocks.
LOGO = [
    ' ▄▄▄▄▄               ▄     ▄    ▄▄   +',
    ' █   █   ▄▄▄ ▄▄  ▄▄▄ █  ▄▄ █▄▄ █▄▄ ▄▄▄ ▄ ▄ ▄▄▄▄',
    ' ▀███▀   █ █ █ █ █▄█ █ █ █ █   █   █ █ █▀  █ █ █',
    '▀▀▀▀▀▀▀  ▀▀▀ ▀ ▀ █   ▀  ▀▀  ▀▀ ▀   ▀▀▀ ▀   ▀ ▀ ▀',
]
TRY = ["Design an iPhone app for tracking house plants",
       "Is a 30 × 30 pt toolbar button too small?",
       "/onplatform:review HomeView.swift"]


def setup_done():
    p = subprocess.run([sys.executable, os.path.join(ROOT, "skills", "setup", "allow.py"), "--check"],
                       capture_output=True)
    return p.returncode == 0


def style_on(cwd):
    for path in (os.path.join(cwd, ".claude", "settings.local.json"),
                 os.path.join(cwd, ".claude", "settings.json"),
                 os.path.join(os.path.expanduser("~"), ".claude", "settings.json")):
        try:
            style = json.load(open(path, encoding="utf-8")).get("outputStyle")
        except (OSError, ValueError):
            continue
        if style:
            return "onplatform" in style
    return False


def card(cwd, setup, style):
    first = statusline.lines({"workspace": {"current_dir": cwd}}, colour=False)[0]
    design = first.split("  ·  ", 1)[1].split("  /", 1)[0] if "  ·  " in first else None
    home = os.path.expanduser("~")
    where = "~" + cwd[len(home):] if cwd == home or cwd.startswith(home + "/") else cwd

    rows = [""] + [" " + a for a in LOGO] + [
            "",
            "Designs that look native on iPhone, iPad, Mac and Android",
            "",
            f"Directory:  {where}",
            f"Design:     {design or 'none here yet'}",
            f"Setup:      {'done' if setup else 'not yet, /onplatform:setup stops the prompts'}",
            f"Voice:      {'onplatform' if style else 'default, /output-style onplatform:onplatform'}",
            "",
            f"Try:        {TRY[0]}"] + [f"            {t}" for t in TRY[1:]] + [""]
    inner = max(WIDTH, max(len(r) for r in rows) + 4)
    out = ["╭" + "─" * inner + "╮"]
    out += ["│  " + r.ljust(inner - 2) + "│" for r in rows]
    out.append("╰" + "─" * inner + "╯")
    return "\n".join(out)


def main():
    cwd = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
    print(card(cwd, setup_done(), style_on(cwd)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

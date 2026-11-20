#!/usr/bin/env python3
"""The two permission rules that let onplatform's skills work without prompts.

Claude Code asks before reading files outside the project and before
running a script, and the plugin's files live outside every project. A
plugin can't grant itself permissions, so this writes two rules into the
person's own settings, once:

  Read(//<plugin folder>/**)            read the skills' references
  Bash(python3 <plugin folder>/*)       run the skills' own scripts

The folder is the plugin's install folder above its version, so the rules
still hold after /plugin updates it. Nothing else is allowed: no other
script, no writes.

    python3 allow.py            show the rules and where they'd go
    python3 allow.py --apply    add them (a copy of the old settings is kept)
    python3 allow.py --check    exit 0 if they're already there

With --statusline it also sets onplatform's status line (statusline.py),
which shows the platform and layout of the design you're in. It never
replaces a status line you already have; it says what's there instead.
"""

import argparse
import json
import os
import re
import shutil
import sys

ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SETTINGS = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")


def base():
    """The install folder above the version: .../plugins/cache/<market>/<plugin>."""
    root = os.path.realpath(ROOT)
    m = re.match(r"(.*/plugins/cache/[^/]+/[^/]+)(/|$)", root)
    return m.group(1) if m else root


def rules():
    b = base()
    return [f"Read(/{b}/**)", f"Bash(python3 {b}/*)"]


def statusline_command():
    """Run whichever version is installed, so /plugin updates don't break it."""
    b, root = base(), os.path.realpath(ROOT)
    if b == root:
        return f'python3 "{root}/skills/setup/statusline.py"'
    return (f'python3 "$(ls -d {b}/*/skills/setup/statusline.py 2>/dev/null | sort -V | tail -1)"')


def ours(settings):
    cmd = (settings.get("statusLine") or {}).get("command", "")
    return "statusline.py" in cmd and "onplatform" in cmd


def load():
    try:
        return json.load(open(SETTINGS, encoding="utf-8"))
    except FileNotFoundError:
        return {}


def missing(settings):
    have = set(((settings.get("permissions") or {}).get("allow")) or [])
    return [r for r in rules() if r not in have]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--statusline", action="store_true", help="also set the status line")
    a = ap.parse_args()
    try:
        settings = load()
    except ValueError:
        print(f"{SETTINGS} isn't valid JSON, so it was left alone. Add these to permissions.allow by hand:")
        print("\n".join("  " + r for r in rules()))
        return 1
    todo = missing(settings)
    line = None
    if a.statusline:
        if ours(settings):
            pass
        elif settings.get("statusLine"):
            print("Kept your status line, which is already set to: "
                  + json.dumps(settings["statusLine"].get("command", settings["statusLine"])))
        else:
            line = {"type": "command", "command": statusline_command(), "padding": 0}
    if a.check:
        return 0 if not todo else 1
    if not todo and not line:
        print(f"Already set up: everything is in {SETTINGS}.")
        return 0
    if not a.apply:
        if todo:
            print(f"Would add to permissions.allow in {SETTINGS}:")
            print("\n".join("  " + r for r in todo))
        if line:
            print(f"Would set statusLine in {SETTINGS} to:\n  {line['command']}")
        return 0
    if os.path.exists(SETTINGS):
        shutil.copy2(SETTINGS, SETTINGS + ".onplatform-backup")
    if todo:
        settings.setdefault("permissions", {}).setdefault("allow", []).extend(todo)
    if line:
        settings["statusLine"] = line
    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    with open(SETTINGS, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2)
        fh.write("\n")
    print(f"Added to {SETTINGS}:")
    if todo:
        print("\n".join("  " + r for r in todo))
    if line:
        print("  statusLine: onplatform's status line")
    if os.path.exists(SETTINGS + ".onplatform-backup"):
        print(f"The previous file is at {SETTINGS}.onplatform-backup.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

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
    a = ap.parse_args()
    try:
        settings = load()
    except ValueError:
        print(f"{SETTINGS} isn't valid JSON, so it was left alone. Add these to permissions.allow by hand:")
        print("\n".join("  " + r for r in rules()))
        return 1
    todo = missing(settings)
    if a.check:
        return 0 if not todo else 1
    if not todo:
        print(f"Already set up: both rules are in {SETTINGS}.")
        return 0
    if not a.apply:
        print(f"Would add to permissions.allow in {SETTINGS}:")
        print("\n".join("  " + r for r in todo))
        return 0
    if os.path.exists(SETTINGS):
        shutil.copy2(SETTINGS, SETTINGS + ".onplatform-backup")
    settings.setdefault("permissions", {}).setdefault("allow", []).extend(todo)
    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    with open(SETTINGS, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2)
        fh.write("\n")
    print(f"Added to {SETTINGS}:")
    print("\n".join("  " + r for r in todo))
    if os.path.exists(SETTINGS + ".onplatform-backup"):
        print(f"The previous file is at {SETTINGS}.onplatform-backup.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

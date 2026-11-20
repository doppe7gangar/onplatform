#!/usr/bin/env python3
"""When a session starts: one line saying onplatform is on, and how to reach it.

Shown to the person only (a systemMessage), not added to the model's
context, and only on a fresh start: not after /clear, a resume or a
compaction. The counts come from the plugin's own folders, so the line
can't drift from what's installed.

Off with ONPLATFORM_BANNER=off in the environment (settings.json "env").
"""

import json
import os
import sys

ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def count(folder, test):
    path = os.path.join(ROOT, folder)
    try:
        return sum(1 for n in os.listdir(path) if test(os.path.join(path, n)))
    except OSError:
        return 0


def set_up():
    """True once /onplatform:setup's rules are in the person's settings."""
    sys.path.insert(0, os.path.join(ROOT, "skills", "setup"))
    try:
        import allow
        return not allow.missing(allow.load())
    except Exception:
        return True  # can't tell: don't nag


def main():
    if os.environ.get("ONPLATFORM_BANNER", "").lower() in ("off", "0", "false", "no"):
        return 0
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    if event.get("source", "startup") != "startup":
        return 0
    skills = count(os.path.join(".claude", "skills"), lambda p: os.path.isfile(os.path.join(p, "SKILL.md")))
    commands = count("skills", lambda p: os.path.isfile(os.path.join(p, "SKILL.md")))
    agents = count("agents", lambda p: p.endswith(".md"))
    line = f"onplatform ready · {skills} skills · {commands} /onplatform: commands · {agents} agents"
    if not set_up():
        line += " · /onplatform:setup stops the permission prompts"
    print(json.dumps({"systemMessage": line, "suppressOutput": True}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # a hook must never get in the way of starting
        sys.exit(0)

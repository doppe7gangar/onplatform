---
description: Let the skills read their files and run their scripts without asking each time
argument-hint: "(no arguments)"
disable-model-invocation: true
---

# Set up onplatform

Claude Code asks before reading files outside the project and before running
a script, and the plugin lives outside every project, so the skills ask the
first time they look something up. This adds two narrow rules to the
person's own settings so they stop asking.

1. Show what would change:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/setup/allow.py`
   If it says it's already set up, say so and stop.
2. Show the person the rules it prints and where they go, in one short
   message: one lets Claude read the plugin's own files, the other lets it
   run the plugin's own Python scripts, and nothing else. Ask whether to add
   them.
3. Only on a yes: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/setup/allow.py --apply`.
   Tell them it's done, that the old settings were copied beside the file,
   and that the rules take effect in the next session.

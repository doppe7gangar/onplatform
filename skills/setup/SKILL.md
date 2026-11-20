---
description: Stop the permission prompts and turn on onplatform's status line
argument-hint: "(no arguments)"
disable-model-invocation: true
---

# Set up onplatform

Claude Code asks before reading files outside the project and before running
a script, and the plugin lives outside every project, so the skills ask the
first time they look something up. This adds two narrow rules to the
person's own settings so they stop asking, and, if they want it, a status
line that shows the platform and layout of the design they're in:

```
◆ onplatform  iPhone · tab bar · Thirsty  ·  Opus
```

1. Show what would change:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/setup/allow.py --statusline`
   If it says everything is already set up, say so and stop.
2. Tell the person in one short message what it printed: one rule lets
   Claude read the plugin's own files, the other lets it run the plugin's
   own Python scripts, and nothing else; and the status line, shown as the
   line above. If it kept their own status line, say it's left alone. Ask
   whether to add it all, the rules only, or nothing.
3. Only on a yes: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/setup/allow.py --apply --statusline`
   (without `--statusline` for the rules only). Say it's done, that the old
   settings were copied beside the file, and that it takes effect in the
   next session.
4. Close with one line: for onplatform's voice in every reply, run
   `/output-style onplatform:onplatform`.

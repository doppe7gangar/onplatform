---
description: Serve a design folder as a live preview that reloads itself whenever the design changes, in a browser or on a phone on the same network.
argument-hint: "[design folder] [--phone]"
disable-model-invocation: true
---

# Preview a design

What to preview: $ARGUMENTS. If no folder was named, use `./design`, or the
folder here that holds `index.html` and `DESIGN.md`.

Start the server in the background, so the conversation can go on while it
runs:

`python3 ${CLAUDE_PLUGIN_ROOT}/.claude/skills/design-workflow/preview.py <folder>`

With `--phone` it also serves on this network and prints the address to open
on a phone, where a design reads very differently than on a desktop; only on
a network the person trusts.

Give the person the address it prints (on a Mac, `open` it), and the
addresses for the other states: `?state=empty`, `?state=loading`,
`?state=error`. The page reloads itself after each change to the design, so
it can stay open while you keep working. Say how to stop it: stop the
background task, or Ctrl-C where it runs.

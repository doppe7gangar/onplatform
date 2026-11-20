---
description: Start here: what onplatform does, and three things to try
argument-hint: "(no arguments)"
disable-model-invocation: true
---

# Start here

Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/setup/allow.py --check` first. Its
exit status says whether `/onplatform:setup` has been done (0 means done).

Then reply with exactly the card below and nothing else: no preamble, no
closing offer. Keep the bold, the table and the line breaks as they are.
Include the last line only when the check said setup isn't done.

**onplatform** · designs that look native on iPhone, iPad, Mac and Android, measured from Apple's and Google's own kits

| Say | You get |
|---|---|
| *Design an iPhone app for tracking house plants* | A tappable prototype with every screen and state, checked in a browser |
| *Is a 30 × 30 pt toolbar button too small?* | The verdict, Apple's rule and the fix, in about ten lines |
| `/onplatform:review` | Your SwiftUI or Compose held against Apple's or Google's rules |

No need to name a skill; the right one picks itself. For a whole session as a designer: `claude --agent onplatform:designer`

One-time: `/onplatform:setup` stops the permission prompts.

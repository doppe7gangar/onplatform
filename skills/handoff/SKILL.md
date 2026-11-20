---
description: Turn an approved design into SwiftUI, and prove nothing was lost
argument-hint: "[design folder] [SwiftUI project folder]"
disable-model-invocation: true
---

# Hand off to SwiftUI

The design and the target: $ARGUMENTS. If they weren't named, use `./design`
and ask where the SwiftUI project should go.

Scripts live in `${CLAUDE_PLUGIN_ROOT}/.claude/skills/`.

1. Follow step 17 of the `onplatform:design-workflow` skill: each screen, state,
   sheet and SF Symbol in the design becomes its SwiftUI counterpart, with
   system controls in place of the web recipes and semantic colours and
   text styles in place of raw values.
2. `python3 ${CLAUDE_PLUGIN_ROOT}/.claude/skills/design-workflow/check_handoff.py <design> <swift folder>`
   reports what the SwiftUI dropped or changed.
3. `python3 ${CLAUDE_PLUGIN_ROOT}/.claude/skills/hig-guide/check_swiftui.py <swift folder>`
   reports what the HIG would flag in the code itself.
4. Fix and run both again until they pass.

Report what was built, what the checks said, and anything the design left
open that the code had to decide.

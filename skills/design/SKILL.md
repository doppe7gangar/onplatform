---
description: Design an app, site or dashboard from a brief to a working prototype that reads as native on iPhone, iPad, Mac or Android, checked in a real browser before it's handed over.
argument-hint: "<what you want to build>"
disable-model-invocation: true
---

# Design it

The brief: $ARGUMENTS

If no brief came with the command, ask for one in a sentence and stop.

Scripts live in `${CLAUDE_PLUGIN_ROOT}/.claude/skills/design-workflow/`; below, `D` stands for that folder.

1. **Load the method.** Invoke the `onplatform:design-workflow` skill and follow it. It
   brings in `onplatform:hig-guide`, `onplatform:ui-kit-for-apple-platforms`, `onplatform:motion-for-apple-platforms` and
   `onplatform:ui-kit-for-android` as the work needs them. For a one-screen request,
   take its short path.
2. **Settle the brief before drawing:** the platform, who it's for, the
   screens and the states each one has. Ask only what can't be inferred, and
   say what you assumed.
3. **Scaffold, don't hand-roll:**
   `python3 D/new_project.py --name "<name>" --brand "<#hex>" --kind <ios|ipados|macos|android|web> --model <model> -o ./design`
4. **Show it while you build:** start `python3 D/preview.py ./design` in the
   background and give the person the address. It reloads after every
   change, so they watch the design come together.
5. **Build on the scaffold** with real content and the loading, empty and
   error states, keeping the kit's recipes. They carry the measured metrics.
6. **Check until it passes:** `python3 D/check_design.py ./design`. It taps
   every control and fails the ones that do nothing. Then render it with
   `python3 D/render_review.py ./design` and work through the review.
7. **Stress it:** `python3 D/stress_test.py ./design` renders every screen at
   the largest text, right to left and with longer strings. Fix what fails
   and look at the renders in `design/.visual-review/stress/`.
8. **Second opinion, then fix, at most twice.** Hand the folder to the
   `onplatform:design-critic` agent. Fix the changes it ranks highest, run
   `check_design.py` again, and send it back once more if it asked for more
   than three. Say in the handover what you left and why.
9. **Licences:** `python3 D/check_distribution.py ./design`.
10. **Hand over:** what you built, how to open it (`open design/index.html`),
   what passed, what you assumed, and what comes next: `/onplatform:figma` to send
   it to Figma, `/onplatform:handoff` for SwiftUI, and `/onplatform:ship` before it's
   shared or published.

---
description: Run every mechanical check on a design folder (taps, states, contrast, use of the kit, SF Symbol names, licences, the largest text, right to left, long text) and fix what fails until it passes.
argument-hint: "[design folder]"
disable-model-invocation: true
---

# Check a design

The folder: $ARGUMENTS. If none was named, use `./design`, or the folder
here that holds `index.html` and `DESIGN.md`.

Scripts live in `${CLAUDE_PLUGIN_ROOT}/.claude/skills/design-workflow/`; below, `D` stands for that folder.

1. `python3 D/check_design.py <folder>`. It drives a real browser. If
   Playwright is missing, run it with `--no-browser`, say the browser checks
   didn't run, and give the setup:
   `pip3 install playwright pillow && python3 -m playwright install chromium`.
2. `python3 D/check_distribution.py <folder>`, for what the design carries
   and under what licence.
3. `python3 D/stress_test.py <folder>`: every screen at the largest text,
   right to left, and with longer strings. Look at the renders it saves in
   `<folder>/.visual-review/stress/` as well as its findings.
4. Fix each FAIL where it starts: use the kit's recipe rather than
   overriding it, and the design's tokens rather than raw values. Run all
   three again until they pass.

Report what failed, what you changed, and the closing lines of each check,
word for word.

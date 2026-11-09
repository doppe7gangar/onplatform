# Testing these skills yourself

Four ways, cheapest first. You need nothing installed for the first one.

Paths below assume the repo is where GitHub Desktop puts it,
`~/Documents/GitHub/onplatform`. Adjust if you cloned somewhere else.

---

## 1. Look at it (no setup)

```bash
open ~/Documents/GitHub/onplatform/.claude/skills/ui-kit-for-apple-platforms/example.html
```

One screen, using every recipe the way a real app would rather than
lining them up for inspection. To check dark mode, flip
**System Settings → Appearance** while it's open — the page follows the
system, so it should switch without a reload.

What you're looking for: a grey page with white cards, capsule buttons,
green switches, separators that start at the text rather than the card
edge.

On a Mac the type renders in SF Pro from your own system copy, because
`-apple-system` finds it first. Everywhere else it renders in the bundled
Inter. `fonts/sf.css` explains how to use your own copy of SF Pro instead.

---

## 2. Test the UI-kit skill in Claude Code (the real test)

Install it once, for every project:

```bash
mkdir -p ~/.claude/skills
cp -R ~/Documents/GitHub/onplatform/.claude/skills/ui-kit-for-apple-platforms ~/.claude/skills/
```

Then in any empty folder:

```bash
mkdir ~/Desktop/skill-test && cd ~/Desktop/skill-test
claude
```

Ask for something ordinary:

> build me a simple expense tracker web page — a list of expenses, a
> total at the top, and an add button. make it feel like an Apple app.

**What tells you it worked:**

- It opens `ui-kit-for-apple-platforms` or `design-workflow` before writing any CSS. A
  request for a whole page or app goes through `design-workflow`, which
  scaffolds the project and brings the kit in; that's expected and can
  take half an hour, because it runs its own checks.
- It copies `ios-tokens.css` and `ios-components.css` in rather than
  reinventing them, and the page uses the kit's classes (`ios-list`,
  `ios-navbar`, `ios-btn`).
- The files it writes reference `var(--ios-accent)` and friends, not
  raw hex codes.

**What tells you it didn't:** hardcoded `#007AFF` anywhere. That's the
old palette from search results — the measured iOS 27 accent is
`#0088FF`. It's the clearest single tell. The subtler one is a page that
has the right colours on hand-built lists and bars: it looks almost like
iOS, which is the failure this kit exists to prevent.

Open the result and compare it against `example.html` side by side.

The same check, run and graded for you, screenshots included:

```bash
python3 scripts/eval/test_ui_kit_build.py --save /tmp/uikit
python3 scripts/eval/test_ui_kit_build.py --grade ./design   # grade your own build
```

---

## 3. Run the automated checks

One-time setup:

```bash
pip3 install playwright pillow
python3 -m playwright install chromium
```

Then:

```bash
cd ~/Documents/GitHub/onplatform
python3 scripts/verify_web_ui.py -v
```

218 checks in a real browser, across light, dark, and increased
contrast. It asserts computed values rather than appearance: every token
resolves, the type scale lands on the HIG's numbers to the pixel, the
switch measures 64×28 with a 38×24 pill knob travelling 22px, hit targets clear 44px,
separators skip each list's first row, the colour pairs meet the contrast
they should, and a bundled face actually renders rather than silently
falling through to whatever the platform substitutes.

It exits non-zero if anything fails, so it's worth running after any
edit to the CSS. Drop `-v` to see only failures.

To re-measure from the PNGs after changing the kit:

```bash
python3 scripts/extract_ui_kit_tokens.py   # PNGs -> measurements
python3 scripts/build_design_tokens.py     # -> CSS, Swift, Kotlin, XML,
                                           #    Dart, TS, Design Tokens JSON
python3 scripts/verify_web_ui.py           # asserts the rendered result
```

The exports all come from the same measurements, so a value can't drift
between platforms. Each one names the file it was measured from.

---

## 4. Test the HIG reference skill

```bash
cp -R ~/Documents/GitHub/onplatform/.claude/skills/hig-guide ~/.claude/skills/
```

Ask questions where you can check the answer:

> what's the minimum tap target on iOS, and where does Apple say it?

A working answer gives **both** numbers and says they disagree — 44×44 pt
as the general rule from [Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons), 28×28 pt as the floor in the
accessibility table — rather than confidently quoting one. That specific
question used to produce opposite answers on different runs, so it's a
good canary.

> 設計一個 iOS 設定畫面的文字階層，給我實際的 pt 數值

Non-English works; Apple's pages are English but retrieval doesn't care.
You should get 34/41 for Large Title, 17/22 body, 13/18 footnote.

Or paste real SwiftUI and ask for a review before shipping.

### Checking SwiftUI without a model

```bash
python3 ~/.claude/skills/hig-guide/check_swiftui.py MyApp/
python3 scripts/eval/test_check_swiftui.py    # the checker against a seeded app
```

On a Mac, `python3 ~/.claude/skills/hig-guide/sf_symbols.py --install`
copies the SF Symbol names, renames and release versions from macOS or
Xcode into `~/.cache/hig-guide/`, and both checkers start flagging names
that don't exist or need a newer OS. If it finds nothing, point `--from`
at a folder holding `name_availability.plist`.
`python3 scripts/eval/test_sf_symbols.py` tests the reading and the checks
against a small stand-in list, since Apple's own can't be committed here.

### The macOS recipes

```bash
python3 .claude/skills/ui-kit-for-apple-platforms/verify_mac_ui.py -v
```

Measures `mac-example.html` in Chromium, light, dark and Increased
Contrast: the window's corners, the traffic lights' size, pitch and
position, the toolbar band and its glass controls, the control heights
and corners, the switch, the sidebar's width, rows and insets, menu rows
and their highlight, table rows and selection, the alert, the sheet, the
type and the colours, and a brand accent reaching every accent surface.
Every expected number is the one `macos-components.css` says Apple's
macOS 27 design kit carries.
`python3 scripts/eval/design_workflow_smoke.py` scaffolds both Mac models
and checks that a Mac design with an iPhone tab bar, or without its
window, fails `check_design.py`.

### The iPadOS recipes

```bash
python3 .claude/skills/ui-kit-for-apple-platforms/verify_ipad_ui.py -v
```

Measures `ipad-example.html` in Chromium, light and dark, in 67 checks:
the iPad's screen and corners, the 32pt status bar with the app's menu,
the 320pt sidebar's background, toolbar, search field, rows, symbol
column, selection and headers, the floating toolbar controls, the tab
bar at the top centre, the title block, the sheet and its grabber, the
popover and its arrow, and the dim. The expected numbers are written
into the verifier from Apple's iOS and iPadOS 27 design kit.
`python3 scripts/eval/design_workflow_smoke.py` scaffolds both iPad
models and checks that an iPad design with the iPhone's bottom tab bar,
or with neither a sidebar nor tabs at the top, fails `check_design.py`.

### The Android (Material 3) recipes

```bash
python3 .claude/skills/ui-kit-for-android/verify_android_ui.py -v
```

Measures `android-example.html` in Chromium, light and dark, in 268
checks: the phone and its status and gesture bars, the three top app
bars, the nav bar and its indicator, buttons, FABs, icon buttons, chips,
cards, lists, the search bar, switches, checkboxes, radios, text fields,
the dialog, menu, tabs, bottom sheet, snackbar and progress bar, the
type, every colour role, and text contrast. The expected numbers are
written into the verifier from Google's Material 3 Design Kit. It also
holds `build_m3_theme.py` to the kit (seeded with `#6750A4` it has to
land on the kit's scheme) and checks a brand theme reaches every
component. `python3 scripts/eval/design_workflow_smoke.py` scaffolds
both Android models and checks that an Android design with Apple chrome,
or without its top app bar, fails `check_design.py`.

### The React components and the Tailwind theme

```bash
python3 scripts/eval/test_react_kit.py       # keyboard, screen reader, axe, light and dark
python3 scripts/eval/test_tailwind_theme.py  # compiles with v4 and v3, colours match the kit
python3 scripts/build_tailwind.py            # regenerate the themes after a token change
```

The React test bundles `react/example.jsx` and drives it from the
keyboard: Enter on a row, arrows through tabs and the segmented control,
Space on a switch, Tab inside an open sheet without escaping it, Escape,
and focus back where it started. axe-core audits the page with each
modal open. Colour contrast is counted separately rather than failed:
light mode keeps Apple's palette, which falls short of 4.5:1 in places
Apple itself chose. Both tests need node and npm, and install what they
use into `scripts/eval/out/`.

### Checking a handoff from design to SwiftUI

```bash
python3 .claude/skills/design-workflow/check_handoff.py ./design ./MyApp
python3 scripts/eval/test_check_handoff.py
```

`scripts/eval/handoff/` holds a small design and a faithful SwiftUI
translation of it. The test requires the faithful one to come back clean
from both checkers, then breaks it eleven ways a real handoff drifts (a
renamed tab, a swapped symbol, a lost loading state, the accent written
as a hex literal, and so on) and requires each to be reported. None of
it compiles Swift; on a Mac, open the views in Xcode and compare each
`#Preview` with the design's matching state.

### Checking an answer rather than trusting it

Every claim in an answer should carry a link to Apple's page. Copy the
answer, then:

```bash
pbpaste | python3 ~/.claude/skills/hig-guide/check_quotes.py -
```

It fetches each HIG page the answer links and grades every quoted span:
**verbatim**, **elided** (honest `[…]`), **truncated** (ends early),
**altered** — reworded, or two separate rules fused into one sentence
Apple never wrote — or **unlinked**, when the answer gives no page to check
against. Anything reported as ALTERED is worth reading twice. A number
should also be the one for the platform you asked about.

---

## What "working" does not mean

`ui-kit-for-apple-platforms` carries Apple's *appearance* to platforms that have no
system palette to ask. On the web specifically it can't carry:

- **Liquid Glass** — the live refraction has no browser equivalent. The
  rim, falloff, tint variants and ambient shadow are all measured and
  built; only the bending of what's behind the surface is missing. It
  needs something behind it to work at all — over a flat background it
  collapses to a grey box, which is a property of the material, not a
  bug.
- **Native behaviour** — sheet physics, rubber-banding, haptics.

**SF Pro isn't shipped.** Apple's licence doesn't allow redistributing
it. Apple devices use their own copy through `-apple-system`, and
everywhere else the kit falls back to the bundled Inter. If you have
Apple's download, `fonts/sf.css` explains how to use your own copy for
mockups.

And in light mode Apple's own palette sits under Apple's own contrast
threshold (secondary label 3.44:1 against a required 4.5:1). That's real,
it's documented in the skill, and `prefers-contrast: more` is wired up to
fix it. Not a bug to report.

---

## 5. Test the design skill on a whole brief

The other three answer questions. `design-workflow` starts projects, so it
needs testing differently: not "is the answer right" but "is the thing
on disk actually wired up".

Ask for a product rather than a control. Anything works —
*"an internal analytics dashboard for our support team, web only, brand
colour #1F6FEB"*, *"a landing page for a B2B time-tracking tool"*,
*"an iOS app for tracking when my house plants need watering"*.

What should happen: it names the kind first, lists the screens, runs
`new_project.py` to scaffold, replaces the placeholder content with the
real design, and runs `check_design.py` before handing it over.

### Grade it with the checker, not by reading

```bash
python3 .claude/skills/design-workflow/check_design.py ./design
```

This is the part worth insisting on. Three earlier rounds of this were
graded by reading the transcript, and all three were called working
while the thing on disk had a font CDN in it, or no `--ios-*` bridge, or
only the happy path. Every one of those survives a screenshot and a
confident summary. The exit code doesn't care about either.

Nonzero means don't ship it. It checks stylesheet order, remote
resources, the bridge surviving, all four states, dead local references,
hand-overridden tokens, contrast, sideways overflow at phone width,
targets under Apple's floor, console errors, and what `--ios-accent`
actually resolved to in a browser.

### Prove the checker isn't just agreeing with you

A checker that only ever passes is worth nothing. Break something and
confirm it fails:

```bash
cp -r design broken
sed -i 's|vendor/fonts/inter.css|https://fonts.googleapis.com/css2?family=Inter|' broken/index.html
python3 .claude/skills/design-workflow/check_design.py broken   # must exit 1
```

Moving `theme.css` above the component sheet, deleting the empty and
error panels, or cutting the bridge off the end of `theme.css` should
each fail too — those are the four failures this was built from.

### The whole thing, automated

```bash
python3 scripts/eval/projtest.py
```

Runs three briefs of different kinds through a fresh agent with all four
skills installed, and grades each by running the checker on whatever it
produced.

### Third-party files against their licences

```bash
python3 scripts/check_licences.py             # offline, on every push
python3 scripts/check_licences.py --upstream  # Material Symbols against their source
python3 scripts/eval/test_check_licences.py   # and that it fails when it should
```

Each third-party component is checked against what NOTICE says about it:
its files are there, its licence text beside them is that licence word
for word, each font's name table names the same family, holder and
licence, and every font, image and icon file in the repo belongs to a
component or to the repo's own work. With `--upstream` it fetches
Material Symbols from Iconify's repository, at a pinned commit, and every
outline and fill has to match path for path. The test breaks one thing at
a time -- a reworded licence, a missing skill licence, an unlisted image,
a swapped font, NOTICE dropping a component -- and each has to fail.

### The plugin

```bash
python3 scripts/eval/test_plugin.py
```

The plugin's pieces, without a model: the marketplace and plugin manifests
agree with each other and with `install.sh`'s version, `claude plugin
validate` passes (when the `claude` command is installed; CI installs it),
every command and agent has the frontmatter it needs and every path it names
exists, the agents can't edit files, and the hooks and the GitHub Action do
what they say. The SwiftUI hook reports a seeded file's violations
(violations first), stays quiet on a clean file, a non-Swift file and a
repeat, and never fails an edit. The commit guard denies a commit or push
that would take SF Pro along, follows `git -C` and a leading `cd` to the
right repository, lets the commit through once git ignores the font, still
catches a font already staged, and turns off with `ONPLATFORM_COMMIT_GUARD=off`. The
Action passes clean SwiftUI and a fresh design, fails the seeded app with an
annotation at each line, and only reports with `fail-on: none`. CI also runs
the Action itself, as another repository would.

To try the plugin in Claude Code without installing it, start
`claude --plugin-dir ~/Documents/GitHub/onplatform` in another folder and run
`/onplatform:ask how big must a button be on iPhone?`.

### The live preview

```bash
python3 scripts/eval/test_preview.py
```

`preview.py` serves a scaffolded design, and the test checks that the page
arrives with its reload script, other files arrive untouched, nothing
outside the folder can be read, an open page in Chromium reloads itself
after a file in the design changes, and `--phone` prints an address for a
phone.

### Measure what the plugin adds

```bash
claude plugin eval . --trust-plugin --tag quick --scaffold \
  --allow-tools Bash "WebFetch(domain:developer.apple.com)"
claude plugin eval . --trust-plugin --tag design --scaffold \
  --allow-tools Bash Write Edit "WebFetch(domain:developer.apple.com)"
```

`evals/` holds cases that `claude plugin eval` runs twice: once with the
plugin and once without, so the score says what the plugin adds rather than
what Claude does anyway. Each run is a real session on your account, so it
costs usage; `--runs 1` and `--max-cost-usd` keep a first try cheap. On Linux,
shell commands need `bubblewrap` and `socat` for the sandbox they run in.
Run it as an ordinary user, as on a Mac or a CI runner: run as root, the
sandbox leaves shell commands nothing they can write to, so the design cases
can't scaffold and score 0 with the plugin, which says nothing about it.

- **`quick`**: a HIG question, which has to give each platform's figure,
  both of Apple's figures for iPhone (the 44×44 default and the 28×28
  minimum) and a link to Apple's page; and a review of the seeded SwiftUI
  app, which has to name the VoiceOver labels, the fixed font sizes and the
  missing destructive role, and keep the 30-point buttons out of the
  violations.
- **`design`**: two whole briefs, an iPhone app and an Android one, graded
  on what lands on disk: the measured kit copied in rather than rebuilt, its
  recipes in the page, the empty state, no `#007AFF`, and for Android
  Material Symbols with no SF Symbols or iOS tab bar.

The `evals` workflow in GitHub Actions runs the same suite on demand, once
an `ANTHROPIC_API_KEY` secret is set.

### What a design hands on

```bash
pip3 install fonttools brotli        # once; reads fonts' name tables
python3 scripts/eval/test_check_distribution.py
```

`check_distribution.py` is the check a design passes before it's shared
or published. The test scaffolds every kind of design `new_project.py`
makes and requires each to pass `--purpose publish` as generated, licences
and all. Then it plants, one at a time, what a design picks up on the way:
SF Pro under its own name and renamed, SF Pro embedded in a Figma export,
SF Symbols from `sf_icons.py` in an iPad design and in an Android one, an
SF Symbols template, a design-resource rendering, an image hot-linked from
Apple, an SF Pro webfont, an image and a font nobody recorded, an embedded
image, Inter without its licence, Material Symbols without theirs, SF Pro
already committed to git. Each has to fail where it should and pass where
it may: SF Pro and SF Symbols pass in a mockup for an Apple platform while
git ignores them, and nowhere else.

---

## 6. One command that checks the rest

```bash
python3 scripts/doctor.py
```

Every number and path in this repo that can be resolved against reality
gets resolved: the topic and component counts against the references,
framework counts against `api-map.md`, the check total against a real run
of the verifier, every `scripts/*.py` named in a doc, every file a skill
promises it will have once installed, leftover placeholders, and that no
Apple text or images turn up (`scripts/provenance_guard.py`).

It exists because the same class of bug turned up four rounds running and
was found by hand each time — a hardcoded 949 against 947 files, a
SKILL.md claiming 2,280 rules after a re-scrape made it 2,326,
instructions naming a script renamed weeks earlier. All four are numbers
or paths a machine can resolve.

`build_design_tokens.py` runs `--fast` (everything
but the browser pass) at the end of every build, so a regenerated file
that no longer matches what the docs claim fails immediately rather than
months later.

What it will **not** catch: whether the values are right. A confidently
wrong measurement stated consistently everywhere passes cleanly. That's
what `verify_web_ui.py` and the eval runs are for.

### The live tests, several times over

```bash
python3 scripts/eval/run_live.py              # every live test, 3 runs each
python3 scripts/eval/run_live.py --only triggering,ui_kit_build --runs 5
```

The live tests ask a real model, and a model answers differently from one
run to the next, so a single pass proves less than it looks. This runs
each one several times and writes `scripts/eval/out/live/SUMMARY.md`:
pass rate per test, every failing line, and minutes per run. The file
ends with a DONE line only when every run has finished, so read it rather
than trusting a notice that something completed. Three runs of
everything takes a couple of hours, most of it the whole-app design
brief.

---

## 7. Where `motion-for-apple-platforms` comes from

`motion-for-apple-platforms` fills a real gap: the HIG covers motion as principle
and has no spring parameters at all. It defers values to `ui-kit-for-apple-platforms` and principles to
`hig-guide`, and says plainly which of its own claims are API fact and
which are one author's observation.

Its references are adapted from the MIT-licensed apple-design-skills
collection, with Apple values reconciled against `ui-kit-for-apple-platforms`'s
measurements; the notice is in `.claude/skills/motion-for-apple-platforms/LICENSE.txt`.

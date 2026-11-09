#!/usr/bin/env python3
"""Smoke-test deterministic parts of the design-workflow workflow.

No model call. It verifies platform-aware reference routing, structural
divergence evidence, content-design evidence, interaction-architecture
evidence, scaffold models, mechanical checks, direction evidence, and
optionally screenshot review setup.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DESIGN = os.path.join(ROOT, ".claude", "skills", "design-workflow")
SELECT = os.path.join(DESIGN, "select_references.py")
SCAFFOLD = os.path.join(DESIGN, "new_project.py")
CHECK = os.path.join(DESIGN, "check_design.py")
DIRECTION = os.path.join(DESIGN, "check_direction.py")
DIVERGENCE = os.path.join(DESIGN, "check_divergence.py")
CONTENT = os.path.join(DESIGN, "check_content.py")
INTERACTION = os.path.join(DESIGN, "check_interaction.py")
GRAMMAR_GATE = os.path.join(DESIGN, "check_grammar.py")
RENDER = os.path.join(DESIGN, "render_review.py")


def run(args, cwd=None, expect=0):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if p.returncode != expect:
        raise RuntimeError(
            f"command returned {p.returncode}, expected {expect}: {' '.join(args)}\n"
            f"stdout:\n{p.stdout}\nstderr:\n{p.stderr}")
    return p


def exists(path):
    if not os.path.exists(path):
        raise RuntimeError(f"missing expected path: {path}")


def test_reference_selector(tmp):
    ios = os.path.join(tmp, "REFERENCES-ios.md")
    run([sys.executable, SELECT, "--query",
         "analytics dashboard filters search status settings",
         "--model", "dashboard", "--platform", "ios", "--limit", "5", "-o", ios])
    text = open(ios, encoding="utf-8").read()
    if "developer.apple.com/design/human-interface-guidelines/" not in text or "ui-kit-for-apple-platforms/" not in text:
        raise RuntimeError("iOS selector lost HIG or measured visual provenance")

    mac = os.path.join(tmp, "REFERENCES-macos.md")
    run([sys.executable, SELECT, "--query",
         "mail sidebar toolbar search list detail menus",
         "--model", "list-detail", "--platform", "macos", "--limit", "5", "-o", mac])
    text = open(mac, encoding="utf-8").read()
    if "`.mac-" not in text or "`.ios-" in text or "`.ipad-" in text:
        raise RuntimeError("macOS selector should point at the Mac kit's recipes, and only those")

    watch = os.path.join(tmp, "REFERENCES-watchos.md")
    run([sys.executable, SELECT, "--query", "workout timer buttons list",
         "--platform", "watchos", "--limit", "3", "-o", watch])
    text = open(watch, encoding="utf-8").read().lower()
    if "no measured watchos kit" not in text or "measured recipe:" in text:
        raise RuntimeError("watchOS selector failed to state the measured-kit boundary")
    print("ok platform-aware reference selector")


def _content_fixture():
    return '''# Design direction

## What the product knows

Every question the interface asks is one the product declined to answer
for itself. Name what it infers, and where each answer comes from.

- **Inferred:** the place, from location and the time of day — a bill at
  8pm within fifty metres of a restaurant needs no venue field.
- **Inferred:** who is present, from the last group settled at this place
  and the people already in the conversation.
- **Inferred:** the total, from the photographed receipt rather than a
  typed figure.
- **Asked:** how to divide it, because that is the one thing the people
  at the table are still deciding — and guessing it wrongly is worse than
  asking.

## Content model

| Content | User question/task | Decision enabled | Content shape | Required context |
|---|---|---|---|---|
| SLA health | Are we within target today? | Decide whether intervention is needed | single metric + comparison | unit %, 90% target, prior day, freshness |
| Ticket trend | Is load improving or worsening? | Decide staffing/escalation | time series | tickets/hour, previous day comparison, last 12h |

## Representation decisions

| Content | Representation | Why this representation | Failure/misreading risk |
|---|---|---|---|
| SLA health | metric | One current value answers the opening question; target and prior period change interpretation | A bare percentage would hide whether 92% is good or bad |
| Ticket trend | chart | The analytical question is how volume changes over time; line shape matters more than exact lookup. Unit: tickets/hour. Comparison: previous day. | Missing periods could look like improvement, so gaps stay explicit |

## Content stress cases

- Zero tickets during a quiet hour without implying data failure.
- SLA falls below target and change becomes negative.
- A queue name expands to 48 characters without breaking hierarchy.

## State continuity

- **Invariant design idea:** today's service health remains the first-read question.
- **Loading:** reserve hero metric and trend geometry with skeletons; navigation remains usable.
- **Empty:** distinguish genuinely no tickets from not-enough-history; explain what can be done next.
- **Error:** keep global shell and last known context where safe; retry is primary in the failed region.
'''


def test_content_gate(tmp):
    root = os.path.join(tmp, "content-fixture")
    os.makedirs(root)
    valid = _content_fixture()
    path = os.path.join(root, "DESIGN.md")
    open(path, "w", encoding="utf-8").write(valid)
    run([sys.executable, CONTENT, root])
    broken = valid.replace("Why this representation", "Style")
    open(path, "w", encoding="utf-8").write(broken)
    run([sys.executable, CONTENT, root], expect=1)
    print("ok content gate accepts representation evidence and rejects unreasoned content")


def _interaction_fixture():
    return '''# Design direction

## Primary interaction flow

| Stage | User action | System response | State/context preserved | Failure/recovery |
|---|---|---|---|---|
| Entry | Select a ticket from the queue | Detail opens and the row remains selected | queue scroll position and current filters are preserved | if ticket disappeared, keep queue context and explain removal |
| Act | Change assignee and add a note | local controls update immediately while note remains editable | selected ticket and keyboard focus stay in detail | validation failure remains beside the note and preserves text |
| Commit | Press Command-Return to submit note | note enters pending state then confirms on server success | ticket selection and draft context are preserved until success | network failure restores editable draft and offers retry |
| Exit/continue | Move to next ticket | next row becomes selected and detail updates | queue position and filters are preserved | if pending work exists, keep draft and prevent silent loss |

## Commit model

- **Frame:** standalone app
- **Model:** explicit for notes; immediate for assignee changes.
- **When the change becomes real:** note after server acknowledgement; assignee optimistically with rollback on failure.
- **Undo/cancel/reversal policy:** note can be cancelled before submit; assignee offers Undo after success and rolls back automatically on failure.
- **Post-completion focus/selection/context:** selection stays on the current ticket and focus returns to the note composer after submission.

## Recovery and interruption

- **Failure condition:** network failure after optimistic assignee change triggers rollback and an inline retry message.
- **Interruption/resumption case:** navigating to another ticket while a note draft exists preserves the draft per ticket and restores it on return.
- **What is preserved:** queue filters, scroll position, selection history, and unsent draft.
- **Retry/rollback/restore behavior:** failed async work can retry in place; optimistic state rolls back without changing selection.

## Interaction stress cases

- Double-submit the note with mouse and keyboard nearly simultaneously; only one request is accepted.
- Change selection while assignee update is pending; completion applies to the original ticket without stealing focus.
- Go offline after typing a draft; the draft survives reconnect and can be submitted later.

## Keyboard and alternate input

- **Keyboard/command path where expected:** arrows move queue selection, Command-Return submits the note, Command-Z invokes Undo.
- **Escape/cancel and Return/commit semantics:** Escape closes transient UI or cancels an uncommitted edit; Return inserts a line break while Command-Return submits.
- **Focus restoration:** closing menus/popovers returns focus to their trigger; submission returns focus to the composer.
- **Touch/pointer alternative:** every keyboard command has a visible button/menu action and pointer path.
'''


def test_interaction_gate(tmp):
    root = os.path.join(tmp, "interaction-fixture")
    os.makedirs(root)
    valid = _interaction_fixture()
    path = os.path.join(root, "DESIGN.md")
    open(path, "w", encoding="utf-8").write(valid)
    run([sys.executable, INTERACTION, root])

    broken = valid.replace("note after server acknowledgement; assignee optimistically with rollback on failure.",
                           "changes happen somehow.")
    open(path, "w", encoding="utf-8").write(broken)
    run([sys.executable, INTERACTION, root], expect=1)
    print("ok interaction gate accepts complete task flow and rejects ambiguous commit semantics")


def test_divergence_gate(tmp):
    root = os.path.join(tmp, "divergence-fixture")
    os.makedirs(root)
    valid = r'''# Design direction

## Candidate directions

### Direction: A — Answer first
- **Frame:** the conversation — it lives in the thread
- **Model:** dashboard
- **Design idea:** Today's support health owns the screen while evidence explains it.
- **Primary region:** one service-health answer and current change
- **Secondary/contextual regions:** trend and queue evidence below the answer
- **Persistent chrome:** compact global navigation and time-range control
- **Compact transformation:** evidence becomes sequential below the primary answer
- **Strength:** fastest status comprehension during repeated monitoring
- **Risk:** can under-serve users who spend long sessions inside one ticket
- **Structural differences:** summary before records; contextual evidence instead of persistent list

### Direction: B — Queue workspace
- **Frame:** a glanceable surface — a widget on the Home Screen
- **Model:** workspace
- **Design idea:** The active queue owns the work surface while status remains contextual.
- **Primary region:** dense ticket queue and active selection
- **Secondary/contextual regions:** service health in a quiet summary strip and inspector
- **Persistent chrome:** destination sidebar and queue controls
- **Compact transformation:** sidebar collapses and selected ticket becomes sequential detail
- **Strength:** supports triage sessions where operators act more than monitor
- **Risk:** overall service health becomes slower to scan at a glance
- **Structural differences:** persistent queue instead of summary; simultaneous work region instead of evidence sequence

## Direction comparison

| Criterion | Direction A | Direction B |
|---|---:|---:|
| Primary-task fit | 5 | 4 |
| Hierarchy clarity | 5 | 4 |
| Information relationship | 4 | 5 |
| Platform fit | 5 | 5 |
| Adaptivity | 5 | 4 |
| Restraint | 5 | 3 |
| Distinctiveness through product logic | 4 | 5 |

**Trade-off interpretation:** Direction B is stronger for prolonged triage, but this product's most frequent opening task is checking current health before deciding whether action is needed. The extra persistent queue chrome therefore costs more than its stronger record relationship helps. Direction A does not win merely by total; its monitoring-first weakness is acceptable because deeper ticket work remains one step away.

## Rejected directions

- Rejected Queue workspace because monitoring is the dominant opening task; making the queue persistent would weaken first-read status clarity.

## Chosen direction

We chose Answer first because the user's recurring task is checking service health. It keeps current status primary, makes queue evidence available without competing for attention, and transforms to a sequential evidence flow on narrow screens.
'''
    path = os.path.join(root, "DESIGN.md")
    open(path, "w", encoding="utf-8").write(valid)
    run([sys.executable, DIVERGENCE, root])
    broken = valid.replace(
        "summary before records; contextual evidence instead of persistent list",
        "different layout")
    open(path, "w", encoding="utf-8").write(broken)
    run([sys.executable, DIVERGENCE, root], expect=1)
    print("ok divergence gate accepts structural comparison and rejects cosmetic/thin evidence")


def test_placeholder_discrimination(tmp):
    """Ordinary vocabulary passes; a genuinely unfilled slot does not.

    The gates used to match banned words as substrings anywhere in
    DESIGN.md. That made two of them unpassable -- they banned the very
    words their own templates mandate -- and left this one as a landmine:
    "todo" and "item 1" are ordinary in a notes or commerce product, and
    the content gate *requires* realistic content, so the two rules
    fought each other. What matters is not which word but where it sits.
    """
    root = os.path.join(tmp, "placeholder-fixture")
    os.makedirs(root)
    path = os.path.join(root, "DESIGN.md")
    base = _interaction_fixture()

    # Realistic product vocabulary, in prose. Must pass.
    prose = base.replace(
        "- Double-submit the note",
        "- Each ticket can carry an inline todo list; item 1 through "
        "item 14 stay numbered on reflow.\n- Double-submit the note")
    open(path, "w", encoding="utf-8").write(prose)
    run([sys.executable, INTERACTION, root])

    # A slot left as the template shipped it. Must fail.
    for unfilled in ("| Entry | TODO |", "| Entry | [pending] |"):
        broken = base.replace("| Entry | Select a ticket from the queue |",
                              unfilled)
        open(path, "w", encoding="utf-8").write(broken)
        run([sys.executable, INTERACTION, root], expect=1)

    print("ok placeholders distinguish ordinary vocabulary from unfilled slots")


def test_placeholder_helper():
    """Unit-level cover for the loose/strict split itself.

    The three gates are checked through their own fixtures, but the
    helper they all now share had none -- and it is the piece that
    decides whether "an inline todo list" is a design or an unfilled
    template. An early version stripped markdown emphasis along with
    list markers, which ate the "**" of a bold label and let
    "**When it becomes real:** TBD" through.
    """
    sys.path.insert(0, DESIGN)
    from gate_placeholders import find

    loose = ("lorem ipsum", "clean and modern")
    strict = ("todo", "tbd", "item 1", "replace this")
    cases = [
        ("Each note carries an inline todo list.", []),
        ("The table shows line item 1 through item 14.", []),
        ("Rows sorted by date; the todos most at risk surface first.", []),
        ("A TBD-style column is not what this means.", []),
        ("| Stage | todo | real |", ["todo"]),
        ("| Stage | **todo** | real |", ["todo"]),
        ("- **When the change becomes real:** TBD", ["tbd"]),
        ("- **When the change becomes real:** on server acknowledgement", []),
        ("## Content\n\nitem 1\nitem 2", ["item 1"]),
        ("- [todo]", ["todo"]),
        ("Body copy is lorem ipsum for now.", ["lorem ipsum"]),
        ("The design is clean and modern.", ["clean and modern"]),
        ("Replace this", ["replace this"]),
        ("Replace this control with a menu above five options.", []),
    ]
    for text, want in cases:
        got = find(text, loose=loose, strict=strict)
        if got != want:
            raise SystemExit(
                f"FAIL gate_placeholders: {text[:44]!r} -> {got}, want {want}")
    print("ok placeholder helper separates prose from unfilled slots")


GRAMMAR = """# Project design grammar

## Scope
- Product: support operations console, web first.
- Platform: web app; iOS reader planned.
- Evidence: three implemented screens plus the shared component sheet.

## Established rules
| Domain | Rule | Evidence | Scope |
|---|---|---|---|
| typography | Section heads are footnote caps | repeated on queue, detail and settings screens | all screens |
| spacing | Cards sit on a 16pt gutter | queue and dashboard screens; detail inspector | all screens |
| navigation | Sidebar is the only top-level switch | queue, dashboard and settings views | wide layouts |
| actions | Primary action lives in the toolbar | queue screen and detail view; never duplicated | all screens |
| selection | Selection survives detail navigation | queue screen, and restored on back | queue and detail |

## Canonical language
| Concept | Term | Icon |
|---|---|---|
| unresolved item | Ticket | tray |

## Adaptive transformations
| Structure | Wide | Compact | Invariant |
|---|---|---|---|
| queue and detail | side by side | sequential detail | selection and filters persist |
"""


def test_grammar_gate(tmp):
    """check_grammar.py had no test of any kind."""
    root = os.path.join(tmp, "grammar-fixture")
    os.makedirs(root)
    path = os.path.join(root, "PROJECT_GRAMMAR.md")
    open(path, "w", encoding="utf-8").write(GRAMMAR)
    run([sys.executable, GRAMMAR_GATE, root])

    # Drop two rules: the gate wants at least five, across four domains.
    thin = GRAMMAR.replace(
        "| actions | Primary action lives in the toolbar | queue screen and detail view; never duplicated | all screens |\n", "")
    thin = thin.replace(
        "| selection | Selection survives detail navigation | queue screen, and restored on back | queue and detail |\n", "")
    open(path, "w", encoding="utf-8").write(thin)
    run([sys.executable, GRAMMAR_GATE, root], expect=1)
    print("ok grammar gate accepts an evidenced grammar and rejects a thin one")


def test_declining_a_chart(tmp):
    """Naming a representation you rejected must not invoke its rules.

    The chart requirements fired on the word appearing anywhere in the
    section, so "a table, not a chart" was told to record the question,
    unit and comparison of the chart it had just ruled out. Choosing the
    simpler representation is the reduction the critique asks for.
    """
    root = os.path.join(tmp, "declined-chart")
    os.makedirs(root)
    path = os.path.join(root, "DESIGN.md")
    valid = _content_fixture()
    sec = re.search(r"(^#+\s+Representation decisions\s*$)([\s\S]*?)(?=^#+\s|\Z)",
                    valid, re.M | re.I)
    declined = valid[:sec.start(2)] + """
| Content | Representation | Why this representation | Failure/misreading risk |
|---|---|---|---|
| Queue volume | table | Operators need exact counts per queue; a chart would blur the numbers they read out on calls. | Shows the last good table with a stale marker. |
""" + valid[sec.end(2):]
    open(path, "w", encoding="utf-8").write(declined)
    run([sys.executable, CONTENT, root])

    # A chart actually chosen still owes its evidence.
    chart_row = next(l for l in valid.splitlines() if "| chart |" in l)
    undocumented = valid.replace(
        chart_row, "| Ticket trend | chart | It looks nice over time. | Might mislead. |")
    open(path, "w", encoding="utf-8").write(undocumented)
    run([sys.executable, CONTENT, root], expect=1)
    print("ok declining a representation does not invoke its requirements")


def test_visual_review_check(tmp):
    """--check is browserless, and had never been executed.

    render_review.py used re.search in check_review() without importing
    re, so every invocation of --check died with NameError -- the
    enforcement half of the visual review, the part that stops pending
    judgments shipping, had never run. It went unnoticed because the
    only test of this tool sits behind --browser and so does not run by
    default. Reading the sheet needs no browser, so this does.
    """
    root = os.path.join(tmp, "visual-review")
    os.makedirs(root)
    path = os.path.join(root, "VISUAL_REVIEW.md")

    pending = ("# Visual review\n\n## 1. Hierarchy\n\n"
               "[PENDING - inspect screenshots]\n\n"
               "## Review status\n\nPENDING\n")
    open(path, "w", encoding="utf-8").write(pending)
    run([sys.executable, RENDER, root, "--check"], expect=1)

    judged = pending.replace("[PENDING - inspect screenshots]",
                             "The eye reads the hero metric, then the tiles.")
    open(path, "w", encoding="utf-8").write(judged)
    run([sys.executable, RENDER, root, "--check"], expect=1)  # status still PENDING

    # However the reviewer emphasised the word -- the sheet's own
    # instruction shows it backticked.
    for form in ("COMPLETE", "`COMPLETE`", "**COMPLETE**"):
        done = judged.replace("## Review status\n\nPENDING\n",
                              "## Review status\n\n" + form + "\n")
        open(path, "w", encoding="utf-8").write(done)
        run([sys.executable, RENDER, root, "--check"])

    print("ok visual review --check rejects pending work and accepts finished work")


def test_cross_platform_tokens(tmp):
    """--kind cross has to deliver something the flag's name promises.

    It used to be a synonym for ios: it took the flag, emitted a web
    page, and left the native teams to copy hex codes out of a
    stylesheet. The contrast pass had already resolved every value for
    both appearances, so the exports and the CSS must agree by
    construction -- which is the property worth asserting, since two
    palettes that drift are worse than one.
    """
    out = os.path.join(tmp, "cross-tokens")
    run([sys.executable, SCAFFOLD, "--name", "Harbor", "--brand", "#1B2A4A",
         "--kind", "cross", "--screens", "Today,Vessels", "--thing", "vessels",
         "-o", out])
    tokens = os.path.join(out, "tokens")
    for filename in ("HarborColor.swift", "HarborColors.kt", "colors.xml"):
        exists(os.path.join(tokens, filename))

    css = open(os.path.join(out, "theme.css"), encoding="utf-8").read()
    xml = open(os.path.join(tokens, "colors.xml"), encoding="utf-8").read()
    kt = open(os.path.join(tokens, "HarborColors.kt"), encoding="utf-8").read()
    light = css.split("@media")[0]
    dark = re.search(r"@media \(prefers-color-scheme: dark\) \{(.*?)\n  \}",
                     css, re.S).group(1)

    for name, key in (("accent", "accent"), ("accent_text", "accentText"),
                      ("on_accent", "onAccent")):
        css_light = re.search(rf"--harbor-{name.replace('_', '-')}: (#\w{{6}})",
                              light).group(1).upper()
        css_dark = re.search(rf"--harbor-{name.replace('_', '-')}: (#\w{{6}})",
                             dark).group(1).upper()
        xml_light = re.search(rf'<color name="{name}">(#\w{{6}})<', xml).group(1).upper()
        xml_dark = re.search(rf'<color name="{name}_dark">(#\w{{6}})<', xml).group(1).upper()
        kt_light = "#" + re.search(rf"val {key} = Color\(0xFF(\w{{6}})\)", kt).group(1).upper()
        kt_dark = "#" + re.search(rf"val {key}Dark = Color\(0xFF(\w{{6}})\)", kt).group(1).upper()
        if not (css_light == xml_light == kt_light):
            raise SystemExit(f"FAIL {name} light differs: css {css_light}, "
                             f"xml {xml_light}, kotlin {kt_light}")
        if not (css_dark == xml_dark == kt_dark):
            raise SystemExit(f"FAIL {name} dark differs: css {css_dark}, "
                             f"xml {xml_dark}, kotlin {kt_dark}")
    print("ok cross-platform exports carry the same palette as the stylesheet")


def scaffold(tmp, kind, model, name):
    out = os.path.join(tmp, name)
    args = [sys.executable, SCAFFOLD, "--name", name, "--brand", "#4C7DFF",
            "--kind", kind, "--screens", "Home,Browse,Settings",
            "--thing", "items", "-o", out]
    if model:
        args[args.index("--screens"):args.index("--screens")] = ["--model", model]
    run(args)
    vendor = (("material-components.css", os.path.join("fonts", "roboto.css"))
              if kind == "android" else ("ios-tokens.css", "ios-components.css"))
    for rel in ("index.html", "DESIGN.md", "README.md", "theme.css") + tuple(
            os.path.join("vendor", v) for v in vendor):
        exists(os.path.join(out, rel))
    run([sys.executable, CHECK, out, "--no-browser"])
    run([sys.executable, DIRECTION, out], expect=1)
    run([sys.executable, DIVERGENCE, out], expect=1)
    run([sys.executable, CONTENT, out], expect=1)
    run([sys.executable, INTERACTION, out], expect=1)
    return out


def test_models(tmp):
    outputs = {}
    for model in ("workspace", "list-detail", "dashboard", "document"):
        outputs[model] = scaffold(tmp, "web", model, "web-" + model)
        print(f"ok web model {model}")
    outputs["ios-stack"] = scaffold(tmp, "ios", "stack", "ios-stack")
    outputs["ios-tabs"] = scaffold(tmp, "ios", "tabs", "ios-tabs")
    outputs["marketing"] = scaffold(tmp, "marketing", None, "marketing")
    print("ok iOS and marketing models; incomplete evidence correctly rejected")
    for model in ("sidebar", "document"):
        outputs["mac-" + model] = scaffold(tmp, "macos", model, "mac-" + model)
        exists(os.path.join(outputs["mac-" + model], "vendor", "macos-components.css"))
    print("ok macOS models")
    for model in ("sidebar", "tabs"):
        outputs["ipad-" + model] = scaffold(tmp, "ipados", model, "ipad-" + model)
        exists(os.path.join(outputs["ipad-" + model], "vendor", "ipados-components.css"))
    print("ok iPad models")
    for model in ("tabs", "stack"):
        outputs["android-" + model] = scaffold(tmp, "android", model, "android-" + model)
        theme = open(os.path.join(outputs["android-" + model], "theme.css"), encoding="utf-8").read()
        if "--md-sys-color-primary" not in theme or "--ios-" in theme:
            raise RuntimeError("an Android scaffold's theme.css is not a Material scheme")
    if "m3-navbar" in open(os.path.join(outputs["android-stack"], "index.html"), encoding="utf-8").read():
        raise RuntimeError("--model stack emitted a nav bar")
    print("ok Android models")
    return outputs


def test_ipad_chrome(project):
    """An iPad design with the iPhone's bottom tab bar, or with neither a
    sidebar nor tabs at the top, fails."""
    page = os.path.join(project, "index.html")
    original = open(page, encoding="utf-8").read()
    try:
        open(page, "w", encoding="utf-8").write(original.replace(
            '<main class="ipad-content',
            '<nav class="ios-tabbar"><button class="ios-tabbar__item" data-sf-symbol="house">Home</button></nav>'
            '<main class="ipad-content', 1))
        out = run([sys.executable, CHECK, project, "--no-browser"], expect=1).stdout
        if "bottom tab bar" not in out:
            raise RuntimeError("an iPad design with an iPhone tab bar was not called out:\n" + out)
        open(page, "w", encoding="utf-8").write(
            original.replace("ipad-sidebar", "side").replace("ipad-tabbar", "tabs"))
        out = run([sys.executable, CHECK, project, "--no-browser"], expect=1).stdout
        if "neither a sidebar nor tabs" not in out:
            raise RuntimeError("an iPad design without a sidebar or tabs was not called out:\n" + out)
    finally:
        open(page, "w", encoding="utf-8").write(original)
    print("ok an iPhone tab bar, or no sidebar or tabs, fails an iPad design")


def test_android_chrome(project):
    """An Android design wearing Apple chrome, or missing its top app bar, fails."""
    page = os.path.join(project, "index.html")
    original = open(page, encoding="utf-8").read()
    try:
        open(page, "w", encoding="utf-8").write(original.replace(
            '<main class="m3-body"',
            '<nav class="ios-tabbar"><button class="ios-tabbar__item" data-sf-symbol="house">Home</button></nav>'
            '<main class="m3-body"', 1))
        out = run([sys.executable, CHECK, project, "--no-browser"], expect=1).stdout
        if "Apple chrome" not in out:
            raise RuntimeError("an Android design with an iOS tab bar was not called out:\n" + out)
        open(page, "w", encoding="utf-8").write(original.replace("m3-topappbar", "appbar"))
        out = run([sys.executable, CHECK, project, "--no-browser"], expect=1).stdout
        if "an Android design without" not in out:
            raise RuntimeError("an Android design without its top app bar was not called out:\n" + out)
    finally:
        open(page, "w", encoding="utf-8").write(original)
    print("ok Apple chrome and a missing top app bar fail an Android design")


def test_mac_chrome(project):
    """A Mac design wearing iPhone chrome, or missing the window, fails."""
    page = os.path.join(project, "index.html")
    original = open(page, encoding="utf-8").read()
    try:
        open(page, "w", encoding="utf-8").write(original.replace(
            '<main class="mac-content"',
            '<nav class="ios-tabbar"><button class="ios-tabbar__item" data-sf-symbol="house">Home</button></nav>'
            '<main class="mac-content"', 1))
        out = run([sys.executable, CHECK, project, "--no-browser"], expect=1).stdout
        if "iPhone chrome" not in out:
            raise RuntimeError("a Mac design with an iOS tab bar was not called out:\n" + out)
        open(page, "w", encoding="utf-8").write(
            original.replace("mac-window", "window").replace("mac-toolbar", "toolbar"))
        out = run([sys.executable, CHECK, project, "--no-browser"], expect=1).stdout
        if "a Mac design without" not in out:
            raise RuntimeError("a Mac design without its window was not called out:\n" + out)
    finally:
        open(page, "w", encoding="utf-8").write(original)
    print("ok iPhone chrome and a missing window fail a Mac design")


def test_taps_and_figma(project):
    """Tabs that go nowhere and controls that do nothing fail; the Figma
    export captures a frame per state and per screen a control opens."""
    out = run([sys.executable, CHECK, project], expect=1).stdout
    for want in ("doesn't exist yet", "do nothing when tapped"):
        if want not in out:
            raise RuntimeError(f"the tap check missed {want!r}:\n" + out)
    page = os.path.join(project, "index.html")
    original = open(page, encoding="utf-8").read()
    try:
        extra = "".join(
            f'<div class="tabscreen" data-screen-id="{s}" hidden><h1 class="largetitle">{s.title()}</h1>'
            f'<main class="screen"><p>{s.title()} screen</p></main></div>\n' for s in ("browse", "settings"))
        open(page, "w", encoding="utf-8").write(original.replace('    <nav class="ios-tabbar">', extra + '    <nav class="ios-tabbar">', 1))
        out = run([sys.executable, CHECK, project], expect=1).stdout
        if "doesn't exist yet" in out:
            raise RuntimeError("built screens still reported missing:\n" + out)
        run([sys.executable, os.path.join(DESIGN, "export_figma.py"), project])
        exported = open(os.path.join(project, "figma", "figma-light-1.html"), encoding="utf-8").read()
        frames = exported.count('class="figma-frame"')
        if frames < 6 or "<script" in exported or "vendor/" in exported:
            raise RuntimeError(f"Figma export has {frames} frames or still links files")
    finally:
        open(page, "w", encoding="utf-8").write(original)
    print("ok dead taps and missing screens fail; the Figma export holds every screen and state")


def test_content_and_brand(tmp):
    """An iPhone design of lists alone fails, and so does one whose brand
    colour is in theme.css but nowhere on the screen. The scaffold, which
    opens on a hero in the brand colour, passes both."""
    project = os.path.join(tmp, "ios-brand")
    run([sys.executable, SCAFFOLD, "--name", "Supper", "--brand", "#C1552E", "--kind", "ios",
         "--model", "stack", "--screens", "Tonight", "--thing", "recipes", "-o", project])
    # It fails until its controls are wired (test_taps_and_figma); here
    # only the two verdicts matter.
    out = run([sys.executable, CHECK, project], expect=1).stdout
    for want in ("opens on content", "ok   index.html: the brand colour is"):
        if want not in out:
            raise RuntimeError(f"the scaffold should pass {want!r}:\n" + out)
    page = os.path.join(project, "index.html")
    original = open(page, encoding="utf-8").read()
    try:
        lists = re.sub(r'\s*<a class="ios-hero".*?</a>\s*<a class="ios-card".*?</a>', "", original,
                       count=1, flags=re.S)
        lists = re.sub(r'<svg class="ios-ring".*?</svg>', "", lists, flags=re.S)
        open(page, "w", encoding="utf-8").write(lists)
        out = run([sys.executable, CHECK, project, "--no-browser"], expect=1).stdout
        if "every screen is lists" not in out:
            raise RuntimeError("a design of lists alone was not called out:\n" + out)
        # The accent pointed back at the system blue: theme.css still
        # holds the brand, the screen shows none of it.
        blue = original.replace("</style>", "  :root { --ios-accent: #0088FF; --accent-text-safe: #0066CC; }\n</style>", 1)
        open(page, "w", encoding="utf-8").write(blue)
        out = run([sys.executable, CHECK, project], expect=1).stdout
        if "the brand colour #C1552E is" not in out or "not in the design" not in out:
            raise RuntimeError("a design that never shows its brand colour was not called out:\n" + out)
    finally:
        open(page, "w", encoding="utf-8").write(original)
    print("ok a design of lists alone, or one hiding its brand colour, fails")


def test_render_review(project):
    p = subprocess.run([sys.executable, RENDER, project], capture_output=True, text=True)
    if p.returncode != 0:
        combined = (p.stdout + "\n" + p.stderr).lower()
        if "playwright" in combined or "browser" in combined or "chromium" in combined:
            print("skip rendered review (browser unavailable)")
            return
        raise RuntimeError(f"render review failed:\n{p.stdout}\n{p.stderr}")
    exists(os.path.join(project, "VISUAL_REVIEW.md"))
    exists(os.path.join(project, ".visual-review", "audit.json"))
    run([sys.executable, RENDER, project, "--check"], expect=1)
    print("ok rendered review requires completed critique")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser", action="store_true")
    a = ap.parse_args()
    for path in (SELECT, SCAFFOLD, CHECK, DIRECTION, DIVERGENCE, CONTENT,
                 INTERACTION, RENDER):
        exists(path)
    with tempfile.TemporaryDirectory(prefix="design-workflow-smoke-") as tmp:
        test_reference_selector(tmp)
        test_content_gate(tmp)
        test_interaction_gate(tmp)
        test_divergence_gate(tmp)
        test_placeholder_discrimination(tmp)
        test_placeholder_helper()
        test_grammar_gate(tmp)
        test_declining_a_chart(tmp)
        test_visual_review_check(tmp)
        test_cross_platform_tokens(tmp)
        outputs = test_models(tmp)
        test_mac_chrome(outputs["mac-sidebar"])
        test_taps_and_figma(outputs["ios-tabs"])
        test_ipad_chrome(outputs["ipad-sidebar"])
        test_android_chrome(outputs["android-tabs"])
        test_content_and_brand(tmp)
        if a.browser:
            test_render_review(outputs["dashboard"])
    print("design workflow smoke test passed")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("FAIL " + str(exc), file=sys.stderr)
        sys.exit(1)
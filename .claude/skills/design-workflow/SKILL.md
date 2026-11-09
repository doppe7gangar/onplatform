---
name: design-workflow
description: Design or redesign a whole product (an app, site, dashboard, marketing page or cross-platform project) with Apple-level hierarchy, restraint, adaptivity and accessibility: the screens and how they connect, a scaffolded and tappable prototype, checked in a browser and critiqued from renders. Use whenever someone describes a product they want rather than asking about one control: "I want an app for splitting bills", "we need a landing page", "help me make a tool that…", "can you build me…", with or without the word design, a platform or a brand colour. Also for a design system or brand palette, a build that ships only its happy path, and turning an approved design into SwiftUI without losing screens, states or symbols. When the request names a product rather than a component this skill runs first, for Android too, in Material 3 with ui-kit-for-android. For a specific rule use hig-guide; for exact iOS values and CSS, ui-kit-for-apple-platforms; for animation, motion-for-apple-platforms.
---

# Apple Design Director

Specialists:
- `hig-guide` — authoritative platform rules, behavior, accessibility, components, APIs
- `ui-kit-for-apple-platforms` — measured iOS visual values/recipes where system appearance is not available
- `ui-kit-for-android` — measured Material 3 values/recipes, for Android apps
- `motion-for-apple-platforms` — interaction physics and animation
- `design-workflow` — hierarchy, content, divergence, composition, adaptivity, interaction architecture, coherence, project grammar, implementation audit, reduction, and critique

## Authority rule
Use `HIG → platform differences → system APIs/components → product composition → measured visual evidence (when available) → project grammar → design judgment`.

The measured visual corpus is iOS 27, from Apple's kit renderings checked against the colour variables in Apple's iOS and iPadOS 27 design kit; iPadOS 27 layouts from that same kit; and macOS 27, from Apple's macOS 27 design kit (fewer components). Never present an iOS measurement as macOS evidence, or the reverse.

## Governing principle
**Do not begin by placing components. Begin by composing information.** Prefer hierarchy through position, alignment, spacing, typography, scale, grouping, disclosure, motion, or context over unnecessary containers.

**Name the SF Symbol behind every icon.** They cannot ship here — Apple's licence covers using them inside apps that run on Apple platforms, not extracting them into a web kit — so every glyph in a mockup is a stand-in and the name is the part that has to be exact. Write `data-sf-symbol="house.fill"` on the slot. It costs an attribute and turns a drawing that resembles a house into `Image(systemName:)`, which is what the implementation actually needs. The status bar is symbols too, and its placeholder characters are placeholders. Once hig-guide's `sf_symbols.py --install` has copied the Mac's list, `check_design.py` checks every name against it; a name that doesn't exist reads as a spec and draws nothing.

**Draw the stand-in at the symbol's weight.** Measured from SF Pro's own symbol glyphs, SF Symbols stroke at 0.08em in regular and 0.11em in semibold: `stroke-width="2"` on a 24-unit `viewBox` beside regular text, about 2.7 beside semibold, always with round caps and joins. Strokes of 1.4 to 1.7, the web icon-set default, are what made generated lists read as a website. Use the filled shape when the name ends in `.fill`, and colour by meaning, as Health does with an orange flame and a red heart, rather than putting every glyph in the accent.

**Open on the content, not on a list.** An app made of grouped lists alone reads as Settings, however correct each row is. Apple's own apps lead with what the person came for -- Health with its figures, Fitness with rings, Weather with the sky, Home with a picture of the room -- and keep lists for the long tail beneath. Give the main screen a hero, a figure or a chart, and put the brand colour where the eye lands: on the hero, the figures and the selected tab, not only on a "+" button. `check_design.py` fails a design with no content anywhere, warns when the first screen is lists alone, and measures how much of the rendered first screen is the brand colour.

**Then express that hierarchy with the measured recipes, rather than rebuilding them.** Deciding structure first is not a licence to hand-roll the list, the navigation bar and the tab bar afterwards. `ui-kit-for-apple-platforms`'s `ios-components.css` carries the grouped-list metrics, the bar heights, the control geometry and the tracking this corpus measured from Apple's own renderings; a from-scratch approximation of them is the difference between a design that reads as iOS and one that reads as almost-iOS. Change the content, the composition and the palette. Keep the recipes. On the Mac the same goes for `macos-components.css`: the window, its traffic lights, the sidebar, the toolbar's glass controls and the 24pt controls measured from Apple's macOS 27 design kit. It has fewer recipes than iOS; where it has none, compose from `hig-guide` and say so.

## Size the process to the request
One screen or page takes the short path: a single primary task, with its sheets and states. That's most single-page requests: an expense tracker page, a settings screen, a sign-up form.

1. Route the platform and name the one question the screen answers: `references/platform-routing.md`, `references/content-hierarchy.md`.
2. Scaffold (step 12) and build the screen on it, with real content and its loading, empty and error states. On iPhone, compose each screen from the closest of the screens in `../ui-kit-for-apple-platforms/ios-screens.html` and its parts, not from memory: the main screens from the content-first ones (`#summary` opens on a hero and cards, `#detail` on the subject's picture, `#browse` on tiles), settings and forms from Apple's own (inset list, plain list, empty state, tab bar app). Colour and pictures belong in those content parts; elsewhere, no tinted circles behind row icons, no custom round buttons in rows, no card shadows or gradients, no icons typed as characters. The scaffold opens on a hero and a figure: replace them with the product's own. At phone width the scaffold drops the bezel but keeps the status bar, Dynamic Island and home indicator, so the design still reads as an iPhone app on a phone or in a screenshot. On a Mac, run `python3 ../ui-kit-for-apple-platforms/sf_icons.py ./design` so the icons are real SF Symbols. On iOS keep its large title: a top-level iOS screen without one reads as a web page. For an iPad app scaffold `--kind ipados` and keep the glass sidebar or the tabs at the top: with the iPhone's bottom tab bar it reads as a stretched phone. For a Mac app scaffold `--kind macos` and keep the window, sidebar and toolbar: with a tab bar or 17pt text it reads as an iPad app on a desk. For an Android app scaffold `--kind android` and keep the top app bar, nav bar and Material Symbols: with a tab bar, a large title or SF Symbols it reads as an iPhone port.
3. Make every control do something when tapped, with `prototype.js` (the scaffold copies it into the project's vendor folder) rather than a script per screen: `data-go="saved"` on a tab or sidebar row shows the screen `data-screen-id="saved"`, `data-push` opens a detail with `data-back` to return, `data-sheet` opens `data-sheet-id` and `data-dismiss` closes it, `data-toggle` flips a button or switch, and `data-toast="Saved"` confirms an action. Use the banner sparingly: in Apple's apps the change itself is usually the confirmation (the row updates, the checkmark appears). Build every screen the navigation names: a tab that goes nowhere is the first thing a reviewer taps. When a list opens a detail, every row should open its own: put the records in one `<script type="application/json" id="prototype-data">` block, `data-item="plants.fig"` on each row, and `data-field="name"` (or `data-field-src`, `data-field-tint`, `data-show`, and `data-each` with a `<template>` for a list such as a history) in the detail screen, which fills itself from the tapped row's record. Leave the screen's markup filled with the first record so it reads right before anything is tapped. A control that really is inert in the prototype takes `data-inert`.
   To watch it come together, serve it with live reload: `python3 preview.py ./design` in the background (`--phone` to open it on a phone on the same network), and give the person the address.
   Run `python3 check_design.py ./design` until it passes; it taps every control and fails the ones that do nothing. Keep scripts plain (`<script src>`, no `type="module"`, `import` or `export`): the design opens straight from a file, and browsers refuse to run modules there, so that part of the page silently does nothing.
4. Run `python3 render_review.py ./design`, look at the screenshots, and fix what they show. Then run `python3 render_review.py ./design --check`: the screenshots and the review must describe the page as it is now, not as it was before the fixes.
   Then `python3 stress_test.py ./design`: every screen and sheet at the largest text (iOS's AX3, Android's 200%), right to left, and with every string 40% longer, the way German runs. Fix its failures (text cut off, running off the screen, colliding), and look at its renders in `.visual-review/stress/`, which show what the numbers don't. Name directional symbols `chevron.backward` and `chevron.forward`, not `.left` and `.right`: only those mirror in Arabic and Hebrew.
   Then get a second opinion and act on it, at most twice: hand the folder to the plugin's `design-critic` agent, fix the changes it ranks highest (what the kit measures before what is taste), run `check_design.py` again, and send it back once more if the first round asked for more than three changes. Without the plugin's agent, or when you can't start one, critique it yourself in a separate pass: follow `references/visual-critique.md` against the screenshots alone, before rereading `DESIGN.md`, so you judge what is on the screen rather than what you meant.
5. Deliver the web page and, unless the person only wants the page, the Figma file too (step 18).
6. If the app is SwiftUI and the request includes the code, hand off (step 17).

Skip the rest. Divergence candidates, cross-screen coherence, project grammar and the implementation audit exist for products with several screens; on one screen they take most of the time for little of the value. Say in one line that you took the short path. A product with screens to move between, or a request for design directions, takes the full workflow below.

# Required workflow

## 1–11. Product reasoning
Follow these references in order as applicable:

1. `references/platform-routing.md` — platform/HIG routing and system-component preference
2. `references/content-hierarchy.md` — question/task → decision → representation
3. `references/design-invariants.md` — structural invariants
4. `references/spatial-models.md` + `references/design-divergence.md` — 2–3 credible directions
5. `select_references.py` — platform-aware evidence shortlist and inspection
6. `references/adaptivity.md` — architectural transformation across widths/input
7. `references/interaction-architecture.md` — entry → action → commit → recovery → continuation
8. `references/product-coherence.md` — cross-screen semantics and transition audit

Use realistic content, stress cases, explicit commit/recovery behavior, and task-driven differences rather than genre defaults.

## 12. Scaffold, then build on it
Once the platform and spatial model are chosen, generate the project instead of writing a page from scratch. That includes a one-screen request:

```bash
python3 new_project.py --name Ledger --brand "#0088FF" \
  --kind ios --model stack --screens "Expenses,Add Expense" -o ./design

python3 new_project.py --name Pulse --brand "#5A67D8" \
  --kind web --model dashboard --character dense \
  --screens "Overview,Reports,Settings" -o ./design

python3 new_project.py --name Pantry --brand "#2F7D5B" \
  --kind macos --model sidebar \
  --screens "All Recipes,Favorites,Recent" -o ./design

python3 new_project.py --name Pantry --brand "#2F7D5B" \
  --kind ipados --model sidebar \
  --screens "All Recipes,Favorites,Recent" -o ./design

python3 new_project.py --name Pantry --brand "#2F7D5B" \
  --kind android --model tabs \
  --screens "Home,Search,Saved,Profile" -o ./design
```

It copies the measured kit into the project (`./design/vendor/ios-tokens.css`, `./design/vendor/ios-components.css`, for `--kind ipados` `./design/vendor/ipados-components.css`, and for `--kind macos` `./design/vendor/macos-components.css`; for `--kind android` Roboto and `./design/vendor/material-components.css` instead), wires the brand into `theme.css` (for Android, a Material 3 scheme derived from it), and writes the `DESIGN.md` skeleton and the loading, empty and error states the gates check for. Replace its placeholder content with the real design. Don't paste copies of the tokens inline or rebuild the components it links. A hand-written page skips all of it, and the result looks almost like iOS instead of like iOS. Marketing pages select the editorial model on their own. If no generated model fits (`references/spatial-models.md`), scaffold the closest one and record in `DESIGN.md` where the design departs from it.

## 13. Extract or inherit the project design grammar
Read `references/design-grammar.md`.

If `PROJECT_GRAMMAR.md` exists, read it before designing new screens. Inherit applicable **established** rules by default. Allow justified exceptions when task, content, platform, or input model requires them.

After at least two meaningful screen/state families exist, create or refresh `PROJECT_GRAMMAR.md`. Classify rules as **established**, **provisional**, **exception**, or **retired**. Capture semantic typography, spacing, geometry/material meaning, navigation/selection, action placement, content representation, interaction, language/icons, useful repeated motion, and adaptive transformations.

Do not convert accidental repetition into a rule. Do not turn the grammar into a token dump.

## 14. Audit the implementation against the grammar
Once implementation exists, run:

```bash
python3 audit_grammar.py ./design
```

This creates `IMPLEMENTATION_GRAMMAR_AUDIT.md` from actual HTML/CSS evidence. It extracts repeated and one-off typography, spacing, geometry, surface/material patterns, semantic element usage, recurring labels, and repeated implementation classes.

**Observations are evidence, not automatic rules.** Review every generated prompt and decide whether the observation:

- confirms an established grammar rule;
- should remain provisional;
- is an intentional exception that needs documentation;
- is accidental drift/refactoring debt;
- contradicts or retires an older rule.

Set the audit status to `COMPLETE`, then verify:

```bash
python3 audit_grammar.py ./design --check
```

If implementation evidence changes the grammar, update `PROJECT_GRAMMAR.md` deliberately and rerun `check_grammar.py`. Never let code silently redefine the design system.

## 15. Plan component states and accessibility
Read `references/interaction-accessibility.md`. Check applicable focus, hover, pressed, selected, disabled, editing, loading, drag/drop, destructive/undo and inactive-window states plus scaling/zoom, assistive semantics, targets, non-color communication, Reduce Motion/Transparency, focus visibility, and recovery.

## 16. Compose and review
Compose regions, reading order, density, persistent/contextual chrome, and functional empty space before decorative material choices. Avoid card wallpaper, excessive pills, decorative glass/blur, gratuitous shadows, unsupported giant headings, duplicate primary actions, and decorative motion.

## 17. Hand off to SwiftUI
When the design is approved and the app is SwiftUI, write the views from the design rather than from memory of it. `references/swiftui-handoff.md` maps every kit component to its SwiftUI construct, shows the one-view, four-preview pattern for the loading, empty and error states, and lists what to leave behind: row heights, separators, radii and hex colours are what the browser had to be told and what iOS already draws. The brand colour goes in the `AccentColor` asset.

Then check that nothing was lost on the way, and that the Swift holds up on its own:

```bash
python3 check_handoff.py ./design ./MyApp
python3 ../hig-guide/check_swiftui.py ./MyApp
```

`check_handoff.py` reads the design for its screen titles, tabs, sheets, states, SF Symbols, components, button labels and accent, and reports each one it can't find in the Swift. It reads the Swift as text; nothing here compiles it. Say so when you hand over, and give the Mac steps at the end of the reference.

# Project gates

```bash
python3 check_divergence.py ./design
# All of them at once, in the order the evidence appears:
python3 grade.py ./design            # add --quick to skip the browser pass

# Or one at a time, when you want the full list of what a gate wants:
python3 check_content.py ./design
python3 check_interaction.py ./design
python3 check_coherence.py ./design
python3 check_grammar.py ./design          # once grammar is applicable
python3 audit_grammar.py ./design --check # after implementation audit is completed
python3 check_direction.py ./design
python3 check_design.py ./design
```

Rendered review:

```bash
python3 render_review.py ./design
```

Use `references/visual-critique.md` and record findings as **evidence → consequence → correction**. Review project-grammar adherence and implementation-audit findings alongside hierarchy, content, interaction, coherence, typography, density, adaptivity, accessibility, materials, platform authenticity, states, transitions, and reduction.

After revision:

```bash
python3 render_review.py ./design --check
```

## 18. Send it to Figma
The page is the prototype; Figma is where people comment on it and take it further. Once the design passes, export a frame for every state and every screen its controls open, in light and dark:

```bash
python3 export_figma.py ./design --dark
```

That writes figma-light-1.html and figma-dark-1.html into the design's figma folder, each standing on its own. Send each one with Figma's MCP server: call `html_to_figma` with the Figma file's key (`create_new_file` makes one; ask which team when there are several) and `cssSelector` `".figma-frame"`, then POST the file to the URL it returns:

```bash
curl -sS -f -X POST -H "Content-Type: text/html" --data-binary @design/figma/figma-light-1.html "<url>"
```

Give the person the Figma link. The frames arrive as plain layers, not as components linked to a library, and text keeps the page's fonts, so SF Pro shows as SF Pro only where Figma has it installed. Say both when you hand over.

If Figma's MCP server isn't connected, say so and give the one-time setup instead of skipping the step silently: `claude mcp add --transport http figma https://mcp.figma.com/mcp`, then `/mcp` inside Claude Code to sign in.

## 19. Before it leaves your hands
A design picks things up on the way that may not go where it goes: your own SF Pro from `--sf`, SF Symbols drawn by `sf_icons.py`, both embedded again in the Figma export, images someone dropped in. Before a design is pushed to a public repo, deployed, zipped for someone or attached anywhere, run:

```bash
python3 check_distribution.py ./design --purpose publish
```

It lists every file with its origin and licence, and fails on Apple's fonts and symbols (recognised by what they are, not what they're called), images from Apple's design resources or hot-linked from Apple's sites, the kit's files or fonts without the licence that has to travel with them, and any image or font nobody recorded in `assets.json`. Without `--purpose publish` it checks a working mockup: SF Pro and SF Symbols pass there in a design for Apple's platforms as long as git ignores them, and fail in an Android, web or marketing design. `new_project.py` writes a NOTICES.md into the design's vendor folder, with the licence files the check looks for; keep them with the design. A pass means nothing it knows to look for was found, not that every use is licensed: say so when you hand over.

# Complete loop

```text
brief
→ platform/HIG
→ read existing project grammar
→ hierarchy + content + invariants
→ divergence + reference inspection
→ adaptivity + interaction architecture
→ cross-screen coherence
→ extract/update project grammar
→ scaffold (new_project.py)
→ implement on the scaffold
→ implementation grammar audit
→ classify observed repetition/drift
→ update grammar deliberately if warranted
→ evidence gates + mechanical gate
→ rendered review
→ correction / reduction
→ rerender + completed audit checks
→ Figma (export_figma + html_to_figma)
→ SwiftUI handoff (check_handoff + check_swiftui)
→ before it's shared or published (check_distribution --purpose publish)
```

# Final standard
A successful result feels Apple-like because it is clear, restrained, adaptive, accessible, platform-correct, content-aware, behaviorally dependable, coherent across screens and transitions, and capable of maintaining its own evidence-backed design grammar—not because repeated CSS or rounded glass accidentally became the design system.
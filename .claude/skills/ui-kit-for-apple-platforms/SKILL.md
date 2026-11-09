---
name: ui-kit-for-apple-platforms
description: Apple's iOS 27, iPadOS 27 and macOS 27 design values (colour, type, control geometry, states) measured from Apple's own design kits, with ready recipes: CSS custom properties and component classes (navigation and tab bars, grouped lists, sheets, alerts, buttons, switches, segmented controls, sliders, empty states, Liquid Glass), accessible React components, a Tailwind v4/v3 theme, iPad split views, Mac windows, and tokens for SwiftUI, Jetpack Compose, Android XML, Flutter and React Native. Use whenever UI should look like Apple's where no system palette can be asked: a web app, landing page, dashboard, React/Vue/Svelte component, an iPad or Mac mockup, a Flutter or React Native app, a design system; whenever someone says "make it look like Apple", "iOS style" or "Apple aesthetic"; and when Apple-like UI gets details wrong. The values are measured, not remembered: the accent is #0088FF, not the #007AFF found online. For which control to use, how layouts adapt, and native SwiftUI/UIKit/AppKit work, use hig-guide.
---

# Apple UI for the web

Apple publishes its system palette — twelve colours and a six-step grey
ramp, each in light, dark and Increased Contrast — on the HIG's Color
page. It is easy to miss, because the values live in the *alt text* of
the swatch images (`R-0,G-136,B-255`) rather than as hex anywhere in the
prose. Grep for `#` and you find nothing, which is exactly what happened
here for most of this skill's life.

What Apple does not publish is everything else: the semantic colours
(`label`, `separator`, the fill ladder) are deliberately dynamic, and
control geometry, state treatments and materials are stated nowhere. The
UI kit renderings carry those, because a screenshot of a real component
is a rendering of the real values.

So this skill has three sources, and says which is which. Published
values come from the Color page. The colour variables in Apple's iOS and
iPadOS 27 design kit for Figma name every system colour in light and dark.
Measured values come from the kit's renderings — and every measured value
that overlaps either of the others matches it, which is the reason to
trust the ones that don't overlap.

| File | What it is |
|---|---|
| `tokens/` | **The measured values**, one file per target — see below. Generated; don't hand-edit. |
| `fonts/` | **Inter, bundled** (SIL OFL) — the non-Apple fallback for SF Pro, with its licence. |
| `ios-components.css` | **Web component recipes** built on the CSS tokens. Bars: `ios-navbar`, `ios-tabbar`, `ios-controls` (floating glass group), `ios-statusbar`. Content: `ios-list` (52pt rows, 26pt corners), `ios-empty`. Presentation: `ios-sheet`, `ios-alert`, `ios-actionsheet`. Controls: `ios-btn`, `ios-glass-btn`, `ios-switch`, `ios-segmented`, `ios-stepper`, `ios-slider`, `ios-chip`, `ios-field`, `ios-pagecontrol`. Material: `ios-glass`. Read a recipe's section of the file before using it: its selectors name the parts it expects inside. |
| `example.html` | Working reference page. Open it to see every recipe, light and dark. |
| `macos-components.css` | **macOS 27 recipes**, measured from Apple's macOS 27 design kit: `mac-window` with its traffic lights, `mac-sidebar`, `mac-toolbar` with glass `mac-tool`, `mac-toolgroup`, `mac-tabs` and `mac-toolsearch`, `mac-btn`, `mac-popup`, `mac-field`, `mac-search`, `mac-segmented`, `mac-check`, `mac-radio`, `mac-switch`, `mac-progress`, `mac-list`, `mac-table`, `mac-menu`, `mac-sheet`, `mac-alert`, `mac-popover`, `mac-empty`, `mac-inspector`. |
| `mac-example.html` | Every macOS recipe in four windows, light and dark. `verify_mac_ui.py` measures it. |
| `ipados-components.css` | **iPadOS 27 layouts** on top of the iPhone recipes, measured from Apple's iOS and iPadOS 27 design kit: the `ipad` frame and `ipad-statusbar`, `ipad-split` with the glass `ipad-sidebar` (toolbar, `ipad-search`, rows, headers), `ipad-content` with the floating `ipad-toolbar`, `ipad-tabbar` at the top centre and `ipad-title`, `ipad-sheet`, `ipad-popover`, `ipad-scrim`. |
| `ipad-example.html` | Three iPads — a split view with a popover, tabs at the top, a sheet — light and dark. `verify_ipad_ui.py` measures it. |
| `react/` | **React components** over the recipes (`ios.jsx`, types in `ios.d.ts`, `ios-react.css`), with the keyboard and screen-reader behaviour the static recipes can't have. `example.jsx` uses every one. |
| `tailwind/` | **Tailwind themes**: `theme.css` for v4, `preset.cjs` for v3. Utilities such as `bg-ios-accent`, `rounded-ios-card` and `ios-text-body` that read the kit's variables. |
| `ui-kit-tokens.json` | **Every measurement**, 945 renderings × colours + geometry + state. Query it for anything the recipes don't cover. |

## Picking a target

| Building for | Use | Note |
|---|---|---|
| Web, any framework | `tokens/ios-tokens.css` + `ios-components.css` | Recipes included |
| An iPad app, as a mockup | `ipados-components.css` over the iOS recipes | Split view, top tab bar, sheets; see **iPadOS** below |
| A Mac app, as a mockup | `macos-components.css` | Window, sidebar, toolbar, controls; see **macOS** below |
| React Native / JS | `tokens/tokens.ts` | Colours + metrics, typed |
| Android (Compose) | `tokens/AppleKitTokens.kt` | Light and dark objects |
| Android (views) | `tokens/colors.xml` | Light values |
| Flutter | `tokens/apple_kit_tokens.dart` | Light and dark classes |
| SwiftUI / UIKit | `tokens/AppleKitTokens.swift` | **Usually the wrong answer — read on** |
| Figma, Style Dictionary | `tokens/tokens.json` | Design Tokens format, with provenance |

**On Apple platforms, don't paste these literals.** `Color.accentColor`,
`UIColor.systemBlue`, `.primary` already resolve to the right value and
adapt to Dark Mode and Increase Contrast for free — and they'll track
whatever Apple changes next, which a hardcoded `#0088FF` won't. The Swift
export exists for the cases the semantic API can't reach: custom Core
Graphics drawing, a canvas, or matching Apple's palette deliberately. For
native work you almost certainly want **hig-guide** instead.

**On Android, think before reaching for this.** Material has its own
colour roles, its own switch, and its own conventions that users expect.
An iOS palette on Android is a legitimate choice when cross-platform
brand consistency is the deliberate goal; it is a bad default.

## Whole iPhone screens: start from Apple's

`ios-screens.html` opens with four screens composed the way Apple composes
them on the Examples page of its iOS and iPadOS 27 kit, from the kit's
parts and nothing else: an inset list (thumbnail row, stepper, date and time
capsules, pop-up value, switch, action row), a plain list with letter
sections, an empty state with its symbol in a circle, and a tab bar app.
Copy the closest one and change the content. `verify_ios_screens.py`
holds them to Apple's numbers: the large title at y 116, an inset list
20pt in and 362pt wide at y 183, 52pt rows and 68pt two-line rows, 39pt
letter sections, the empty state's circle at y 334 and its 52pt capsule
36pt in.

The parts they use: `ios-largetitle` (with `ios-largetitle__subtitle`),
`ios-list__text` + `ios-list__subtitle`, `ios-list__thumb`,
`ios-list__accessory`, `ios-list--plain` + `ios-list__section`,
`ios-pill`, `ios-stepper`, `ios-popup`, and `ios-empty--circle` with
`ios-empty--fill`.

What Apple's screens don't have, and a page that has them reads as a web
page dressed as an app: tinted circles behind list-row icons (Settings
uses a 30pt rounded square; the circle belongs to the empty state), round
custom buttons inside rows, shadows under cards, gradients on cards and
buttons, coloured section backgrounds, and icons typed as characters or
emoji. `check_design.py` fails the last one.

## Content first: what Apple's own apps open on

Those four screens are the system's chrome and its lists, and an app
built from them alone reads as Settings: grey page, white rows,
chevrons. Health, Fitness, Weather, Home and Journal open on the content
instead -- a big figure, a ring, a chart, a picture, a run of colourful
tiles -- and keep the list for the long tail underneath. The last three
screens in `ios-screens.html` are composed that way:

- `#summary`: a hero card the screen opens on, a card with a figure and a
  ring, a pair of tiles, over a tab bar.
- `#detail`: the subject's picture running up under a white status bar,
  glass controls on it, then a row of stats, a chart card and the history.
- `#browse`: a sideways carousel of picture cards, then a grid of tiles.

The parts, in `ios-components.css` under "Content first": `ios-hero`
(with `ios-art`, `ios-art--scrim`, `ios-hero__eyebrow`, `__title`,
`__body`, `__action`), `ios-headerhero` with `ios-statusbar--over`,
`ios-card` (`__head`, `__meta`, `__split`), `ios-metric` (`--hero`,
`--tinted`), `ios-ring`, `ios-bars`, `ios-progress`, `ios-badge`,
`ios-stats`, `ios-tiles` + `ios-tile` (`--filled`), `ios-carousel`,
`ios-sectionhead` and `ios-homeindicator`.

Each takes its colour from `--tint`, and with none set, from the accent,
so a brand theme colours all of them; set `--tint` or an `ios-tint-*`
class on a card and the ring, bars and art inside follow. Text in a tint
is mixed toward the label colour until it clears 4.5:1, and `ios-art`
caps how light it draws a pale brand so white words on it stay legible.
`ios-art` is artwork made from the tint and a large symbol, for when
there is no photograph; with one, put `<img class="ios-art__img">` inside.
Use the person's photos or ones whose licence allows it, never a
hotlinked image. These parts are composed, not measured -- Apple's kit
draws the controls, not the apps -- so they follow the kit's rhythm (26pt
corners, the 16pt gutter, the type scale) rather than a figure read off a
screen. `verify_ios_screens.py` holds them to it, and to their contrast.

**Real SF Symbols, on a Mac.** Every icon in the markup names its symbol
(`data-sf-symbol="leaf.fill"`) over a drawn stand-in. The stand-ins are
the quickest giveaway. On a Mac, `python3 sf_icons.py ./design` draws
each named symbol with the Mac's own SF Symbols and links them in; run it
again after adding icons. Elsewhere it leaves the drawings. Apple's
licence allows the symbols in mock-ups for its platforms but not handed
around on their own, so they stay in the design and out of this repo; a
design for Android, the web or a marketing site gets none. design-workflow's
`check_distribution.py` fails any design that would publish them.

## macOS

`macos-components.css` is the Mac's counterpart to the iOS recipes,
self-contained, and measured from Apple's macOS 27 design kit for Figma:
each corner, padding, row height and colour is the value Apple's own
components carry. Where the kit blends a translucent material over what
is behind it (the sidebar, menus, alerts), the stylesheet gives what that
blend renders over the surface it normally sits on. Values the kit
doesn't carry say so in the stylesheet.

What comes out of it, and what people get wrong from memory:

- **Windows** and sheets have 16pt corners. The traffic lights are
  **14pt circles 9pt apart** (a 23pt pitch), 19pt in from the window's
  edge and centred in the 52pt toolbar band. Not 12 on 20; that is the
  old Mac.
- **Toolbars** are a 52pt band whose controls are 36pt glass capsules
  holding 28pt buttons. A pressed or selected one is a grey capsule, not
  an accent fill.
- **Sidebars** are 240pt wide and run to the top of the window under
  the traffic lights. Rows are 32pt; a selected row is a **grey pill**
  with 8pt corners, inset 10pt. Icons are in the accent; the text keeps
  its colour. Section headers are 13pt bold grey.
- **Every regular control is 24pt**: push button, pop-up, text and
  search field, segmented control. Push buttons are **rectangles with
  6pt corners**, not capsules. Control text is SF Pro **Medium (510)**.
  A switch is 54×24 with a 32×20 capsule knob.
- **Text is 13pt**, not iOS's 17. Use the `--mac-text-*` styles, and
  `--mac-text-control` on anything clickable.
- A highlighted **menu** item is **#0069F9**, a selected **table** row
  **#0165E2**, both with white text: neither is the accent. Menus have
  12pt corners and 24pt rows; tables 20pt rows.
- An **alert** is 260pt wide with 34pt corners, a 13pt bold title over
  an 11pt message, left aligned, and 28pt capsule buttons stacked full
  width.

```html
<link rel="stylesheet" href="macos-components.css">

<div class="mac-desktop">
  <div class="mac-window">
    <div class="mac-lights"><span></span><span></span><span></span></div>
    <nav class="mac-sidebar">
      <div class="mac-sidebar__header">Library</div>
      <a class="mac-sidebar__item" aria-current="page">
        <span class="mac-sidebar__icon" data-sf-symbol="clock">…</span>Recents</a>
    </nav>
    <div class="mac-main">
      <header class="mac-toolbar">
        <h1 class="mac-toolbar__title">Recents<span class="mac-toolbar__subtitle">24 documents</span></h1>
        <span class="mac-toolbar__spacer"></span>
        <button class="mac-tool" aria-label="New Document" data-sf-symbol="plus">…</button>
      </header>
      <main class="mac-content">…</main>
    </div>
  </div>
</div>
```

The accent is the HIG's system blue, or the brand when a `theme.css`
from design-workflow bridges one in; the bridge fills the selections and
the menu highlight with it too. Set `--mac-accent` to change it by hand,
with `--mac-selection` and `--mac-menu-highlight` if those should follow.
The Mac kit's verifier, `python3 verify_mac_ui.py`, measures
`mac-example.html` against all of this in 87 checks. For a whole Mac app, design-workflow's
`new_project.py --kind macos` scaffolds the window.

## iPadOS

An iPad app is not a big iPhone. `ipados-components.css` carries the
iPadOS 27 shapes from Apple's iOS and iPadOS 27 design kit, on top of the
iPhone recipes:

- **The frame**: iPad Pro 11-inch, 1210 x 834 with 30pt screen corners; under 1300px wide (an actual iPad) the frame drops away.
- **Status bar**: 32pt, 16pt in, 14pt medium — the time, the date, then the app's menu, its name in bold.
- **Split view**: a 320pt Liquid Glass sidebar (#DADADA as the kit renders it; #EFEFEF when the window is inactive) starting under the status bar, 10pt in. Its toolbar is an Edit capsule and 44pt glass circles; under it a 44pt search capsule in Fills/Secondary, then 44pt rows: a 34pt symbol column in the accent, the title in body, detail in the vibrant secondary label. The selected row is a full-width capsule; section headers sit 21pt above and 11pt below in the secondary label.
- **Toolbar**: no bar. Glass controls float 10pt in under the status bar — one symbol is a 44pt circle, a group puts symbols on a 56pt pitch — with the large title, 34/41 bold, and an optional 15pt medium subtitle below, both vibrant. Content scrolling under them brings in the scroll edge effect.
- **Tabs at the top**: iPadOS puts the tab bar at the top centre — a glass capsule with 4pt around 36pt tabs in 15pt medium, the selected one on the neutral capsule in the accent, a 54pt sidebar toggle leading and search trailing. Never the iPhone's bottom tab bar.
- **Sheets** float centred under the status bar, 936pt wide, with 38pt corners, a 60 x 4 grabber and the window dimmed 20%. **Popovers** share the 38pt corners and point a 56 x 13 arrow at their source.

```html
<link rel="stylesheet" href="tokens/ios-tokens.css">
<link rel="stylesheet" href="ios-components.css">
<link rel="stylesheet" href="ipados-components.css">

<div class="ipad">
  <div class="ipad-statusbar">…<span class="ipad-statusbar__app">Mail</span>…</div>
  <div class="ipad-split">
    <nav class="ipad-sidebar">
      <a class="ipad-sidebar__row" aria-current="page">
        <span class="ipad-sidebar__icon" data-sf-symbol="tray">…</span>
        <span class="ipad-sidebar__title">Inbox</span></a>
    </nav>
    <main class="ipad-content">
      <header class="ipad-toolbar">
        <div class="ipad-toolbar__controls">…</div>
        <div class="ipad-title"><h1>Inbox</h1></div>
      </header>
    </main>
  </div>
</div>
```

The iPad kit's verifier, `python3 verify_ipad_ui.py`, measures
`ipad-example.html` against all of this in 67 checks. For a whole iPad
app, design-workflow's `new_project.py --kind ipados` scaffolds it.

## Using it

For the web, start by copying the kit into the project, before writing
any CSS of your own:

```bash
cp -R <this skill's directory>/{tokens,fonts,ios-components.css} ./
```

Then load the tokens first:

```html
<link rel="stylesheet" href="fonts/inter.css">
<link rel="stylesheet" href="tokens/ios-tokens.css">
<link rel="stylesheet" href="ios-components.css">
```

**Copy the font files too — don't link a CDN.** The fonts in `fonts/`
are the point: the two Inter cuts ship here so a page needs no network
fetch at all. Reaching for
`fonts.googleapis.com` to load Inter gives you a slower page, a
third-party dependency, and nothing offline — and asked to build a
settings screen, that is exactly what happened in testing while the
bundled fonts sat unused in the skill directory. If the deliverable is a single
self-contained file, inline `tokens/ios-tokens.css` and
`ios-components.css` verbatim, `--ios-*` names and all, and base64 the
one font you need, or copy `fonts/` next to it. Either beats a CDN.

**Build with the kit, not beside it.** Use the recipes' classes
(`ios-list`, `ios-navbar`, `ios-btn`, …) and the `--ios-*` variables.
Don't re-declare the kit's values under your own names
(`--accent: #0088FF`), and don't rebuild a list, bar or button the
kit already has. In testing, a page built that way got every colour
right and still looked almost like iOS rather than like iOS, because
the lists, bars and buttons around those colours were approximations,
not the measured recipes.

Then use the tokens rather than literals. `var(--ios-accent)` adapts to
dark mode on its own; `#0088FF` does not.

```html
<button class="ios-btn ios-btn--filled">Continue</button>
<button class="ios-btn ios-btn--tinted">Learn More</button>
<button class="ios-btn">Cancel</button>
<button class="ios-btn ios-btn--filled ios-btn--destructive">Delete</button>

<label class="ios-switch">
  <input type="checkbox" checked><span class="ios-switch__track"></span>
</label>
```

For Vue or Svelte, use the CSS as-is and keep the token layer: the
recipes are plain classes with no JS.

### React

`react/ios.jsx` renders the recipes' markup and adds what a static page
can't: a sheet that opens on its first field, keeps Tab inside, closes
on Escape and gives focus back to what opened it; an alert that starts
on Cancel; tabs that follow the arrow keys; switches named by their row;
tappable rows that are real buttons, named "title, value". Copy it with
the kit:

```bash
cp -R <this skill's directory>/{tokens,fonts,ios-components.css,react} ./src/ios/
```

```jsx
import "./ios/tokens/ios-tokens.css";
import "./ios/ios-components.css";
import "./ios/react/ios-react.css";
import { NavBar, LargeTitle, List, Row, Switch, Sheet, useCollapsed } from "./ios/react/ios.jsx";

<NavBar title="Settings" collapsed={useCollapsed()} />
<LargeTitle>Settings</LargeTitle>
<List header="Reminders">
  <Row title="Daily nudge" accessory={<Switch checked={on} onChange={setOn} />} />
  <Row title="Account" value="Signed in" onClick={openAccount} />
</List>
```

Pass `symbol="fork.knife"` wherever an icon goes: the drawing is your
stand-in, the name is what an Apple-platform build needs. Light mode
keeps Apple's own palette, so a contrast audit flags the same places the
contrast section below describes, and only those.

### Tailwind

The themes map utilities onto the kit's variables, so Tailwind classes
follow Dark Mode and Increase Contrast exactly as the recipes do. Load
the tokens as well as the theme:

```css
/* v4 */
@import "tailwindcss";
@import "./ios/tokens/ios-tokens.css";
@import "./ios/ios-components.css";
@import "./ios/tailwind/theme.css";
```

For v3, `presets: [require("./ios/tailwind/preset.cjs")]` in the config,
and the two CSS files in your stylesheet. v3 can't put an opacity
modifier on a variable colour (`bg-ios-accent/50`); v4 can.

Utilities for the parts, recipes for the components: `bg-ios-bg-card`
and `px-ios-gutter` lay out your own content, while a list is still
`ios-list`, which carries row heights, separators and insets that a
string of utilities would only approximate.

## The values that are *not* what people think

Anyone hand-coding "iOS colours" from memory or from a search result gets
these wrong, and wrong in a way that reads as slightly-off rather than
obviously broken:

| | iOS 27 (measured) | What's usually used |
|---|---|---|
| Accent blue | `#0088FF` | `#007AFF` |
| Destructive red | `#FF383C` light / `#FF4245` dark | `#FF3B30` / `#FF453A` |
| Text on glass — bars, buttons, tabs | `#1A1A1A` light / `#F5F5F5` dark | `#000000` / `#FFFFFF` |
| Plain text | `#000000` / `#FFFFFF` | `#1A1A1A` everywhere, from this kit's own past |

Two independent things back these up, and they cover different values.

The second row is a correction. An earlier version of this kit read its
"label" off a glass button and put `#1A1A1A` on every line of text; the
kit's variables name two labels — Labels/Primary, black, and Labels -
Vibrant/Primary, `#1A1A1A`, for text on glass — and the tokens now carry
both as `--ios-label` and `--ios-label-vibrant`.

**External agreement** where Apple's semantics are known: the switch
reads `#34C759` light and `#30D158` dark, exactly systemGreen for each
appearance, and the secondary-label and placeholder greys land on
`rgba(60,60,67,0.6)` and `rgba(60,60,67,0.3)` to the digit.

**Internal corroboration** for the values nothing external confirms —
how many separate components the same hex turns up in:

| Value | Components |
|---|---|
| `#1A1A1A` label on glass | **15** |
| `#0088FF` accent | **9** |
| `#0091FF` accent dark | **8** |
| `#FF383C` red | **5** |
| `#F5F5F5` label on glass, dark | **5** |

A misread of one PNG cannot put the same hex in fifteen unrelated
components. Note the inversion: the values that disagree with the
palette circulating online are the *best* corroborated, while
systemGreen — the one with external confirmation — appears in only two.
`doctor.py` fails the build if any measured colour drops to a single
component.

The measurements that match Apple's published semantics are what — the switch reads `#34C759` in light and
`#30D158` in dark, exactly systemGreen for each appearance, and the
secondary-label and placeholder greys land on `rgba(60,60,67,0.6)` and
`rgba(60,60,67,0.3)` to the digit.

## Details that decide whether it reads as Apple

Most "iOS-style" web UI fails on these rather than on colour:

- **Grouped backgrounds are a pair, and the order matters.** A grey page
  (`--ios-bg`) with white cards floating on it (`--ios-bg-card`), not a
  white page with grey cards. Inverting this is the single fastest way to
  look not-quite-right.
- **Separators start at the text, not the card edge**, and the last row
  has none. `.ios-list__row + .ios-list__row::before` does this; a plain
  `border-bottom` doesn't.
- **Translucent greys, not solid ones.** Apple's fills and secondary
  labels are one base grey at several opacities, so they sit correctly on
  any background. `rgba(60,60,67,0.6)` — never its flattened equivalent.
- **Capsule buttons.** iOS 26 moved to fully rounded buttons; a 8px
  radius reads as an older OS.
- **44px hit targets.** `buttons.md` states 44×44 pt as the general rule.
  The 28×28 in the accessibility table is a floor for minor controls, not
  a licence to shrink the primary action.
- **Type scale, exactly.** 17/22 body, 34/41 large title, 13/18 footnote.
  The tokens are complete `font` shorthands so `font: var(--ios-text-body)`
  is valid on its own — a shorthand without a family is invalid CSS and
  the browser silently drops it, leaving everything at 16px while still
  looking broadly plausible.

## Liquid Glass

A plain `backdrop-filter` is why most "iOS 26 style" web UI looks flat.
Measured off `Materials/_Liquid Glass` at 4×, the surface is four layers,
and the blur is the least of them:

- **Rim.** Not uniform. Light comes from above, so in dark mode the top
  edge is `#7E7E7E` against a `#1A1A1A` body — a bright specular line —
  while the sides fall to `#151515`, *darker* than the body. In light
  mode the whole rim is darker than the face (`#C5` top, `#97` sides on
  `#F9F9F9`), so it reads as an outline instead.
- **Falloff.** Just inside the rim, a band grading back to the body over
  ~1.5 pt: `#949494 → #434343 → #1F1F1F → #1A1A1A`.
- **Body.** Very slightly darker at the centre than at the edges.
- **Ambient shadow.** Wide and soft — 8% black in light, 15% in dark at
  the edge, still 3–5% sixteen points out.

```html
<button class="ios-glass ios-glass--light ios-glass-btn ios-glass--capsule">
  Focus
</button>
```

Tint variants, measured rather than invented. "Light" and "Dark" Liquid
Glass are the same neutral grey at two strengths, not a white/black pair,
and "Prominent" isn't a tint at all — it's the accent filled solid:

| Class | Value | Use |
|---|---|---|
| `.ios-glass--light` | `rgba(115,115,128,.078)` | over busy or bright content, so colour survives |
| `.ios-glass--dark` | `rgba(116,116,128,.18)` | over quiet content, where the control must separate |
| `.ios-glass--prominent` | `var(--ios-accent)`, opaque | the primary action |
| `.ios-glass--clear` | minimal tint | over vivid artwork |

`.ios-navbar` and `.ios-tabbar` are glass already.

**It only works over something.** Glass is a refraction; on a flat
background there is nothing to refract and nothing to blur, and it
collapses to a grey box. If a design has no photography, gradient, or
scrolling content behind the bars, glass is the wrong material — reach
for a plain surface rather than faking it.

`prefers-reduced-transparency` drops every glass surface to an opaque
one, which is the setting Apple's own Reduce Transparency maps to.

## Typography is where it stops looking like SF

Getting the family right is the easy half. Two things decide whether the
type actually reads as Apple, and both are counterintuitive.

**Tracking is not monotonic.** Apple publishes a per-size table
(Apple's typography page, *Tracking values → SF Pro*; the figures are in `tokens/sf-pro-tracking.json`) and the sign flips:

| Style | Size | Tracking |
|---|---|---|
| Large Title | 34 pt | **+0.012em** |
| Title 1 | 28 pt | **+0.014em** |
| Title 2 | 22 pt | −0.012em |
| Body / Headline | 17 pt | −0.026em |
| Footnote | 13 pt | −0.006em |
| Caption 2 | 11 pt | +0.006em |

Large type is tracked **looser**, not tighter. The intuition that big
text tightens is wrong here, and it is wrong on the most prominent text
on the screen. On Apple platforms the font's `trak` table applies these
automatically; browsers ignore `trak`, so they must be set as
`letter-spacing`. Use `var(--ios-track-<style>)` beside every
`var(--ios-text-<style>)`.

**SF's weight axis is not the CSS ladder.** Read off the variable font's
named instances:

| | Ultralight | Thin | Light | Regular | Medium | Semibold | Bold | Heavy | Black |
|---|---|---|---|---|---|---|---|---|---|
| `wght` | 31 | 111 | 274 | 400 | **510** | **590** | 700 | 860 | 1000 |

Medium is 510 and Semibold is 590. `font-weight: 600` asks for something
between two real weights that Apple never ships — close enough to look
fine and wrong enough to feel off. Use `var(--ios-weight-semibold)`.

Both sets are generated, not typed: the tracking is parsed out of
Apple's typography page and the weights come from the font's own `fvar` table.

## Contrast: Apple's light palette does not clear Apple's own table

Worth knowing before you ship text in it. `accessibility.md` requires
**4.5:1 up to 17 pt**, 3:1 at 18 pt or bold. Measured, on the light
grouped background:

| Pair | Ratio | |
|---|---|---|
| `--ios-label` on card | **17.4:1** | fine |
| `--ios-label-secondary` on card | **3.44:1** | under 4.5 |
| `--ios-accent` as text on page | **3.15:1** | under 4.5 |
| `--ios-red` as text on card | **3.57:1** | under 4.5 |
| `--ios-label-tertiary` on card | **1.73:1** | placeholder only, never content |
| white on filled accent button | **3.52:1** | passes — the label is semibold, so 3:1 applies |

Dark mode clears 4.5:1 on every one of these. Light is where it bites.

This is a property of Apple's real values, not a mistake in the recipes,
and it is survivable on iOS because Increase Contrast adapts the system
colours at render time. Nothing does that for you on the web. So:

- **Body-size text carrying meaning → `--ios-label`.** Secondary and
  tertiary are for supporting text, and even then they are under the
  threshold in light mode.
- **Accent-coloured text** (plain buttons, links) is at 3.15–3.52:1.
  Fine for a short interactive label people expect to be blue; not fine
  for a paragraph.
- **`prefers-contrast: more` is wired up** and darkens accent, red, and
  secondary just enough to clear 4.5:1 with the hue kept. That is the
  web port of Increase Contrast — leave it in.

`scripts/verify_web_ui.py` asserts all of this in a real browser, so a
change that breaks it fails rather than merely looking fine.

## What does not transfer, and don't pretend it does

- **SF Pro — bring your own.** Apple's licence doesn't allow
  redistributing it, so the kit doesn't ship it, and off Apple devices
  the stack lands on Inter. Macs, iPhones and iPads need nothing:
  `-apple-system` leads the stack and is the system's own SF Pro.

  Anyone with Apple's download can use their own copy for mockups: copy
  `SF-Pro.ttf` into `fonts/` and link `fonts/sf.css` **after**
  `tokens/ios-tokens.css`, which would otherwise set `--ios-font` straight
  back. The scaffold does the same with `new_project.py --sf
  /path/to/SF-Pro.ttf`. Load the file rather than relying on an installed
  copy found by name: the variable font's optical size defaults to
  Display, and only a loaded file gets it set from the text size. Found
  by name on Linux, 17pt text came out 11% too tight. The copy is
  gitignored; keep it off public sites.

- **Liquid Glass — the refraction only.** The live bending of what sits
  behind the surface has no browser equivalent. Everything else about it
  does, and is built: see below.
- **Dynamic Type.** The web equivalent is `rem` plus the browser's own
  text scaling, which the tokens use. It is not the same thing — there is
  no accessibility-size ladder.
- **Native behaviour.** Sheet physics, rubber-band scrolling, haptics,
  swipe-back. Approximating these badly is worse than leaving them out.

Say so when it comes up. A page that honestly borrows Apple's visual
language beats one that claims to be indistinguishable and isn't.

## Anything the recipes don't cover

`ui-kit-tokens.json` holds every measurement, one record per rendering,
with `component`, `appearance`, `state`, `size_pt`, `radius_pt` and the
colours with their alpha and coverage share. Query it directly:

```bash
python3 - <<'EOF'
import json
rows = json.load(open("ui-kit-tokens.json"))
for r in rows:
    if r["component"] == "Sliders" and r["appearance"] == "light":
        print(r["file"], r["size_pt"], r["radius_pt"],
              [c["css"] for c in r["colours"][:3]])
EOF
```

Components measured include Alerts, Action Sheets, Tab Bars, Keyboards,
Notifications, Date & Time Pickers, Steppers, Sliders, Text Fields,
Materials, Page Controls, Pop-up Buttons, Context Menus and App Icons.

Re-measure after changing the kit, then re-verify:

```bash
python3 scripts/extract_ui_kit_tokens.py   # PNGs  -> ui-kit-tokens.json
python3 scripts/build_design_tokens.py     # JSON  -> CSS, Swift, Kotlin,
                                           #    XML, Dart, TS, tokens.json
python3 scripts/verify_web_ui.py           # asserts the rendered result
```

`verify_web_ui.py` drives a real browser over `example.html` and checks
computed values, not appearance: every token resolves, the type scale
lands on Apple's published numbers to the pixel, the switch measures 64x28
with a 38×24 pill knob travelling 22px, hit targets clear 44px, separators skip each
list's first row, the grouped backgrounds are the right way round, and
every colour pair meets the contrast it should, a bundled face
actually renders rather than falling through to a substitute, and the
iOS 27 kit's own shapes hold: the 62pt tab bar with 54pt tabs and 10pt
labels, the 62pt status bar with its 17pt clock, monochrome glass
controls, a navigation bar with no material until content scrolls under
it, and plain and glass text in their two labels. 218 checks across
light, dark, and increased contrast.

## Rules, not just looks

This skill carries appearance. It does not carry Apple's guidance about
*when* to use what — whether a thing should be a sheet or a popover,
whether an alert is warranted, how a layout should adapt. That's the
**hig-guide** skill, which routes to Apple's official pages, holds the spec figures, and
the platform differences. Reach for it whenever the question is about
behaviour or structure rather than pixels, and for any native SwiftUI,
UIKit, or AppKit work.

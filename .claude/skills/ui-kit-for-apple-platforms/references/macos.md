# macOS

_Part of ui-kit-for-apple-platforms. File paths are relative to the skill's folder, one level up._


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

**Content first on the Mac.** `macos-components.css` has the same
content parts at Mac sizes -- `mac-hero` with `mac-art`, `mac-card`,
`mac-metric`, `mac-ring`, `mac-bars`, `mac-badge`, `mac-stats`,
`mac-tiles`, `mac-sectionhead`, and `mac-summary` to set a hero beside
two cards -- for an app about its content (Music, Weather, Home) rather
than about managing files. They take `--tint` and the `mac-tint-*`
classes the same way. On iPad, use the iOS parts: `ipados-components.css`
loads with `ios-components.css`.

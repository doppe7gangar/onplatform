# iPadOS

_Part of ui-kit-for-apple-platforms. File paths are relative to the skill's folder, one level up._


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

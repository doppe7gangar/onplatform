---
name: ui-kit-for-android
description: Material 3 for Android designs, measured from Google's Material 3 Design Kit: light and dark colour roles, Roboto type scale, shapes, CSS recipes for app bars, nav bar and rail, buttons, FABs, chips, cards, lists, fields, dialogs and sheets, Material Symbols, and a theme builder from one brand colour for CSS, Jetpack Compose or Android XML. Use whenever something should look like a native Android app: "design an Android app", "Material You", "Material 3", "make it look like a Pixel app", a Play Store screenshot, an Android version of an iOS design.
---

# Material 3 for the web

An Android design that is a web page in a phone frame gives itself away
in seconds: the bar is the wrong height, the title the wrong size, the
corners too round or not round enough, the colours picked by eye so the
containers are too saturated and dark mode is a different hue. This kit
removes the guessing. Every number in `material-components.css` was
measured from Google's Material 3 Design Kit for Figma, and the colours
come from the same algorithm Android uses, so a brand colour turns into
a scheme that reads as Android rather than as a palette.

| File | What it is |
|---|---|
| `material-components.css` | Colour roles (light and dark), type scale, shape, elevation, and every component recipe |
| `fonts/roboto.css` | Roboto, variable weight, bundled (SIL OFL) |
| `build_m3_theme.py` | One brand colour → a full Material 3 scheme, as CSS, Compose or Android XML |
| `icon.py` | Material Symbols as inline SVG: 158 common icons, outlined and filled, drawn for 24 dp |
| `icons/names.txt` | Every Material Symbols name, so a checker can tell a real icon from a made-up one |
| `android-example.html` | Five phones and a component sheet, light and dark. `verify_android_ui.py` measures it. |
| `check_compose.py` | Material 3 problems in Jetpack Compose code that the code alone decides: text under 11 sp, literal colours, unlabelled icon buttons, targets under 48 dp, Material 2 imports |

## Use it

For a whole app, let design-workflow scaffold it, which wires all of this
up and adds the four states:

```bash
python3 ../design-workflow/new_project.py --name Pantry --brand "#C1552E" \
  --kind android --model tabs --screens "Home,Search,Saved,Profile" -o ./design
```

By hand, link the font, the recipes, then your theme, in that order:

```html
<link rel="stylesheet" href="fonts/roboto.css">
<link rel="stylesheet" href="material-components.css">
<link rel="stylesheet" href="theme.css">
```

```bash
python3 build_m3_theme.py "#C1552E" -o theme.css                       # the web
python3 build_m3_theme.py "#C1552E" --format compose -o Color.kt       # Jetpack Compose
python3 build_m3_theme.py "#C1552E" --format xml -o colors.xml         # Android views
python3 build_m3_theme.py "#C1552E" --secondary "#2E6BC1" -o theme.css # a second brand colour
```

The brand colour is a *seed*, not the primary. Android reads its hue and
chroma, builds tonal palettes from them, and takes primary from tone 40
in light and tone 80 in dark, so white text reads on it. A bright brand
therefore comes out deeper as primary. That's correct, and it's what
Material Theme Builder and Android's dynamic colour do too. Seeded with
the kit's own `#6750A4`, the builder lands on the kit's 62 role colours,
59 of them within 1/255, which is how you know the maths is right.

## The screen

A phone is `.m3-device`: 412 × 917 dp, Figma's Android Compact frame, in
the kit's 8 dp bezel with 28 dp screen corners. On a real phone (under
460 px wide) the frame drops away and the screen fills it. Inside, top to
bottom:

```html
<div class="m3-device">
  <div class="m3-statusbar"><span>9:30</span><span class="m3-statusbar__icons">…</span></div>
  <header class="m3-topappbar">…</header>
  <main class="m3-body">…</main>          <!-- scrolls -->
  <button class="m3-fab m3-fab--anchored" aria-label="New recipe">…</button>
  <nav class="m3-navbar">…</nav>
  <div class="m3-gesturebar"></div>
</div>
```

`android-example.html` has every piece in context. Copy from it rather
than writing markup from memory.

## The measurements

- **Status bar** 52 dp, time in Roboto Medium 14/20, a 24 dp camera cutout 18 dp down. **Gesture bar** 24 dp with a 108 × 4 handle; under a nav bar it takes the nav bar's colour.
- **Top app bar**, small: 64 dp, 48 dp icon buttons 4 dp from the edges, the title in title-large (22/28) starting at 56 dp after a leading button, 16 without one. Leading icon in on-surface, trailing in on-surface-variant. When content scrolls under it, it and the status bar turn surface-container (`data-scrolled="1"` on the device). `--center` centres the title on the bar.
- **Medium flexible** app bar 112 dp, title in headline-medium at 500 on its own line, 16 dp in, 12 above the bottom. **Large** 120 dp, display-small at 500.
- **Nav bar** 64 dp on surface-container: a 56 × 32 indicator with 16 dp corners, 6 dp from the top, a 24 dp icon, label-medium 4 dp below. The active destination: secondary-container indicator, on-secondary-container icon in its *filled* glyph, secondary label. Three to five destinations. **Nav rail** 96 dp wide, for tablets and landscape.
- **Buttons** 40 dp tall in a 48 dp target, fully round, 16 dp padding, label-large, a 20 dp icon 8 dp from the label. Filled (primary) is the default; `--tonal` (secondary-container), `--outlined` (1 dp outline-variant), `--elevated` (surface-container-low, level 1), `--text` (primary, 12 dp padding). `--medium` is 56 dp with title-medium. Labels in sentence case: "Try again", not "Try Again".
- **FAB** 56 dp, primary-container, 16 dp corners, level 3; medium 80 dp (20), large 96 dp (28). `--anchored` puts it 16 dp from the right and 16 dp above the nav bar.
- **Icon buttons** a 40 dp container in a 48 dp target, 24 dp icon: standard, `--filled`, `--tonal`, `--outlined`, `--square` (12 dp corners).
- **Chips** 32 dp, 8 dp corners, 1 dp outline-variant border, 16 dp padding; selected filter chips fill with secondary-container and lead with an 18 dp check. A row: 8 dp padding, 4 dp apart.
- **Cards** 12 dp corners: `--elevated` (surface-container-low, level 1), `--filled` (surface-container-highest), `--outlined`. **Media tiles**: a 16 dp-cornered image, title-small, body-small.
- **Lists** one line 56 dp, two 72, three 88, 16 dp padding and gaps. Headline body-large, supporting text body-medium in on-surface-variant, trailing text label-small. Leading 24 dp icon, 40 dp avatar, or 56 dp image with 16 dp corners.
- **Search bar** 56 dp, fully round, surface-container-high. **Text fields** 56 dp: filled (4 dp top corners, surface-container-highest, a 1 dp indicator that turns 3 dp primary on focus) or `--outlined`; the label sits in body-large and rises to body-small.
- **Switch** 52 × 32; off is a 16 dp outline-coloured handle on surface-container-highest with a 2 dp outline, on is a 24 dp on-primary handle on primary. **Checkbox** 18 dp, 2 dp corners; **radio** 20 dp; both in 48 dp targets.
- **Dialog** 312 dp wide, 28 dp corners, surface-container-high, 24 dp padding, headline-small title, body-medium text in on-surface-variant, text buttons at the end. **Bottom sheet** surface-container-low, 28 dp top corners, a 32 × 4 drag handle. **Scrim** black at 32%.
- **Menu** surface-container-low, 16 dp corners, level 3, 48 dp items with 20 dp icons. **Snackbar** inverse-surface, 4 dp corners, 48 dp, action in inverse-primary. **Tabs** 48 dp, title-small, a 3 dp primary indicator under the selected label. **Linear progress** 4 dp, a 4 dp gap and a stop dot.

State layers, the focus ring (3 dp of secondary, 2 dp out), disabled
colours, badges and the motion curves aren't drawn in the kit; those
come from the Material 3 spec and the stylesheet says so where it sets
them.

## Rules that make it read as Android

1. **Never write a hex into a component.** Use the roles (`var(--md-sys-color-primary)`, `--md-sys-color-surface-container`…). Change the seed and regenerate `theme.css` instead. A hand-tuned colour stops matching its dark twin.
2. **Surfaces are tones, not shadows.** Elevation in Material 3 is mostly the surface-container ladder (lowest → highest). Only the FAB, menus, elevated cards and buttons carry shadows.
3. **Icons are Material Symbols, named.** `python3 icon.py home` prints one; `--fill` for an active nav destination. Every `<svg>` carries `data-icon="home"`, the name an engineer types into Compose or the symbols font. Never SF Symbols, never emoji.
4. **Type comes from the 15 styles.** `font: var(--m3-type-body-large); letter-spacing: var(--m3-track-body-large);`. Nothing under label-small's 11 sp.
5. **Touch targets are 48 dp.** The recipes already extend the 40 dp button and 32 dp chip to 48; keep that when composing your own.
6. **No Apple chrome.** No tab bar with a translucent blur, no large-title navigation bar, no grouped inset lists, no capsule-only buttons with chevrons. An Android version of an iOS design keeps the structure and swaps the chrome. design-workflow's `check_design.py` fails a page that mixes them.

## Checking it

```bash
python3 verify_android_ui.py      # from this folder; -v prints every check
```

It drives Chromium over `android-example.html` in light and dark and
reads what the layout engine produced: the phone and its bars, every
component's size, padding, corners, type and shadow, every colour role,
text contrast, the Roboto load, the icons' glyphs, and whether a brand
theme from `build_m3_theme.py` reaches every component, in 268 checks.
The expected numbers are written into the verifier, not read back from
the stylesheet, so a recipe that drifts from the kit fails.

For Jetpack Compose code, `python3 check_compose.py <files or folders>`
reports what the code alone decides, as violations, guidance and API
issues, each linked to the Material page; `--json` for a machine. The
plugin runs it after every `.kt` edit.

For a design, design-workflow's `check_design.py` treats a page that links
`material-components.css` as Android: Roboto, a top app bar, Material
Symbols names, the 48 dp target floor, the 11 sp text floor and the
theme's contrast, light and dark.

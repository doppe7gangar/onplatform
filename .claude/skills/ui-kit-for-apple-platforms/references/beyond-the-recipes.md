# Anything the recipes don't cover

_Part of ui-kit-for-apple-platforms. File paths are relative to the skill's folder, one level up._


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

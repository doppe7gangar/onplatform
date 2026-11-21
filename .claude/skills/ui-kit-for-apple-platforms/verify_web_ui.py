#!/usr/bin/env python3
"""Assert the web components render the values they claim to.

A screenshot is not a test. The type scale was silently dropping to the
browser default 16px while the page still looked broadly like iOS,
because `font: var(--ios-text-body)` was a shorthand with no family and
browsers discard the whole declaration -- invisible by eye, obvious the
moment anything reads getComputedStyle.

So this drives a real browser over the reference page and checks the
numbers: that every token resolves, that the type scale lands on the
values Apple's typography page states, that the switch geometry and its state changes
match what was measured off the kit, that hit targets clear 44px, that
the grouped background pairing is the right way round, and that the
colour pairs the recipes put together actually meet the contrast ratios
Apple's own table requires.

    python3 scripts/verify_web_ui.py           # from the repo
    python3 verify_web_ui.py                   # from inside the skill
    python3 verify_web_ui.py -v                # print every check
"""

import argparse
import os
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("needs playwright:\n"
             "  pip install playwright && playwright install chromium")

HERE = os.path.dirname(os.path.abspath(__file__))

# Runs from two places. In the repo it sits in scripts/ and the skill is
# under .claude/skills/; installed, it sits inside the skill itself with
# example.html as a sibling. hig-guide ships check_swiftui.py the same
# way, and a checker that only works from the repo is a checker nobody
# installing the skill can run.
if os.path.exists(os.path.join(HERE, "example.html")):
    SKILL = HERE
else:
    SKILL = os.path.join(os.path.dirname(HERE), ".claude", "skills",
                         "ui-kit-for-apple-platforms")
PAGE = "file://" + os.path.join(SKILL, "example.html")

# Where Chromium lives varies by machine. Playwright finds its own copy
# after `playwright install chromium`, which is the normal case; this
# only overrides that when a specific binary is pointed at, so the script
# runs unchanged on a laptop and in a container that ships its own.
CHROME = os.environ.get("CHROME_PATH") or None
if CHROME is None:
    _bundled = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
    CHROME = _bundled if os.path.exists(_bundled) else None

# Dynamic Type at the Large (default) setting, from Apple's typography page. These are
# the whole point of the type tokens, so they are checked to the pixel.
TYPE_SCALE = {
    "--ios-text-large-title": (34, 41),
    "--ios-text-title1": (28, 34),
    "--ios-text-title2": (22, 28),
    "--ios-text-title3": (20, 25),
    "--ios-text-headline": (17, 22),
    "--ios-text-body": (17, 22),
    "--ios-text-callout": (16, 21),
    "--ios-text-subhead": (15, 20),
    "--ios-text-footnote": (13, 18),
    "--ios-text-caption1": (12, 16),
    "--ios-text-caption2": (11, 13),
}

COLOUR_TOKENS = [
    "--ios-label", "--ios-label-secondary", "--ios-label-tertiary",
    "--ios-accent", "--ios-red", "--ios-green",
    "--ios-fill-control", "--ios-fill-track", "--ios-surface",
    "--ios-bg", "--ios-bg-card", "--ios-separator",
]


class Checks:
    def __init__(self, verbose):
        self.fails = []
        self.n = 0
        self.verbose = verbose

    def __call__(self, ok, label, detail=""):
        self.n += 1
        if ok:
            if self.verbose:
                print(f"  ok    {label}  {detail}")
        else:
            print(f"  FAIL  {label}  {detail}")
            self.fails.append(label)


def srgb_lum(rgb):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    a, b = srgb_lum(fg), srgb_lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def run(pw, scheme, c, contrast_more=False):
    launch = {"args": ["--no-sandbox"]}
    if CHROME:
        launch["executable_path"] = CHROME
    b = pw.chromium.launch(**launch)
    pg = b.new_page(viewport={"width": 430, "height": 932},
                    color_scheme=scheme,
                    contrast="more" if contrast_more else "no-preference")
    pg.goto(PAGE)
    # A fixed 200ms is a race, not a wait: one run in several asserted
    # against the fallback face because the woff2 had not arrived yet,
    # and a check that fails at random teaches people to re-run it rather
    # than read it. document.fonts.ready resolves when the faces the page
    # actually uses have loaded.
    pg.wait_for_function("() => document.fonts.status === 'loaded'",
                         timeout=10000)
    pg.wait_for_timeout(120)
    print(f"\n== {scheme}{' + prefers-contrast:more' if contrast_more else ''} ==")

    # 1. every token resolves to something
    vals = pg.evaluate(
        "toks => { const s = getComputedStyle(document.documentElement);"
        " return Object.fromEntries(toks.map(t => [t, s.getPropertyValue(t).trim()])); }",
        COLOUR_TOKENS)
    for t, v in vals.items():
        c(bool(v), f"token {t} resolves", v)

    # 2. type scale, to the pixel
    for tok, (size, leading) in TYPE_SCALE.items():
        got = pg.evaluate(
            """tok => { const e = document.createElement('span');
                 e.style.font = getComputedStyle(document.documentElement)
                   .getPropertyValue(tok);
                 e.textContent = 'x'; document.body.appendChild(e);
                 const cs = getComputedStyle(e);
                 const r = [cs.fontSize, cs.lineHeight]; e.remove(); return r; }""",
            tok)
        c(got[0] == f"{size}px", f"{tok} size", f"{got[0]} want {size}px")
        c(got[1] == f"{leading}px", f"{tok} leading", f"{got[1]} want {leading}px")

    # 3. hit targets: every interactive control clears 44px
    small = pg.evaluate(
        """() => [...document.querySelectorAll(
             'button, input:not([type=checkbox]):not([type=radio]), .ios-switch')]
           .map(e => ({t: e.className || e.tagName,
                       h: Math.round(e.getBoundingClientRect().height),
                       w: Math.round(e.getBoundingClientRect().width)}))
           .filter(x => x.h > 0 && x.h < 44)""")
    # The switch is 28pt by Apple's own design; its row supplies the target.
    unexpected = [s for s in small if "ios-switch" not in str(s["t"])]
    c(not unexpected, "controls >= 44px tall", str(unexpected or "all pass"))

    # 4. switch geometry and state, against what was measured off the kit
    sw = pg.evaluate(
        """() => { const on = document.querySelector('.ios-switch input:checked');
             const off = [...document.querySelectorAll('.ios-switch input')]
               .find(i => !i.checked && !i.disabled);
             const dis = document.querySelector('.ios-switch input:disabled');
             const tr = i => i.nextElementSibling;
             const cs = e => getComputedStyle(e);
             const box = document.querySelector('.ios-switch').getBoundingClientRect();
             return {w: Math.round(box.width), h: Math.round(box.height),
                     radius: cs(tr(on)).borderTopLeftRadius,
                     onBg: cs(tr(on)).backgroundColor,
                     offBg: cs(tr(off)).backgroundColor,
                     disOpacity: cs(tr(dis)).opacity,
                     knobOn: cs(tr(on), '::after').transform}; }""")
    c(sw["w"] == 64, "switch width 64", str(sw["w"]))
    c(sw["h"] == 28, "switch height 28", str(sw["h"]))
    c(sw["onBg"] != sw["offBg"], "switch on/off differ",
      f"{sw['onBg']} vs {sw['offBg']}")
    c(float(sw["disOpacity"]) < 1, "switch disabled fades", sw["disOpacity"])

    # The knob is a 38x24 pill in Apple's renderings (Toggles/*_Idle_*),
    # so it travels width - knob - 2x2 inset = 22px. A circle knob
    # travelling 36 is the older switch, and this used to assert it.
    knob = pg.evaluate(
        """() => { const t = document.querySelector('.ios-switch input:checked')
                     .nextElementSibling;
             const cs = getComputedStyle(t, '::after'); const m = cs.transform;
             return {w: parseFloat(cs.width), h: parseFloat(cs.height),
                     travel: m === 'none' ? 0 : Math.round(parseFloat(m.split(',')[4]))}; }""")
    c(knob["w"] == 38 and knob["h"] == 24, "switch knob is a 38x24 pill",
      f"{knob['w']}x{knob['h']}")
    c(knob["travel"] == 22, "switch knob travel = 64-38-4 = 22px", str(knob["travel"]))

    # 5. grouped background pairing, and the right way round in light
    bg = vals["--ios-bg"]
    card = vals["--ios-bg-card"]
    c(bg != card, "page and card backgrounds differ", f"{bg} / {card}")
    if scheme == "light":
        c(srgb_lum(parse_rgb(pg, bg)) < srgb_lum(parse_rgb(pg, card)),
          "light: card is lighter than page", f"{bg} < {card}")

    # 6. separators: absent on each list's first row, present on the rest.
    # Checked per list -- flattening every .ios-list__row across the page
    # makes the second list's first row look like a missing separator.
    per_list = pg.evaluate(
        """() => [...document.querySelectorAll('.ios-list')].map(l =>
             [...l.querySelectorAll('.ios-list__row')].map(r => {
               const cs = getComputedStyle(r, '::before');
               return cs.content !== 'none'
                      && cs.backgroundColor !== 'rgba(0, 0, 0, 0)'; }))""")
    c(bool(per_list), "found lists to check", f"{len(per_list)} lists")
    for i, rows in enumerate(per_list):
        c(rows and rows[0] is False, f"list {i}: first row has no separator",
          str(rows[:1]))
        c(all(rows[1:]), f"list {i}: later rows have separators", str(rows[1:]))

    # 7. contrast, against the thresholds in accessibility.md.
    #
    # Apple's own light palette does not clear its own table -- secondary
    # label lands at 3.44:1 on white and the accent at 3.52:1, both under
    # the 4.5:1 required up to 17 pt. That is a property of the measured
    # values, not a bug in the recipes, so at the default contrast setting
    # these are reported and allowed. Under prefers-contrast:more, where
    # the overrides are supposed to fix it, they must pass.
    KNOWN_LIGHT_SHORTFALL = {"secondary on card", "accent text on card"}
    pairs = [
        ("--ios-label", "--ios-bg-card", 4.5, "body label on card"),
        ("--ios-label-secondary", "--ios-bg-card", 4.5, "secondary on card"),
        # Apple aims Increased Contrast at the card, not the page behind
        # it: its published #1E6EF4 is 4.57:1 on white and 4.10:1 on the
        # grouped grey. Card is where list text sits, so that is the pair
        # held to the threshold.
        ("--ios-accent", "--ios-bg-card", 4.5, "accent text on card"),
    ]
    for fg_t, bg_t, need, label in pairs:
        fg = composite(pg, vals[fg_t], vals[bg_t])
        bgc = parse_rgb(pg, vals[bg_t])
        ratio = contrast(fg, bgc)
        excused = (scheme == "light" and not contrast_more
                   and label in KNOWN_LIGHT_SHORTFALL)
        if excused:
            c(ratio >= 3.0, f"contrast {label} (Apple's value, >=3:1)",
              f"{ratio:.2f}:1 -- under 4.5, see prefers-contrast:more")
        else:
            c(ratio >= need, f"contrast {label}",
              f"{ratio:.2f}:1 need {need}:1")

    # white-on-fill for the filled button, which is what people ship most
    fbg = pg.evaluate(
        "()=>getComputedStyle(document.querySelector('.ios-btn--filled')).backgroundColor")
    fcol = pg.evaluate(
        "()=>getComputedStyle(document.querySelector('.ios-btn--filled')).color")
    ratio = contrast(parse_rgb(pg, fcol), parse_rgb(pg, fbg))
    c(ratio >= 3.0, "contrast white on filled button",
      f"{ratio:.2f}:1 need 3:1 (17pt semibold counts as bold)")

    # 7b. a bundled font actually renders.
    #
    # font-family listing a face proves nothing -- an unresolved family
    # falls through silently and the page still looks plausible in
    # whatever the platform substitutes. So measure: the rendered text
    # run has to match one of the faces shipped here and not the
    # platform fallback. That is the system font where -apple-system
    # resolves (SF Pro on a Mac), the bundled Inter elsewhere, or SF Pro
    # when someone has put their own copy next to fonts/sf.css. The kit
    # doesn't ship SF Pro, so it can't be the reference on a Mac; the
    # system font is measured instead, and counts only if it resolved.
    # A Range is used rather than the element box,
    # because these labels are blocks and their box is the container
    # width, not the text.
    font = pg.evaluate(
        """() => { const el = document.querySelector('.hero__label');
             if (!el) return null;
             const cs = getComputedStyle(el);
             const rng = document.createRange(); rng.selectNodeContents(el);
             const real = rng.getBoundingClientRect().width;
             // A probe span rather than canvas measureText: the canvas
             // ignores CSS letter-spacing, so once tracking was applied
             // every width disagreed with the rendered run and the check
             // failed on correct CSS. The span copies the tracking too.
             const m = fam => {
               const s = document.createElement('span');
               s.style.cssText = 'position:absolute;white-space:nowrap;'
                 + 'font-weight:' + cs.fontWeight + ';font-size:' + cs.fontSize
                 + ';letter-spacing:' + cs.letterSpacing
                 + ';font-family:' + fam;
               s.textContent = el.textContent;
               document.body.appendChild(s);
               const w = s.getBoundingClientRect().width; s.remove(); return w;
             };
             return {real, sf: m('"SF Pro"'), inter: m('Inter'),
                     system: m('-apple-system, BlinkMacSystemFont'),
                     unresolved: m('no-such-family'),
                     fallback: m('"DejaVu Sans"')}; }""")
    if font:
        # A face that didn't resolve measures as the browser's default
        # font, so it only counts if it measured as something else.
        faces = {name: width for name, width in (
                     ("the system font", font["system"]),
                     ("SF Pro", font["sf"]), ("Inter", font["inter"]))
                 if abs(width - font["unresolved"]) > 0.5}
        name, width = min(faces.items(), default=("no intended face", 0.0),
                          key=lambda kv: abs(kv[1] - font["real"]))
        c(abs(width - font["real"]) < 1.0,
          "text renders in the system font, Inter or your own SF Pro",
          f"{name} at {font['real']:.1f}px "
          f"(fallback would be {font['fallback']:.1f}px)")
        c(abs(font["real"] - font["fallback"]) > 1.0,
          "rendered text is not the platform fallback",
          f"{font['real']:.1f}px vs {font['fallback']:.1f}px")

    # 9. Apple's iOS 27 design kit, cross-checked. The kit's variables and
    # components, not memory: text black on a plain background and #1A1A1A
    # on glass; the wide 62pt tab bar with 54pt tabs, 10pt semibold labels
    # and a neutral selection capsule; the 62pt status bar with a 17pt
    # clock; monochrome glass controls; a navigation bar with no material
    # until content scrolls under it.
    if not contrast_more:
        kit = {"light": {"--ios-label": "rgb(0, 0, 0)", "--ios-label-vibrant": "rgb(26, 26, 26)",
                         "--ios-bg": "rgb(242, 242, 247)", "--ios-bg-card": "rgb(255, 255, 255)",
                         "--ios-separator": "rgba(0, 0, 0, 0.12)",
                         "--ios-fill-vibrant-tertiary": "rgb(237, 237, 237)",
                         "--ios-accent": "rgb(0, 136, 255)"},
               "dark": {"--ios-label": "rgb(255, 255, 255)", "--ios-label-vibrant": "rgb(245, 245, 245)",
                        "--ios-bg": "rgb(0, 0, 0)", "--ios-bg-card": "rgb(28, 28, 30)",
                        "--ios-separator": "rgba(255, 255, 255, 0.17)",
                        "--ios-fill-vibrant-tertiary": "rgb(18, 18, 18)",
                        "--ios-accent": "rgb(0, 145, 255)"}}[scheme]
        resolved = pg.evaluate(
            """toks => Object.fromEntries(toks.map(t => { const e = document.createElement('span');
                 e.style.color = 'var(' + t + ')'; document.body.appendChild(e);
                 const v = getComputedStyle(e).color; e.remove(); return [t, v]; }))""",
            list(kit))
        for t, want in kit.items():
            c(resolved[t] == want, f"kit: {t} is the iOS 27 kit's value", f"{resolved[t]} want {want}")
        g = pg.evaluate(
            """() => { const cs = (e, p) => getComputedStyle(e, p || null);
                 const bar = document.querySelector('#tabbar');
                 const sel = bar.querySelector('[aria-selected="true"]');
                 const off = bar.querySelector('.ios-tabbar__item:not([aria-selected="true"])');
                 const sb = document.querySelector('.ios-statusbar');
                 const isl = document.querySelector('.ios-statusbar__island');
                 const ctl = document.querySelector('#controls');
                 const nav = document.querySelector('.ios-navbar');
                 return {barH: bar.getBoundingClientRect().height, barM: cs(bar).marginLeft,
                   tabH: sel.getBoundingClientRect().height, tabFont: cs(off).fontSize,
                   tabLh: cs(off).lineHeight, tabW: cs(off).fontWeight, offColor: cs(off).color,
                   selBg: cs(sel).backgroundColor, selColor: cs(sel).color,
                   sbH: sb.getBoundingClientRect().height, sbFont: cs(sb).fontSize, sbW: cs(sb).fontWeight,
                   islW: isl.getBoundingClientRect().width, islH: isl.getBoundingClientRect().height,
                   ctlH: ctl.getBoundingClientRect().height, ctlColor: cs(ctl.querySelector('button')).color,
                   ctlShadow: cs(ctl).boxShadow, navBg: cs(nav).backgroundColor,
                   navEdge: cs(nav, '::before').opacity,
                   title: cs(document.querySelector('.ios-navbar__title')).color,
                   body: cs(document.body).color}; }""")
        c(g["barH"] == 62, "kit: tab bar capsule is 62pt", str(g["barH"]))
        c(g["barM"] == "21px", "kit: tab bar floats 21pt from the sides", g["barM"])
        c(g["tabH"] == 54, "kit: tabs are 54pt", str(g["tabH"]))
        c((g["tabFont"], g["tabLh"], g["tabW"]) == ("10px", "12px", "590"),
          "kit: tab labels are 10/12 semibold", f"{g['tabFont']}/{g['tabLh']} {g['tabW']}")
        c(g["offColor"] == kit["--ios-label-vibrant"], "kit: unselected tabs are the vibrant label, not grey", g["offColor"])
        c(g["selBg"] == kit["--ios-fill-vibrant-tertiary"], "kit: the selected tab sits on the neutral capsule", g["selBg"])
        c(g["selColor"] == kit["--ios-accent"], "kit: the selected tab takes the accent", g["selColor"])
        c(g["sbH"] == 62, "kit: status bar is 62pt", str(g["sbH"]))
        c((g["sbFont"], g["sbW"]) == ("17px", "590"), "kit: status bar time is 17pt semibold",
          f"{g['sbFont']} {g['sbW']}")
        c((round(g["islW"], 2), round(g["islH"], 1)) == (125.33, 36.7), "kit: Dynamic Island at rest is 125.33 x 36.67 (HIG)",
          f"{g['islW']} x {g['islH']}")
        c(g["ctlH"] == 44, "kit: glass controls are 44pt", str(g["ctlH"]))
        c(g["ctlColor"] == kit["--ios-label-vibrant"], "kit: glass controls are monochrome", g["ctlColor"])
        c("0.5px" in g["ctlShadow"], "kit: glass controls carry the 0.5pt rim", g["ctlShadow"][:60])
        c(g["navBg"] == "rgba(0, 0, 0, 0)" and float(g["navEdge"]) == 0,
          "kit: the navigation bar has no material at rest", f"{g['navBg']} edge {g['navEdge']}")
        c(g["title"] == kit["--ios-label-vibrant"], "kit: the bar title is the vibrant label", g["title"])
        c(g["body"] == kit["--ios-label"], "kit: body text is the plain label", g["body"])
        pg.evaluate("() => document.querySelector('.ios-navbar').classList.add('is-scrolled')")
        pg.wait_for_timeout(260)
        edge = pg.evaluate("() => getComputedStyle(document.querySelector('.ios-navbar'), '::before').opacity")
        c(float(edge) > .9, "kit: scrolled content brings in the scroll edge effect", edge)
        pg.evaluate("() => document.querySelector('.ios-navbar').classList.remove('is-scrolled')")

    # 8. no horizontal overflow at a phone width
    c(pg.evaluate("()=>document.documentElement.scrollWidth") <= 430,
      "no horizontal overflow at 430px")

    b.close()


def parse_rgb(pg, css):
    """Resolve any CSS colour to an (r,g,b) tuple via the browser."""
    return tuple(pg.evaluate(
        """v => { const d = document.createElement('div');
             d.style.color = v; document.body.appendChild(d);
             const c = getComputedStyle(d).color; d.remove();
             return c.match(/[\\d.]+/g).slice(0,3).map(Number); }""", css))


def composite(pg, fg_css, bg_css):
    """Flatten a translucent foreground onto its background."""
    m = pg.evaluate(
        """v => { const d = document.createElement('div');
             d.style.color = v; document.body.appendChild(d);
             const c = getComputedStyle(d).color; d.remove();
             return c.match(/[\\d.]+/g).map(Number); }""", fg_css)
    fg, a = m[:3], (m[3] if len(m) > 3 else 1.0)
    bg = parse_rgb(pg, bg_css)
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(PAGE.replace("file://", "")):
        sys.exit(f"reference page missing: {PAGE}")

    c = Checks(args.verbose)
    with sync_playwright() as pw:
        for scheme in ("light", "dark"):
            run(pw, scheme, c)
        # The overrides only earn their place if they actually clear 4.5:1.
        run(pw, "light", c, contrast_more=True)

    print(f"\n{c.n - len(c.fails)}/{c.n} checks passed")
    if c.fails:
        print("failed: " + ", ".join(sorted(set(c.fails))))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

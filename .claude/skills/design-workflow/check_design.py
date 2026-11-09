#!/usr/bin/env python3
"""Check a design directory against the things a screenshot cannot show.

The recurring failure in this skill was never ugliness. It was a page
that looked completely fine and was wrong underneath: the theme linked
before the components that overwrite it, so a careful brand palette
rendered in Apple's blue; a font CDN in the head, so it fell back to
Helvetica on a plane; three of four states missing, so the first real
empty list shipped as a blank rectangle. Every one of those survives a
screenshot review, and every one is mechanically detectable.

So this is the design equivalent of doctor.py. Static checks always run.
The browser pass needs playwright and adds the things only a real layout
engine knows -- what --ios-accent actually resolved to, whether anything
overflows at phone width, whether the fonts loaded at all.

    python3 check_design.py ./design
    python3 check_design.py ./design --no-browser

Exit status is the point: nonzero means do not ship it.
"""

import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_theme import contrast, hex_to_rgb  # noqa: E402

# Symbol names are checked against the Mac's own list when sf_symbols.py
# has copied it; the module lives with hig-guide, a sibling skill.
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "hig-guide"))
try:
    import sf_symbols  # noqa: E402
except ImportError:
    sf_symbols = None

APPLE_BLUE = {"#0088ff", "#007aff", "#0a84ff", "#0091ff"}

# Every Material Symbols name, shipped with ui-kit-for-android, a sibling.
_NAMES = os.path.join(os.path.dirname(HERE), "ui-kit-for-android", "icons", "names.txt")
M3_ICON_NAMES = (set(l.strip() for l in open(_NAMES, encoding="utf-8") if l.strip() and not l.startswith("#"))
                 if os.path.exists(_NAMES) else None)

PASS, FAIL, WARN = [], [], []


def ok(msg):
    PASS.append(msg)


def bad(msg):
    FAIL.append(msg)


def warn(msg):
    WARN.append(msg)


# ------------------------------------------------------------- static

def sheets_in_order(html):
    """The href of every stylesheet link, in document order."""
    return re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', html, re.I)


def href_of(tag):
    m = re.search(r'href=["\']([^"\']+)["\']', tag, re.I)
    return m.group(1) if m else ""


def check_link_order(path, html):
    hrefs = [href_of(t) for t in sheets_in_order(html)]
    name = os.path.basename(path)
    theme = [i for i, h in enumerate(hrefs) if h.endswith("theme.css")]
    comp = [i for i, h in enumerate(hrefs) if "components" in h]
    toks = [i for i, h in enumerate(hrefs) if "tokens" in h]

    if not theme:
        bad(f"{name}: links no theme.css. The brand system is not applied; "
            f"whatever palette shows is Apple's.")
        return
    if not comp and not toks:
        warn(f"{name}: links neither the tokens nor the component recipes, "
             f"so nothing here is using the measured values.")
        return
    for group in (comp, toks):
        if group and max(group) > min(theme):
            label = os.path.basename(hrefs[max(group)])
            if label.startswith("material"):
                bad(f"{name}: {label} is linked AFTER theme.css. It defines "
                    f"every --md-sys-color-* role, so it overwrites the "
                    f"brand scheme -- the page renders in the kit's baseline "
                    f"purple and looks fine doing it. Move theme.css last.")
            else:
                bad(f"{name}: {label} is linked AFTER theme.css. It redefines "
                    f"--ios-accent and friends, so it overwrites the brand "
                    f"palette -- the page renders in Apple's blue and looks "
                    f"fine doing it. Move theme.css last.")
            return
    ok(f"{name}: stylesheet order correct (theme.css last)")


def check_offline(path, html):
    name = os.path.basename(path)
    ext = re.findall(r'(?:href|src)=["\'](https?://[^"\']+)["\']', html, re.I)
    ext += re.findall(r'@import\s+url\(["\']?(https?://[^"\')]+)', html, re.I)
    if ext:
        hosts = sorted({re.sub(r"https?://([^/]+).*", r"\1", u) for u in ext})
        bad(f"{name}: loads {len(ext)} remote resource(s) from "
            f"{', '.join(hosts)}. The kit ships the fonts -- vendor them, "
            f"or this renders in Helvetica for anyone offline or behind a "
            f"blocked CDN.")
    else:
        ok(f"{name}: no remote resources, opens offline")


def check_local_refs(path, html):
    name, root = os.path.basename(path), os.path.dirname(path)
    missing = []
    for ref in re.findall(r'(?:href|src)=["\']([^"\':#][^"\']*)["\']', html):
        if ref.startswith(("http", "//", "data:", "mailto:")):
            continue
        if not os.path.exists(os.path.join(root, ref.split("?")[0])):
            missing.append(ref)
    if missing:
        bad(f"{name}: {len(missing)} local reference(s) do not exist on "
            f"disk: {', '.join(missing[:4])}")
    else:
        ok(f"{name}: every local reference resolves")


# A state is present when there is *markup that renders it*, not when
# the word appears somewhere in the file. Checking for the string
# "empty" passed a page whose empty panel had been deleted, because the
# stylesheet still carried `.state--empty` and the switcher still had a
# button labelled Empty. Scaffolding is not content. So: strip <style>
# and <script>, then look for the element or for copy only that state
# would have.
STATE_SIGNS = {
    "loading": r'class="[^"]*(?:state--loading|skel)|aria-busy',
    "empty":   r'class="[^"]*state--empty|no [a-z ]{0,24}yet|nothing (?:here|to show)',
    "error":   r"class=\"[^\"]*state--error|couldn't load|couldn.t load|try again|went wrong",
}


def body_of(html):
    """The markup, minus stylesheets and scripts."""
    s = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.S | re.I)
    s = re.sub(r"<script[^>]*>.*?</script>", " ", s, flags=re.S | re.I)
    # The state switcher is scaffolding and names all four states.
    s = re.sub(r'<div class="demo__bar".*?</div>', " ", s, flags=re.S)
    return s


def check_states(path, html):
    name = os.path.basename(path)
    body = body_of(html).lower()
    missing = [label for label, pat in STATE_SIGNS.items()
               if not re.search(pat, body)]
    if missing:
        bad(f"{name}: no markup for the {', '.join(sorted(missing))} state"
            f"{'s' if len(missing) > 1 else ''}. Any screen that loads "
            f"anything has four, and shipping only the happy path is the "
            f"single commonest gap in real builds. references/screens.md "
            f"has the shapes.")
    else:
        ok(f"{name}: populated, loading, empty and error all present")


def check_m3_theme(root, css):
    """A Material 3 theme: every role in both appearances, and the text
    roles readable on what they sit on."""
    def block(text):
        return dict(re.findall(r"--md-sys-color-([a-z-]+):\s*(#[0-9A-Fa-f]{6})", text))
    light = block(css.split("@media")[0])
    dark_m = re.search(r":root\[data-theme=\"dark\"\]\s*\{(.*?)\}", css, re.S)
    dark = block(dark_m.group(1)) if dark_m else {}
    need = ("primary", "on-primary", "primary-container", "secondary-container", "surface",
            "on-surface", "on-surface-variant", "surface-container", "outline-variant")
    missing = [r for r in need if r not in light or r not in dark]
    if missing:
        bad(f"theme.css lacks {', '.join(missing[:4])} in "
            f"{'light or dark' if light else 'light'}. The Material recipes "
            f"read every role, in both appearances; regenerate it with "
            f"ui-kit-for-android/build_m3_theme.py rather than writing it by hand.")
        return css
    ok(f"theme.css carries {len(light)} Material colour roles, light and dark")
    for mode, roles in (("light", light), ("dark", dark)):
        for fg, bg in (("on-primary", "primary"), ("on-surface", "surface"),
                       ("on-surface-variant", "surface-container")):
            r = contrast(hex_to_rgb(roles[fg]), hex_to_rgb(roles[bg]))
            if r < 4.5:
                bad(f"theme.css {mode}: {fg} on {bg} is {r:.2f}:1, under 4.5:1.")
    return css


def check_theme(root):
    p = os.path.join(root, "theme.css")
    if not os.path.exists(p):
        bad("no theme.css. Generate one: build_theme.py '#RRGGBB' --name x "
            "(or, for Android, ui-kit-for-android/build_m3_theme.py '#RRGGBB' -o theme.css)")
        return None
    css = open(p, encoding="utf-8").read()
    if "--md-sys-color-" in css and "--ios-" not in css:
        return check_m3_theme(root, css)

    bridge = re.findall(r"--ios-([a-z0-9-]+):\s*var\(--([a-z0-9-]+)-", css)
    if not bridge:
        bad("theme.css has no --ios-* bridge. The component recipes read "
            "--ios-accent, so without it you get a brand palette and "
            "Apple-blue buttons -- a system that looks right until you "
            "place a component. Regenerate rather than hand-edit.")
    else:
        names = sorted({b[0] for b in bridge})
        ok(f"theme.css bridges {len(names)} --ios-* names ({', '.join(names[:4])}...)")

    m = re.search(r"--[a-z0-9-]+-accent:\s*(#[0-9A-Fa-f]{6})", css)
    if not m:
        warn("theme.css defines no *-accent; cannot check contrast")
        return css
    accent = m.group(1)
    if accent.lower() in APPLE_BLUE:
        warn(f"the accent is {accent}, which is Apple's own. Fine for an "
             f"iOS-looking demo, wrong for a client with a brand.")

    on = re.search(r"--[a-z0-9-]+-on-accent:\s*(#[0-9A-Fa-f]{6})", css)
    if on:
        r = contrast(hex_to_rgb(on.group(1)), hex_to_rgb(accent))
        if r < 3.0:
            bad(f"label on the accent fill is {r:.2f}:1, under the 3:1 "
                f"Apple allows even at bold.")
        else:
            ok(f"label on accent fill {r:.2f}:1 (3:1 needed at semibold)")

    txt = re.search(r"--[a-z0-9-]+-accent-text:\s*(#[0-9A-Fa-f]{6})", css)
    if txt:
        r = contrast(hex_to_rgb(txt.group(1)), (255, 255, 255))
        if r < 4.5:
            warn(f"accent-text is {r:.2f}:1 on white, under 4.5:1 -- the "
                 f"brand hue may not reach it by lightness alone. Use it "
                 f"as a fill behind white, not as coloured text.")
        else:
            ok(f"accent-text {r:.2f}:1 on white (4.5:1 needed to 17pt)")
    return css


def project_css(path, html):
    """The page's own CSS: inline, attribute, and its local stylesheets.

    Reading only <style> left a hole wide enough to drive a project
    through -- put the CSS in app.css, as most real ones do, and every
    hard-coded colour and every overridden token went unseen. theme.css
    and vendor/ are excluded: those are generated and measured
    respectively, and neither is the page's own work.
    """
    root = os.path.dirname(path)
    css = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))
    css += " " + " ".join(re.findall(r'style=["\']([^"\']+)["\']', html))
    for href in re.findall(r'<link[^>]+href=["\']([^"\']+\.css)["\']', html, re.I):
        if href.startswith(("http", "//")) or href.endswith("theme.css"):
            continue
        if "vendor/" in href or "ios-tokens" in href or "ios-components" in href:
            continue
        f = os.path.join(root, href.split("?")[0])
        if os.path.exists(f):
            css += " " + open(f, encoding="utf-8", errors="replace").read()
    # Strip comments. A file that documents its palette in its own header
    # -- which the good ones do, with the contrast numbers -- otherwise
    # gets every value in that header counted against it, and the check
    # ends up scolding the file for being well documented.
    return re.sub(r"/\*.*?\*/", " ", css, flags=re.S)


def check_token_overrides(path, html):
    """A page redefining --ios-* by hand has stepped around the theme."""
    name = os.path.basename(path)
    hits = sorted(set(re.findall(r"(--(?:ios|md-sys-color)-[a-z0-9-]+)\s*:\s*(?!var\()[^;}]+",
                                 project_css(path, html))))
    if hits:
        bad(f"{name}: redefines {len(hits)} system token(s) with literal "
            f"values ({', '.join(hits[:4])}). That is the theme being "
            f"worked around rather than used -- the value stops following "
            f"dark mode and stops following the brand. Change the brand "
            f"colour and regenerate instead.")
    else:
        ok(f"{name}: does not override the system tokens by hand")


# Components the kit measures that carry the platform's shape. A design
# can skip the switch or the segmented control and still look native; an
# Apple-platform design with none of these has rebuilt the system from
# scratch rather than used it.
STRUCTURAL = ("ios-list", "ios-navbar", "ios-tabbar")

# iOS and iPadOS here; a Mac design is held to the Mac recipes instead
# (MAC_STRUCTURAL), since demanding the iOS grouped list of a Mac app
# would be worse advice than none.
TOUCH_PLATFORM = re.compile(r"\b(ios|iphone|ipad|ipados)\b", re.I)


def kit_classes(path, html):
    """Component families the linked ios- and macos-components.css define."""
    root, families = os.path.dirname(path), set()
    for href in re.findall(r'<link[^>]+href=["\']([^"\']*(?:ios|ipados|macos|material)-components\.css)["\']',
                           html, re.I):
        f = os.path.join(root, href.split("?")[0])
        if os.path.exists(f):
            css = open(f, encoding="utf-8", errors="replace").read()
            families |= {c.split("--")[0]
                         for c in re.findall(r"^\.([a-z][\w-]*)", css, re.M)}
    return families


# The Mac recipes that carry a Mac window's shape, and the iPhone chrome
# that has no place in one.
MAC_STRUCTURAL = ("mac-window", "mac-toolbar")
IPHONE_CHROME = ("ios-tabbar", "ios-navbar", "ios-statusbar")


# An Android screen carries a top app bar; and none of Apple's chrome.
M3_STRUCTURAL = ("m3-topappbar",)
APPLE_CHROME = IPHONE_CHROME + ("mac-window", "mac-toolbar", "mac-sidebar", "ios-list")


# An iPad screen has a sidebar or tabs at the top -- never the iPhone's
# bottom tab bar.
IPAD_STRUCTURAL = ("ipad-sidebar", "ipad-tabbar")


def is_ipad(path, html):
    """An iPad design: it links the iPad recipes, or DESIGN.md says iPadOS."""
    if re.search(r'href=["\'][^"\']*ipados-components\.css', html, re.I):
        return True
    d = os.path.join(os.path.dirname(path), "DESIGN.md")
    if os.path.exists(d):
        m = re.search(r"^## Platform mode\s+`?([\w-]+)`?", open(d, encoding="utf-8").read(), re.M)
        if m and m.group(1).lower() in ("ipados", "ipad"):
            return True
    return False


def is_android(path, html):
    """An Android design: it links the Material recipes, or DESIGN.md says Android."""
    if re.search(r'href=["\'][^"\']*material-components\.css', html, re.I):
        return True
    plat = target_platform(path) or ""
    d = os.path.join(os.path.dirname(path), "DESIGN.md")
    mode = ""
    if os.path.exists(d):
        m = re.search(r"^## Platform mode\s+`?([\w-]+)`?", open(d, encoding="utf-8").read(), re.M)
        mode = m.group(1) if m else ""
    return bool(re.search(r"\bandroid\b", plat, re.I)) or mode.lower() == "android"


def is_mac(path, html):
    """A Mac design: it links the Mac recipes, or DESIGN.md says macOS."""
    if re.search(r'href=["\'][^"\']*macos-components\.css', html, re.I):
        return True
    plat = target_platform(path) or ""
    d = os.path.join(os.path.dirname(path), "DESIGN.md")
    mode = ""
    if os.path.exists(d):
        m = re.search(r"^## Platform mode\s+`?([\w-]+)`?", open(d, encoding="utf-8").read(), re.M)
        mode = m.group(1) if m else ""
    return bool(re.search(r"\bmac(os)?\b", plat, re.I)) or mode.lower() == "macos"


def target_platform(path):
    d = os.path.join(os.path.dirname(path), "DESIGN.md")
    if not os.path.exists(d):
        return None
    # The value after the colon, up to the first sentence break. The
    # whole line would include clauses like "Not a web app wearing iOS
    # chrome", and matching "web" inside a sentence that denies it is how
    # an iOS design escaped this check.
    m = re.search(r"^[-*\s]*\**Target platform\(?s?\)?:?\**:?\s*(.+)$",
                  open(d, encoding="utf-8").read(), re.M | re.I)
    if not m:
        return None
    return re.split(r"(?<=[a-z])\.\s|\s[—-]\s", m.group(1))[0].strip()


def check_uses_kit(path, html):
    """Linking the measured components is not the same as using them.

    Every run so far vendored the kit, linked it in the right order, kept
    the bridge alive, passed contrast -- and then hand-rolled its own
    list, navigation bar and tab bar. The scaffold ships eighteen
    ios-list rows; the finished designs had none, three times out of
    three. Order, bridge, contrast and states all stay true while you
    rebuild the system from scratch, so nothing here could see it, and
    the result reads as an approximation of iOS rather than iOS.
    """
    name = os.path.basename(path)
    families = kit_classes(path, html)
    if not families:
        return
    used = {c for c in families
            if re.search(r'class="[^"]*\b' + re.escape(c) + r'\b', html)}
    if not used:
        bad(f"{name}: links ios-components.css and uses none of its "
            f"{len(families)} component recipes. The measured values were "
            f"vendored and then bypassed -- either use them or stop "
            f"shipping the stylesheet.")
        return

    if is_ipad(path, html):
        if re.search(r'class="[^"]*\bios-tabbar\b', html):
            bad(f"{name}: an iPad design with the iPhone's bottom tab bar. iPadOS puts "
                f"tabs at the top centre (.ipad-tabbar) or a sidebar beside the content "
                f"(.ipad-sidebar); at the bottom it reads as a stretched iPhone app.")
            return
        mac = [c for c in ("mac-window", "mac-toolbar") if re.search(r'class="[^"]*\b' + c + r'\b', html)]
        if mac:
            bad(f"{name}: an iPad design using Mac chrome ({', '.join(mac)}).")
            return
        if not any(c in used for c in IPAD_STRUCTURAL):
            bad(f"{name}: an iPad design with neither a sidebar nor tabs at the top. "
                f"The 320pt glass sidebar or the top tab bar is what makes it read as "
                f"an iPad app rather than a big iPhone; ipados-components.css has both.")
            return
        ok(f"{name}: an iPad layout built from {len(used)} of the kit's measured components")
        return

    if is_android(path, html):
        chrome = [c for c in APPLE_CHROME
                  if re.search(r'class="[^"]*\b' + re.escape(c) + r'\b', html)]
        if chrome:
            bad(f"{name}: an Android design using Apple chrome ({', '.join(chrome)}). "
                f"Android has a top app bar, a nav bar and Material lists; "
                f"material-components.css has the measured ones.")
            return
        missing = [c for c in M3_STRUCTURAL if c in families and c not in used]
        if missing:
            bad(f"{name}: an Android design without {', '.join(missing)}. The 64 dp "
                f"bar with its 48 dp icon buttons and title-large title is the "
                f"first thing that reads as Android; hand-built, it reads as a "
                f"web page.")
            return
        ok(f"{name}: an Android screen built from {len(used)} of the kit's measured components")
        return

    if is_mac(path, html):
        chrome = [c for c in IPHONE_CHROME
                  if re.search(r'class="[^"]*\b' + re.escape(c) + r'\b', html)]
        if chrome:
            bad(f"{name}: a Mac design using iPhone chrome ({', '.join(chrome)}). A Mac "
                f"window has a sidebar and a toolbar, not a tab bar, a navigation "
                f"bar or a status bar; macos-components.css has the measured ones.")
            return
        missing = [c for c in MAC_STRUCTURAL if c in families and c not in used]
        if missing:
            bad(f"{name}: a Mac design without {', '.join(missing)}. The window, its "
                f"16pt corners, the traffic lights and the 52pt toolbar band with "
                f"its glass controls are what make it read as a Mac app; "
                f"hand-built, it reads as a web page with a title bar.")
            return
        ok(f"{name}: a Mac window built from {len(used)} of the kit's measured components")
        return

    plat = target_platform(path)
    if plat and TOUCH_PLATFORM.search(plat):
        missing = [c for c in STRUCTURAL if c in families and c not in used]
        if len(missing) == len(STRUCTURAL):
            bad(f"{name}: targets an Apple platform ({plat.strip()[:48]}) "
                f"and uses none of {', '.join(STRUCTURAL)}. Those carry the "
                f"grouped-list metrics, the bar heights and the tracking "
                f"this corpus measured; hand-rolling them is what makes a "
                f"design read as almost-iOS.")
            return
    ok(f"{name}: uses {len(used)} of the kit's measured components")


# The parts a content-first iPhone screen is made of (ios-components.css,
# "Content first"), and the plain image or chart a design may draw itself.
CONTENT_PARTS = ("ios-hero", "ios-headerhero", "ios-card", "ios-tile", "ios-ring",
                 "ios-bars", "ios-art", "ios-carousel", "ios-stats", "ios-metric",
                 "ios-progress", "mac-hero", "mac-card", "mac-tile", "mac-ring",
                 "mac-bars", "mac-art", "mac-stats", "mac-metric")
_CONTENT = re.compile(r'class="[^"]*\b(?:' + "|".join(CONTENT_PARTS) + r')\b'
                      r'|<img\b[^>]*\bsrc="[^"]+"|<picture\b|<canvas\b|<video\b'
                      r'|<svg\b[^>]*\brole="img"')


def check_content_first(path, html):
    """An iPhone app built from grouped lists alone reads as Settings.

    It is the most common way a design here came out correct and still
    bad: measured chrome, real data, every check green, and every screen
    a grey page of white rows. Apple's own apps open on the content --
    Health on its figures, Fitness on rings, Weather on the sky, Home on
    a picture of the room -- and keep lists for the long tail. A design
    with no content part anywhere fails; one whose first screen has none
    is warned, since a mail or notes app can rightly open on a list.
    """
    name = os.path.basename(path)
    mac = is_mac(path, html)
    if not (re.search(r'class="[^"]*\bios-statusbar\b', html) or is_ipad(path, html) or mac):
        return
    body = body_of(html)
    if mac and not _CONTENT.search(body):
        # Finder, Mail and Notes are rightly tables and lists; a Mac app
        # that is about its content still wants to open on it.
        warn(f"{name}: the window is tables and lists alone. If the app is about its "
             f"content rather than managing files, open on it the way Music and Weather "
             f"do: macos-components.css \"Content first\" has the parts at Mac sizes.")
        return
    if not _CONTENT.search(body):
        bad(f"{name}: every screen is lists -- no hero, card, figure, chart, tile or "
            f"picture anywhere -- so it reads as a Settings pane, not an app. Open "
            f"the main screen on what the person came for, the way Health, Fitness "
            f"and Weather do: ios-components.css \"Content first\" has the parts and "
            f"ios-screens.html (#summary, #detail, #browse) shows them composed.")
        return
    marks = [m.start() for m in re.finditer(r'data-screen-id="', body)]
    first = body[marks[0]:marks[1]] if len(marks) > 1 else body
    first = re.split(r'class="state state--loading"', first)[0]
    if not _CONTENT.search(first):
        warn(f"{name}: the first screen is lists alone. Unless the product really is "
             f"a list (mail, notes), open it on a hero, a figure or a chart "
             f"(ios-components.css \"Content first\") and keep the list below it.")
        return
    ok(f"{name}: opens on content, not on a list")


def check_prototype_data(path, html):
    """Rows that open a detail open their own record, and the records exist.

    A list pushes one detail screen; with nothing to tell the rows apart
    every row opened the same plant, which is the second thing a reviewer
    taps. prototype.js fills the screen from data-item; this holds the
    references to the data block and points at rows that have none.
    """
    import json
    name = os.path.basename(path)
    m = re.search(r'<script[^>]*\bid="prototype-data"[^>]*>(.*?)</script>', html, re.S)
    data = None
    if m:
        try:
            data = json.loads(m.group(1))
        except ValueError as e:
            bad(f"{name}: the prototype-data block is not valid JSON ({str(e)[:60]}); "
                f"no row can open its own record.")
            return
    missing = []
    for ref in re.findall(r'\bdata-item="([^"{][^"]*)"', html):
        node = data
        for k in ref.strip().split("."):
            node = node.get(k) if isinstance(node, dict) else None
        if node is None:
            missing.append(ref)
    if missing:
        bad(f"{name}: {len(missing)} data-item reference(s) name a record that isn't in "
            f"prototype-data: {', '.join(sorted(set(missing))[:4])}.")
    pushes = {}
    for tag in re.findall(r"<[a-z][^>]*\bdata-push=\"[^\"]+\"[^>]*>", html):
        target = re.search(r'data-push="([^"]+)"', tag).group(1)
        pushes.setdefault(target, []).append("data-item=" in tag)
    for target, items in pushes.items():
        if len(items) >= 3 and not any(items):
            warn(f"{name}: {len(items)} controls open '{target}' and every one shows the "
                 f"same content. Give each its record -- data-item on the row, data-field "
                 f"in the screen, the records in a prototype-data block (prototype.js) -- "
                 f"so a tapped row opens that row.")
    if data is not None and not missing:
        ok(f"{name}: every data-item names a record in prototype-data")


def check_icons_named(path, html):
    """On Android, icons are Material Symbols, named in data-icon.

    The glyphs ship (Apache 2.0), so unlike SF Symbols the drawing is the
    real one -- but the name is still what an engineer types into
    Icons.Outlined or the symbols font, so it has to exist.
    """
    name = os.path.basename(path)
    body = body_of(html)
    if "data-sf-symbol" in body:
        warn(f"{name}: an Android design naming SF Symbols. Android draws "
             f"Material Symbols; ui-kit-for-android/icon.py prints them.")
    icons = re.findall(r"<svg\b[^>]*>", body)
    named = [re.search(r'data-icon="([^"]+)"', t) for t in icons]
    unnamed = [t for t, m in zip(icons, named) if not m and 'viewBox="0 0 24 24"' in t]
    names = sorted({m.group(1) for m in named if m})
    if M3_ICON_NAMES is not None and names:
        unknown = [n for n in names if n not in M3_ICON_NAMES]
        if unknown:
            warn(f"{name}: {len(unknown)} data-icon name(s) aren't Material "
                 f"Symbols, so an engineer can't find them: {', '.join(unknown[:5])}")
        else:
            ok(f"{name}: all {len(names)} icon names are Material Symbols")
    if unnamed:
        warn(f"{name}: {len(unnamed)} 24 dp icon(s) without data-icon. Name the "
             f"Material Symbol each one is -- icon.py adds it.")


def check_symbols_named(path, html):
    """Icons must say which SF Symbol they stand for.

    SF Symbols cannot ship in a web kit: Apple's licence covers use
    inside apps running on Apple platforms, not extraction into a font or
    reproduction as SVG. So every glyph here is a stand-in, and the thing
    that has to be exact is the *name* -- an engineer reading the markup
    needs Image(systemName: "house.fill"), not a drawing that resembles a
    house. Naming it costs one attribute and turns a mockup into a
    specification.
    """
    name = os.path.basename(path)
    body = body_of(html)

    # A name that doesn't exist is worse than none: it reads as a spec and
    # Image(systemName:) draws nothing. Checked when the Mac's list is here,
    # on every literal name, whatever element carries it.
    db = sf_symbols.load() if sf_symbols else None
    names = sorted(set(n for n in re.findall(r'(?<![\w:.-])data-sf-symbol="([^"]+)"', body)
                       if re.fullmatch(r"[A-Za-z0-9.]+", n)))
    if db and names:
        bad = []
        for n in names:
            status, detail = sf_symbols.lookup(db, n)
            if status == "unknown":
                bad.append(f"{n}" + (f" (did you mean {detail}?)" if detail else ""))
            elif status == "renamed":
                bad.append(f"{n} (renamed {detail})")
        if bad:
            warn(f"{name}: {len(bad)} data-sf-symbol name(s) aren't SF Symbols, so the "
                 f"implementation would draw nothing: " + ", ".join(bad))
        else:
            ok(f"{name}: all {len(names)} SF Symbol names exist")

    slots = re.findall(
        r'<[a-z]+[^>]*class="[^"]*(?:rowicon|ios-tabbar__item|'
        r'ios-navbar__action|mac-sidebar__icon|mac-tool(?![\w-])|mac-menu__icon)'
        r'[^"]*"[^>]*>', body)
    # A Mac toolbar control with a word in it is a button, not an icon slot.
    slots = [t for t in slots if "mac-tool" not in t or
             re.search(re.escape(t) + r"\s*<svg", body)]
    if not slots:
        return
    unnamed = [t for t in slots if "data-sf-symbol" not in t]
    # An SVG nested inside the slot may carry the attribute instead.
    if unnamed:
        for t in list(unnamed):
            m = re.search(re.escape(t) + r"(.{0,400}?)</", body, re.S)
            if m and "data-sf-symbol" in m.group(1):
                unnamed.remove(t)
    if unnamed:
        warn(f"{name}: {len(unnamed)} of {len(slots)} icon slot(s) do not "
             f"name the SF Symbol they stand for. The drawing is a "
             f"placeholder either way; the name is what the "
             f"implementation needs. Add data-sf-symbol=\"house.fill\".")
    else:
        ok(f"{name}: all {len(slots)} icon slots name their SF Symbol")


# Characters standing in for icons: geometric shapes, dingbats, arrows,
# stars, and emoji. The kit's chevrons (‹ ›) are type, not icons.
GLYPH_ICONS = re.compile("[\u2190-\u21ff\u2300-\u23ff\u25a0-\u25ff\u2600-\u27bf"
                         "\u2b00-\u2bff\U0001f000-\U0001faff]")


def check_glyph_icons(path, html):
    """An icon drawn with a character reads as a web page at a glance."""
    name = os.path.basename(path)
    text = re.sub(r"<(script|style)\b.*?</\1>|<!--.*?-->", " ", html, flags=re.S | re.I)
    text = re.sub(r'<div class="demo__bar".*?</div>', " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    found = sorted(set(GLYPH_ICONS.findall(text)))
    if found:
        bad(f"{name}: icons drawn with characters ({' '.join(found[:8])}). Apple's apps "
            f"use SF Symbols, never shapes, stars or emoji typed as text: use an SVG "
            f"with data-sf-symbol, and on a Mac run ui-kit-for-apple-platforms's sf_icons.py.")
    else:
        ok(f"{name}: no icons faked with characters")


def check_hardcoded(path, html):
    """Colours written into the page instead of taken from the system."""
    name = os.path.basename(path)
    styles = project_css(path, html)
    # A hex assigned to a custom property is a token being defined, and
    # a token can be redefined for dark mode and reused everywhere. A hex
    # assigned straight to color/background/border is the thing that
    # cannot follow anything. Only the second kind is a problem.
    #
    # This distinction is not pedantry: a dashboard's chart palette is
    # necessarily its own hues -- Apple's semantic tokens hold no set of
    # mutually distinguishable series colours -- and counting a correctly
    # tokenised, light-and-dark, contrast-checked palette as 30 mistakes
    # is how a warning teaches people to stop reading warnings.
    styles = re.sub(r"--[\w-]+\s*:[^;}]*", " ", styles)
    hexes = {h.lower() for h in re.findall(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b",
                                           styles)}
    hexes -= {"#fff", "#ffffff", "#000", "#000000"}   # on-fill text, legitimately
    if len(hexes) > 3:
        warn(f"{name}: {len(hexes)} hard-coded colours in the page's own CSS "
             f"({', '.join(sorted(hexes)[:5])}). Each one is a value that "
             f"will not follow dark mode or the brand. Use the tokens.")
    elif hexes:
        ok(f"{name}: {len(hexes)} hard-coded colour(s), within reason")
    else:
        ok(f"{name}: no hard-coded colours, all from tokens")


# ------------------------------------------------------------ browser

# Text that floating chrome (a tab bar, a toolbar, a banner, a FAB) still
# paints over once every scroller is at its end. Scrolling under the chrome is
# fine; ending under it is not -- the last rows can never be read. Only
# the lower half of the window is looked at, so content passing under a
# navigation bar at the top is left alone.
COVERED_JS = r"""async () => {
  const scrolls = [document.scrollingElement, ...document.querySelectorAll('*')]
    .filter(e => e && e.scrollHeight > e.clientHeight + 2 &&
      (e === document.scrollingElement || /(auto|scroll)/.test(getComputedStyle(e).overflowY)));
  scrolls.forEach(e => { e.scrollTop = e.scrollHeight; });
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const vh = innerHeight, seen = new Set(), out = [];
  // Whatever the hit is, up to where its branch meets the text's, sits
  // over the text. It only hides it if something on that branch paints:
  // a background or a backdrop blur. A transparent stretched link does not.
  const painter = (hit, el) => {
    let found = null;
    for (let e = hit; e && !e.contains(el); e = e.parentElement) {
      const cs = getComputedStyle(e);
      const m = cs.backgroundColor.match(/rgba?\(([^)]+)\)/);
      const alpha = m ? (m[1].split(',')[3] === undefined ? 1 : +m[1].split(',')[3]) : 0;
      if (alpha >= 0.3 || (cs.backdropFilter && cs.backdropFilter !== 'none')) found = e;
    }
    return found;
  };
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walk.nextNode(); n; n = walk.nextNode()) {
    const t = n.textContent.trim(), el = n.parentElement;
    if (t.length < 2 || !el || seen.has(el)) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || +cs.opacity === 0) continue;
    const range = document.createRange(); range.selectNodeContents(n);
    const r = range.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const x = r.left + r.width / 2, y = r.top + r.height / 2;
    if (y < vh * 0.5 || y > vh - 1 || x < 0 || x > innerWidth) continue;
    let clipped = false;
    for (let a = el.parentElement; a; a = a.parentElement) {
      if (getComputedStyle(a).overflowY === 'visible') continue;
      const ar = a.getBoundingClientRect();
      if (y < ar.top || y > ar.bottom) { clipped = true; break; }
    }
    if (clipped) continue;
    const hit = document.elementFromPoint(x, y);
    if (!hit || el.contains(hit) || hit.contains(el)) continue;
    const cover = painter(hit, el);
    if (!cover) continue;
    seen.add(el);
    out.push({ text: t.slice(0, 40), by: (cover.className && cover.className.baseVal === undefined
      ? '.' + String(cover.className).trim().split(/\s+/)[0] : cover.tagName.toLowerCase()) });
  }
  return out;
}"""


# Every control a reviewer can tap, minus the review tools themselves and
# whatever is marked as deliberately inert. Real navigation (a link to
# another page) and native form fields count as alive on their own.
CONTROLS_JS = r"""() => {
  const sel = 'button, a[href], [role=button], [role=tab], [role=menuitem], [role=switch], ' +
    '[onclick], [data-go], [data-push], [data-back], [data-sheet], [data-dismiss], ' +
    '[data-toggle], [data-toast], .ios-list__row--tappable, .m3-list__item--tappable';
  const real = 'button, a, li, [role], [tabindex], [onclick], .ios-list__row--tappable, .m3-list__item--tappable';
  const all = [...document.querySelectorAll(sel)];
  const out = [];
  all.forEach((el, i) => {
    if (el.closest('.demo__bar, [data-set], [data-screen-set], [data-inert], [disabled], [aria-disabled="true"]')) return;
    // A container that only carries an attribute (a device holding a
    // data-toast flag) is not a control; the controls inside it are.
    if (!el.matches(real) && el.querySelector(sel)) return;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2 || el.offsetParent === null) return;
    const href = el.tagName === 'A' ? el.getAttribute('href') : null;
    if (href && href !== '#' && !href.startsWith('javascript')) return;
    const titled = el.querySelector('[class*="title"], [class*="label"], [class*="headline"]');
    const name = (el.getAttribute('aria-label') || (titled && titled.innerText) || el.innerText || el.getAttribute('data-sf-symbol') ||
      el.getAttribute('data-icon') || el.className || el.tagName).toString().trim().split('\n')[0].slice(0, 32);
    out.push({ i, name });
  });
  const missing = [];
  document.querySelectorAll('[data-go], [data-push]').forEach(el => {
    const id = el.getAttribute('data-go') ?? el.getAttribute('data-push');
    if (!document.querySelector(`[data-screen-id="${id}"]`))
      missing.push(`${(el.innerText || el.getAttribute('aria-label') || id).trim().split('\n')[0].slice(0, 24)} -> ${id}`);
  });
  document.querySelectorAll('[data-sheet]').forEach(el => {
    const id = el.getAttribute('data-sheet');
    if (!document.querySelector(`[data-sheet-id="${id}"]`)) missing.push(`sheet ${id}`);
  });
  return { controls: out, missing: [...new Set(missing)] };
}"""

TAP_JS = r"""async (i) => {
  const sel = 'button, a[href], [role=button], [role=tab], [role=menuitem], [role=switch], ' +
    '[onclick], [data-go], [data-push], [data-back], [data-sheet], [data-dismiss], ' +
    '[data-toggle], [data-toast], .ios-list__row--tappable, .m3-list__item--tappable';
  const el = document.querySelectorAll(sel)[i];
  if (!el) return true;
  let changed = 0;
  const mo = new MutationObserver(list => { changed += list.length; });
  mo.observe(document.documentElement, { subtree: true, attributes: true, childList: true, characterData: true });
  const before = location.href;
  el.click();
  await new Promise(r => setTimeout(r, 350));
  mo.disconnect();
  const after = location.href;
  return changed > 0 || (after !== before && !/#$/.test(after));
}"""


BROWSER_JS = r"""() => {
// Rendered contrast, measured rather than parsed. The CSS can be
// perfect and the page still unreadable -- a token overridden further
// down, a colour inherited onto a surface nobody pictured -- and only
// the layout engine knows what a run of text finally sits on. Anything
// inside an aria-hidden subtree is skipped: it is declared decorative,
// nothing announces it, and holding a monogram in an icon tile to the
// same bar as a paragraph teaches people to silence the check.
const RATIO = (a, b) => {
  const lum = c => { const f = v => (v /= 255) <= 0.03928 ? v / 12.92
        : Math.pow((v + 0.055) / 1.055, 2.4);
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const [x, y] = [lum(a), lum(b)];
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
};

// getComputedStyle does not promise rgb(). Chromium hands back
// `color(srgb 0.96 0.96 0.96)` for anything that went through
// color-mix, and those channels are 0-1. Read as 0-255 a near-white
// footer measures as near-black, which is how a perfectly legible
// marketing page came back with thirty-eight contrast failures.
function parseColor(s) {
  const n = (s.match(/[\d.]+(?:e[-+]?\d+)?/gi) || []).map(Number);
  if (n.length < 3) return null;
  const unit = /^color\(/i.test(s);
  return [n[0] * (unit ? 255 : 1), n[1] * (unit ? 255 : 1),
          n[2] * (unit ? 255 : 1), n.length > 3 ? n[3] : 1];
}

const over = (fg, bg) => [0, 1, 2].map(i => fg[i] * fg[3] + bg[i] * (1 - fg[3]));

// Composite every translucent layer down to the first opaque one.
// Apple's label ladder is one grey at several alphas -- the colours the
// system uses most are all translucent -- so dropping alpha would make
// this check meaningless for exactly the text it most needs to judge.
function surfaceOf(el) {
  const layers = [];
  let base = null;
  for (let n = el; n; n = n.parentElement) {
    const c = parseColor(getComputedStyle(n).backgroundColor);
    if (!c || c[3] === 0) continue;
    if (c[3] >= 0.999) { base = c.slice(0, 3); break; }
    layers.push(c);
  }
  if (!base) {
    for (const el2 of [document.body, document.documentElement]) {
      const c = parseColor(getComputedStyle(el2).backgroundColor);
      if (c && c[3] >= 0.999) { base = c.slice(0, 3); break; }
    }
  }
  // A transparent page borrows the viewer's ground; guessing black here
  // put white text at 1.2:1 against nothing at all.
  if (!base) base = matchMedia('(prefers-color-scheme: dark)').matches
      ? [0, 0, 0] : [255, 255, 255];
  let cur = base;
  for (let i = layers.length - 1; i >= 0; i--) cur = over(layers[i], cur);
  return cur;
}

// Text set on a picture -- a photo, a gradient, art drawn behind it --
// has no background colour to read: the DOM says the surface is the
// page, and white words on a dark hero measured 1.1:1 against grey.
// Those runs are handed back with their box instead, and measured
// against the rendered pixels underneath with the text hidden.
// The box round the words themselves, not the element: a tab's box
// takes in its icon and the glass rim, and the rim's dark edge is not
// what the label is read against.
function textBox(e) {
  let L = Infinity, T = Infinity, R = -Infinity, B = -Infinity;
  for (const n of e.childNodes) {
    if (n.nodeType !== 3 || !n.textContent.trim()) continue;
    const rg = document.createRange(); rg.selectNodeContents(n);
    const r = rg.getBoundingClientRect();
    L = Math.min(L, r.left); T = Math.min(T, r.top); R = Math.max(R, r.right); B = Math.max(B, r.bottom);
  }
  return R > L ? [L, T, R - L, B - T] : null;
}
function pictureUnder(e) {
  const tb = textBox(e);
  if (!tb) return false;
  const x = tb[0] + tb[2] / 2, y = tb[1] + tb[3] / 2;
  if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) return false;
  for (const n of document.elementsFromPoint(x, y)) {
    if (n !== e && e.contains(n)) continue;
    const cs = getComputedStyle(n);
    if (n === e) {
      // The words' own element first: a white button on a picture is
      // read against the button, not the picture.
      const own = parseColor(cs.backgroundColor);
      if (own && own[3] >= 0.999) return false;
      if (/url\(/.test(cs.backgroundImage || '')) return true;
      continue;
    }
    if (/^(IMG|VIDEO|CANVAS|PICTURE)$/.test(n.tagName)) return true;
    // A photo is a picture wherever it is. A gradient is one only when
    // it is painted as a layer of its own behind the words (art, a
    // hero); on the text's own container it is a surface -- the glass
    // of a tab bar -- and is measured as one, as before.
    const bi = cs.backgroundImage || 'none';
    if (bi !== 'none' && (/url\(/.test(bi) || !n.contains(e))) return true;
    const bg = parseColor(cs.backgroundColor);
    if (bg && bg[3] >= 0.999) return false;
  }
  return false;
}
let onPicture = [], recordPictures = true;

// Measured in every state, not only the one that happens to be showing.
// A filled button lives in the empty and error panels, which are hidden
// by default -- so a light brand shipped white-on-yellow at 1.25:1 and
// the check called the page ready. Three of the four states were never
// looked at.
const collect = () => [...document.querySelectorAll(
    'p, span, a, li, h1, h2, h3, h4, button, label, td, th, div')]
  .filter(e => e.offsetParent !== null
      && !e.closest('[aria-hidden="true"]')
      && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
  .map(e => {
    const cs = getComputedStyle(e);
    const raw = parseColor(cs.color);
    if (!raw || raw[3] === 0) return null;
    const px0 = parseFloat(cs.fontSize), bold0 = parseInt(cs.fontWeight, 10) >= 590;
    if (pictureUnder(e)) {
      if (recordPictures) {
        onPicture.push({t: e.textContent.trim().slice(0, 30), fg: raw.slice(0, 3),
          box: textBox(e).map(Math.round),
          need: (px0 >= 24 || (px0 >= 18.66 && bold0)) ? 3.0 : 4.5, px: Math.round(px0)});
      }
      return null;
    }
    const bg = surfaceOf(e);
    const fg = over(raw, bg);
    const px = parseFloat(cs.fontSize);
    // SF Pro's semibold is 590, not the CSS ladder's 600. Testing for
    // 600 classed every Apple-faithful semibold run as regular and
    // held it to 4.5:1 where the large-text allowance applies.
    const bold = parseInt(cs.fontWeight, 10) >= 590;
    // Apple and WCAG agree here: large text may sit at 3:1.
    const need = (px >= 24 || (px >= 18.66 && bold)) ? 3.0 : 4.5;
    const r = RATIO(fg, bg);
    return r + 0.01 < need
      ? {t: e.textContent.trim().slice(0, 30), r: +r.toFixed(2), need, px: Math.round(px)}
      : null;
  })
  .filter(Boolean);


// Distinct surface treatments. iOS has essentially one card: a white
// rounded panel on the grouped background. A design carrying eight,
// where two do all the work and six appear once or twice, has accreted
// surfaces rather than chosen them -- and that accretion is most of what
// reads as generic. Reported by name so the reduction pass has a target
// list instead of the advice to prefer hierarchy over containers.
const treatments = (() => {
  const seen = new Map();
  for (const e of document.querySelectorAll('*')) {
    if (e.offsetParent === null) continue;
    const cs = getComputedStyle(e);
    const bg = parseColor(cs.backgroundColor);
    if (!bg || bg[3] <= 0.02) continue;
    const r = parseFloat(cs.borderRadius) || 0;
    if (r < 6 || e.getBoundingClientRect().width < 60) continue;
    const key = [cs.backgroundColor, Math.round(r), cs.borderTopWidth,
                 cs.borderTopColor, (cs.boxShadow || 'none').slice(0, 40)].join(' | ');
    const rec = seen.get(key) || {n: 0, sample: ''};
    rec.n++;
    if (!rec.sample) rec.sample = (e.className || e.tagName).toString().slice(0, 28);
    seen.set(key, rec);
  }
  return [...seen.entries()].map(([k, v]) => ({key: k, n: v.n, sample: v.sample}))
      .sort((a, b) => b.n - a.n);
})();

const root = document.querySelector('[data-state]');
const seen = new Map();
const sweep = () => { for (const c of collect())
    if (!seen.has(c.t) || seen.get(c.t).r > c.r) seen.set(c.t, c); };
if (root) {
  const was = root.dataset.state;
  for (const st of ['populated', 'loading', 'empty', 'error']) {
    root.dataset.state = st;
    root.getBoundingClientRect();   // force layout so offsetParent is right
    // Pictures are measured from a screenshot of the state as loaded.
    recordPictures = st === was;
    sweep();
  }
  root.dataset.state = was;
} else {
  sweep();
}
const lowContrast = [...seen.values()];
  const cs = getComputedStyle(document.documentElement);
  const v = n => cs.getPropertyValue(n).trim();
  const body = getComputedStyle(document.body);
  const de = document.documentElement;
  // A target is what takes the tap, not what is painted: Material draws a
  // 40 dp button inside a 48 dp target (an absolutely placed ::after), and
  // a checkbox's label takes the tap for its 18 dp box.
  const extent = e => {
    const r = e.getBoundingClientRect(); let w = r.width, h = r.height;
    for (const p of ['::before', '::after']) {
      const ps = getComputedStyle(e, p);
      if (ps.content && ps.content !== 'none' && ps.position === 'absolute') {
        w = Math.max(w, parseFloat(ps.width) || 0); h = Math.max(h, parseFloat(ps.height) || 0); }
    }
    return [w, h];
  };
  const small = [...document.querySelectorAll(
      'button, a[href], input, select, [role=button]')]
    .filter(e => e.offsetParent !== null)
    .map(e => { let [w, h] = extent(e);
                const lab = e.closest('label');
                if (lab) { const [lw, lh] = extent(lab); w = Math.max(w, lw); h = Math.max(h, lh); }
                return {t: (e.textContent||e.getAttribute('aria-label')||'?')
                          .trim().slice(0, 28),
                        w: Math.round(w), h: Math.round(h)}; })
    .filter(o => o.w > 0 && o.h > 0 && Math.min(o.w, o.h) < (window.__HIG_MIN_TARGET || 28));
  // In a Mac window, body text is 13pt. Text runs at 16px and up, outside
  // headings and titles, are iOS sizes brought to the desk.
  const macWin = document.querySelector('.mac-window');
  let macText = null;
  if (macWin) {
    const runs = [...macWin.querySelectorAll('*')].filter(e =>
      e.offsetParent !== null && !e.closest('h1, h2, h3, [class*="title"], [aria-hidden="true"]') &&
      [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
    const big = runs.filter(e => parseFloat(getComputedStyle(e).fontSize) >= 16);
    macText = {runs: runs.length, big: big.length,
               sample: big.slice(0, 3).map(e => e.textContent.trim().slice(0, 24) +
                                           ' ' + getComputedStyle(e).fontSize)};
  }
  // On Android, nothing is set smaller than label-small's 11 sp.
  let tiny = null;
  if (document.querySelector('.m3-device, .m3-topappbar')) {
    const runs = [...document.querySelectorAll('body *')].filter(e =>
      e.offsetParent !== null && !e.closest('[aria-hidden="true"], .demo__bar') &&
      [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
    const t = runs.filter(e => parseFloat(getComputedStyle(e).fontSize) < 11);
    tiny = {runs: runs.length, n: t.length,
            sample: t.slice(0, 3).map(e => e.textContent.trim().slice(0, 24) + ' ' + getComputedStyle(e).fontSize)};
  }
  return {
    primary: v('--md-sys-color-primary'),
    tiny,
    accent: v('--ios-accent'),
    label: v('--ios-label'),
    bg: v('--ios-bg'),
    font: body.fontFamily,
    size: body.fontSize,
    lh: body.lineHeight,
    ls: body.letterSpacing,
    overflow: de.scrollWidth - de.clientWidth,
    small: small.slice(0, 6),
    macText,
    lowContrast: lowContrast.slice(0, 8),
    onPicture: onPicture.slice(0, 24),
    treatments: treatments.slice(0, 12),
    lowCount: lowContrast.length,
  };
}"""


def chrome_path():
    """Find a browser without pinning a build number.

    Playwright's own default works when someone has run `playwright
    install`. Some environments ship a browser under a versioned
    directory instead and set PLAYWRIGHT_BROWSERS_PATH, where the default
    lookup misses -- so glob rather than hard-code, because a pinned
    build number is a check that stops running the week it changes.
    """
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    for pat in ("chromium-*/chrome-linux/chrome", "chromium/chrome",
                "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium"):
        hits = sorted(glob.glob(os.path.join(base, pat)))
        if hits:
            return hits[-1]
    return None


# Counts the pixels of a screenshot whose hue is the brand's, and those
# that are the system blue. Run on a canvas in the page so no imaging
# library is needed.
HUE_JS = """async ([png, hue, blueHue]) => {
  const img = new Image(); img.src = 'data:image/png;base64,' + png; await img.decode();
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const x = c.getContext('2d'); x.drawImage(img, 0, 0);
  const d = x.getImageData(0, 0, c.width, c.height).data;
  let brand = 0, blue = 0;
  const near = (h, t) => Math.min(Math.abs(h - t), 360 - Math.abs(h - t)) <= 14;
  for (let i = 0; i < d.length; i += 4) {
    const r = d[i] / 255, g = d[i + 1] / 255, b = d[i + 2] / 255;
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, dl = mx - mn;
    if (dl < 0.12 || l < 0.12 || l > 0.9) continue;
    const s = dl / (1 - Math.abs(2 * l - 1));
    if (s < 0.3) continue;
    let h = mx === r ? ((g - b) / dl) % 6 : mx === g ? (b - r) / dl + 2 : (r - g) / dl + 4;
    h = (h * 60 + 360) % 360;
    if (near(h, hue)) brand++; else if (near(h, blueHue)) blue++;
  }
  return {brand: brand / (d.length / 4), blue: blue / (d.length / 4)};
}"""


def hue_of(hex_colour):
    """Hue in degrees and saturation, 0-1, of a #RRGGBB colour."""
    import colorsys
    r, g, b = (int(hex_colour.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s


# The luminance under each box, lightest and darkest tenth, from a
# screenshot taken with every glyph made transparent.
UNDER_JS = """async ([png, boxes, scale]) => {
  const img = new Image(); img.src = 'data:image/png;base64,' + png; await img.decode();
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const x = c.getContext('2d'); x.drawImage(img, 0, 0);
  const lin = v => (v /= 255) <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  return boxes.map(([l, t, w, h]) => {
    const X = Math.max(0, Math.round(l * scale)), Y = Math.max(0, Math.round(t * scale));
    const W = Math.min(c.width - X, Math.round(w * scale)), H = Math.min(c.height - Y, Math.round(h * scale));
    if (W < 1 || H < 1) return null;
    const d = x.getImageData(X, Y, W, H).data, L = [];
    for (let i = 0; i < d.length; i += 4)
      L.push(0.2126 * lin(d[i]) + 0.7152 * lin(d[i + 1]) + 0.0722 * lin(d[i + 2]));
    L.sort((a, b) => a - b);
    return [L[Math.floor(L.length * 0.1)], L[Math.floor(L.length * 0.9)]];
  });
}"""


def picture_contrast(b, pg, runs):
    """Text on a picture, held to its ratio against the pixels under it.

    For light text the lightest tenth of the box is what it has to beat;
    for dark text, the darkest. A scrim that leaves one bright patch
    under a word fails on that word, which is what a reader sees."""
    import base64
    pg.add_style_tag(content="* { color: transparent !important; "
                             "text-shadow: none !important; caret-color: transparent !important; }")
    pg.wait_for_timeout(60)
    png = base64.b64encode(pg.screenshot()).decode()
    under = pg.evaluate(UNDER_JS, [png, [r["box"] for r in runs], 1])
    low = []
    lin = lambda v: (v / 255) / 12.92 if v / 255 <= 0.03928 else (((v / 255) + 0.055) / 1.055) ** 2.4
    for r, u in zip(runs, under):
        if not u:
            continue
        fl = 0.2126 * lin(r["fg"][0]) + 0.7152 * lin(r["fg"][1]) + 0.0722 * lin(r["fg"][2])
        worst = u[1] if fl > 0.18 else u[0]
        ratio = (max(fl, worst) + 0.05) / (min(fl, worst) + 0.05)
        if ratio + 0.01 < r["need"]:
            low.append({"t": r["t"], "r": round(ratio, 2), "need": r["need"], "px": r["px"]})
    return low


def check_brand_presence(b, url, name, brand, width=390):
    """The brand colour has to be on the screen, not only in theme.css.

    Every check could pass with the accent bridged correctly and the
    brand still nowhere to be seen: a design that coloured its symbols
    with the system blue, kept the accent for a single "+" and built
    the rest in grey shipped a green brand as a blue app. Measured on
    the first screen as rendered, light, at the platform's first width.
    """
    if not brand or not re.fullmatch(r"#[0-9A-Fa-f]{6}", brand):
        return
    hue, sat = hue_of(brand)
    if sat < 0.25:
        return  # a grey or near-black brand is carried by type, not colour
    pg = b.new_page(viewport={"width": width, "height": 844 if width < 600 else 900}, color_scheme="light")
    try:
        pg.goto(url + "?state=populated", wait_until="load")
        pg.wait_for_timeout(250)
        import base64
        png = base64.b64encode(pg.screenshot()).decode()
        blue_hue = hue_of("#0088FF")[0]
        same = min(abs(hue - blue_hue), 360 - abs(hue - blue_hue)) <= 28
        got = pg.evaluate(HUE_JS, [png, hue, -999 if same else blue_hue])
    finally:
        pg.close()
    share, blue = got["brand"] * 100, got["blue"] * 100
    also = (f" The system blue covers {blue:.1f}% -- symbols and highlights coloured "
            f"--ios-blue rather than the accent." if blue > share else "")
    if share < 0.2:
        bad(f"{name}: the brand colour {brand} is {share:.2f}% of the first screen -- "
            f"it is in theme.css but not in the design.{also} Put it where the eye "
            f"lands: the hero, the selected tab, the main action, the figures "
            f"(the content parts take --tint, which defaults to the accent).")
    elif share < 1.0:
        warn(f"{name}: the brand colour {brand} is only {share:.1f}% of the first "
             f"screen.{also} A brand reads when it is on the hero, a chart or the "
             f"selected tab, not just a button.")
    else:
        ok(f"{name}: the brand colour is {share:.0f}% of the first screen")


def check_browser(path, brand):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        warn("playwright not installed; skipped the browser pass, which is "
             "where resolved values and overflow actually get checked")
        return

    name = os.path.basename(path)
    url = "file://" + os.path.abspath(path)
    errors, failed = [], []
    covered_any = ran_states = False
    # macOS's floor is 20x20pt and its push buttons are 24pt tall
    # (numbers.md); holding a Mac window to iOS's 28 would flag Apple's own.
    page = open(path, encoding="utf-8", errors="replace").read()
    mac = is_mac(path, page)
    # Android's touch target is 48 x 48 dp, for every platform version.
    android = is_android(path, page)
    floor = 48 if android else 20 if mac else 28
    # An iPad layout is looked at as an iPad: the iPad Air's landscape
    # width, where the frame drops away, and wide enough to show it.
    # A Mac window is looked at on a desktop: at a phone's width its
    # sidebar leaves the content a sliver, and every finding is about
    # that sliver rather than the design.
    widths = ((1180, 1400) if is_ipad(path, page) else (1280, 1440) if mac
              else (390, 430, 1280))

    def sample(b, scheme, more):
        """Failing text runs for one appearance, optionally under IC."""
        kw = {"viewport": {"width": widths[0], "height": 900}, "color_scheme": scheme}
        if more:
            kw["contrast"] = "more"
        pg = b.new_page(**kw)
        try:
            pg.goto(url, wait_until="load")
            pg.wait_for_timeout(220)
            return pg.evaluate(BROWSER_JS)["lowContrast"]
        finally:
            pg.close()

    def tap_check(pg):
        """A design reviewers can't tap reads as a picture of an app."""
        pg.goto(url + "?state=populated", wait_until="load")
        pg.wait_for_timeout(150)
        found = pg.evaluate(CONTROLS_JS)
        if found["missing"]:
            bad(f"{name}: {len(found['missing'])} control(s) lead to a screen or "
                f"sheet that doesn't exist yet: {'; '.join(found['missing'][:5])}. "
                f"Build it with data-screen-id / data-sheet-id (prototype.js).")
        dead = []
        for c in found["controls"][:80]:
            pg.goto(url + "?state=populated", wait_until="load")
            pg.wait_for_timeout(60)
            if not pg.evaluate(TAP_JS, c["i"]):
                dead.append(c["name"] or "?")
        if dead:
            bad(f"{name}: {len(dead)} of {len(found['controls'])} control(s) do "
                f"nothing when tapped: {', '.join(dead[:6])}. Wire them with "
                f"prototype.js (data-go, data-push, data-sheet, data-toggle, "
                f"data-toast), or mark a deliberately inert one data-inert.")
        elif found["controls"]:
            ok(f"{name}: all {len(found['controls'])} controls respond to a tap")

    with sync_playwright() as p:
        launch = {"args": ["--no-sandbox"]}
        exe = chrome_path()
        if exe:
            launch["executable_path"] = exe
        try:
            b = p.chromium.launch(**launch)
        except Exception as e:
            warn(f"could not launch a browser ({str(e)[:70]}); skipped "
                 f"the browser pass. Run `playwright install chromium`.")
            return
        if True:
            try:
                check_brand_presence(b, url, name, brand, 1280 if mac else widths[0])
            except Exception as e:  # a measurement, never a crash
                warn(f"{name}: couldn't measure the brand colour ({str(e)[:60]})")
        for scheme in ("light", "dark"):
            for width in widths:
                pg = b.new_page(viewport={"width": width, "height": 900},
                                color_scheme=scheme)
                pg.on("console",
                      lambda m: errors.append(m.text)
                      if m.type == "error" else None)
                pg.on("requestfailed",
                      lambda r: failed.append(r.url))
                pg.goto(url, wait_until="load")
                pg.wait_for_timeout(220)
                if mac or android:
                    pg.evaluate(f"() => {{ window.__HIG_MIN_TARGET = {floor}; }}")
                d = pg.evaluate(BROWSER_JS)

                tag = f"{name} {scheme} {width}px"
                if d["overflow"] > 1:
                    bad(f"{tag}: the page scrolls sideways by "
                        f"{d['overflow']}px. Something has a fixed width "
                        f"wider than the viewport.")
                # Contrast is measured in BOTH appearances. It used to run
                # in light only, which is how a generator that emitted an
                # unchecked dark palette -- a navy at 1.24:1 on the dark
                # card -- came back 18/18 ready three times running.
                if width == widths[0]:
                    # Anything Increased Contrast rescues is a different
                    # finding from anything it doesn't. Apple's own
                    # secondary label is 3.44:1 on white and their filled
                    # buttons run white at about 3.5:1 -- deliberate
                    # calls, with the accessibility setting as the
                    # remedy. Failing every Apple-faithful design on
                    # those makes the check unusable, and passing text
                    # that stays unreadable at any setting makes it
                    # pointless. So: measure both, and separate them.
                    try:
                        # Texts STILL failing once Increased Contrast is on.
                        still = {c["t"] for c in sample(b, scheme, True)}
                    except Exception:
                        still = None
                    if still is None:
                        hard, soft = d["lowContrast"], []
                    else:
                        hard = [c for c in d["lowContrast"] if c["t"] in still]
                        soft = [c for c in d["lowContrast"]
                                if c["t"] not in still]
                    if d.get("onPicture"):
                        pic = picture_contrast(b, pg, d["onPicture"])
                        pg.goto(url, wait_until="load")
                        pg.wait_for_timeout(120)
                        if pic:
                            listed = ", ".join(f"\"{c['t']}\" {c['r']}:1 (needs {c['need']})"
                                               for c in pic[:4])
                            bad(f"{name} {scheme}: {len(pic)} text run(s) on a picture "
                                f"under the contrast they need, measured against the "
                                f"pixels behind them: {listed}. Deepen the scrim "
                                f"(.ios-art--scrim) or move the words off the bright part.")
                        else:
                            ok(f"{name} {scheme}: {len(d['onPicture'])} text run(s) on a "
                               f"picture clear their contrast against the pixels behind them")
                    if hard:
                        listed = ", ".join(
                            f"\"{c['t']}\" {c['r']}:1 (needs {c['need']}, "
                            f"{c['px']}px)" for c in hard[:4])
                        bad(f"{name} {scheme}: {len(hard)} text run(s) under "
                            f"the contrast they need, and still failing "
                            f"under Increased Contrast: {listed}")
                    if soft:
                        listed = ", ".join(
                            f"\"{c['t']}\" {c['r']}:1" for c in soft[:3])
                        warn(f"{name} {scheme}: {len(soft)} run(s) below "
                             f"4.5:1 at default settings but fixed by "
                             f"Increased Contrast -- Apple's own secondary "
                             f"label (3.44:1) and filled buttons (~3.5:1) "
                             f"are like this too: {listed}")
                    if not hard and not soft:
                        ok(f"{name} {scheme}: every text run meets its "
                           f"contrast requirement")

                    # Surfaces that appear once or twice have not earned a
                    # treatment of their own. Warned rather than failed:
                    # a canvas, an inspector and a dialog legitimately
                    # differ, so this is a smell to answer, not a defect.
                    # An iOS heuristic: a Mac window has a sidebar, a
                    # toolbar, a table and its selection, all rightly
                    # different surfaces.
                    treats = [] if mac else (d.get("treatments") or [])
                    oneoffs = [t for t in treats if t["n"] <= 2]
                    if len(treats) >= 6 and len(oneoffs) >= 3:
                        listed = ", ".join(
                            f"{t['sample'] or 'unnamed'} (x{t['n']})"
                            for t in oneoffs[:4])
                        warn(f"{name} {scheme}: {len(treats)} distinct surface "
                             f"treatments, {len(oneoffs)} of them used once or "
                             f"twice: {listed}. iOS has essentially one card. "
                             f"Each of these has to earn being different or "
                             f"fold into the one above it.")
                    elif treats:
                        ok(f"{name} {scheme}: {len(treats)} surface "
                           f"treatment(s), none stranded")

                    if android:
                        if d["primary"]:
                            ok(f"{name} {scheme}: --md-sys-color-primary resolves to {d['primary']}")
                        else:
                            bad(f"{name} {scheme}: --md-sys-color-primary resolves to "
                                f"nothing. The Material recipes have no colour to use.")
                    elif d["accent"]:
                        got = d["accent"].lower().replace(" ", "")
                        ok(f"{name} {scheme}: --ios-accent resolves to {got}")
                    else:
                        bad(f"{name} {scheme}: --ios-accent resolves to "
                            f"nothing. The component recipes have no colour "
                            f"to use.")

                if width == widths[0] and scheme == "light":
                    fam = d["font"].lower()
                    if android:
                        if fam.startswith("roboto") or fam.startswith('"roboto'):
                            ok(f"{name}: body font resolves to {d['font'][:44]}")
                        else:
                            bad(f"{name}: body font is {d['font'][:44]} -- Android "
                                f"sets Material's type scale in Roboto; link "
                                f"vendor/fonts/roboto.css and use --m3-type-*.")
                    elif "inter" in fam or "sf pro" in fam or "-apple-system" in fam:
                        ok(f"{name}: body font resolves to {d['font'][:44]}")
                    else:
                        bad(f"{name}: body font is {d['font'][:44]} -- the "
                            f"vendored faces are not being used.")
                    got = (d["accent"] or "").lower().replace(" ", "")
                    if brand and got and not android and got.lstrip("#") != brand.lower().lstrip("#"):
                        warn(f"{name}: --ios-accent resolves to {got} in "
                             f"light, not the brand {brand}. Check the "
                             f"bridge.")
                    if d["small"]:
                        listed = ", ".join(
                            f"{s['t']} ({s['w']}x{s['h']})" for s in d["small"])
                        rule = ("Android's minimum touch target" if android
                                else "macOS's minimum -- its default is 28"
                                if mac else "which is Apple's accessibility floor -- "
                                            "the general rule is 44")
                        unit = "dp" if android else "pt"
                        warn(f"{name}: {len(d['small'])} target(s) under {floor}{unit}, "
                             f"{rule}: {listed}")
                    else:
                        ok(f"{name}: every visible target clears {floor}{'dp' if android else 'pt'}")
                    tn = d.get("tiny")
                    if tn and tn["runs"] >= 5:
                        if tn["n"]:
                            warn(f"{name}: {tn['n']} text run(s) under 11 sp "
                                 f"({'; '.join(tn['sample'])}). Material's smallest "
                                 f"style is label-small, 11 sp.")
                        else:
                            ok(f"{name}: no text under Material's 11 sp floor")
                    mt = d.get("macText")
                    if mt and mt["runs"] >= 5:
                        if mt["big"] > 0.3 * mt["runs"]:
                            warn(f"{name}: {mt['big']} of {mt['runs']} text runs in the "
                                 f"Mac window are 16px or larger ({'; '.join(mt['sample'])}). "
                                 f"Body text on a Mac is 13pt, not iOS's 17 (Apple's typography page); "
                                 f"use the --mac-text-* styles.")
                        else:
                            ok(f"{name}: text in the Mac window is sized for the Mac")

                if width == widths[0] and scheme == "light":
                    tap_check(pg)

                # Every state has to actually render something.
                for st in ("populated", "loading", "empty", "error"):
                    if width != widths[0] or scheme != "light":
                        continue
                    pg.goto(url + "?state=" + st, wait_until="load")
                    pg.wait_for_timeout(120)
                    # Painted area, not text length. A loading state is a
                    # skeleton -- shapes standing in for text it does not
                    # have yet -- so measuring characters reported the one
                    # state that is *supposed* to be wordless as empty.
                    vis = pg.evaluate(
                        "() => [...document.querySelectorAll('.state')]"
                        ".filter(e => e.offsetParent !== null)"
                        ".map(e => e.innerText.trim().length"
                        " + [...e.querySelectorAll('*')].filter(c => {"
                        "   const r = c.getBoundingClientRect();"
                        "   return r.width > 4 && r.height > 4; }).length)")
                    ran_states = True
                    hid = pg.evaluate(COVERED_JS)
                    if hid:
                        bad(f"{name}: in the '{st}' state, scrolled to the end, "
                            f"{len(hid)} piece(s) of text are still under "
                            f"{hid[0]['by']}: \"{hid[0]['text']}\". Pad the "
                            f"bottom of the scrolling content by that element's "
                            f"height so the last of it can be read.")
                        covered_any = True
                    if not vis or not any(v > 0 for v in vis):
                        warn(f"{name}: the '{st}' state renders nothing "
                             f"visible. If the switcher was removed that is "
                             f"expected; otherwise the panel is empty.")
                    else:
                        ok(f"{name}: '{st}' state renders")
                pg.close()
        b.close()

    if not covered_any and ran_states:
        ok(f"{name}: no text left under floating bars or banners")
    modules = sorted({re.search(r"/([^/']+\.m?js)'", e).group(1) for e in errors
                      if "Access to script" in e and re.search(r"/([^/']+\.m?js)'", e)})
    if modules:
        bad(f"{name}: {', '.join(modules)} never runs: it is loaded as a module "
            f"(type=\"module\" or import), and browsers block modules on a page "
            f"opened from a file. Load it with a plain <script src> and drop "
            f"import/export, or inline it.")
        errors = [e for e in errors if "Access to script" not in e
                  and "net::ERR_FAILED" not in e]
        failed = [f for f in failed if not any(f.endswith(m) for m in modules)]
    if errors:
        bad(f"{name}: {len(errors)} console error(s): {errors[0][:90]}")
    else:
        ok(f"{name}: no console errors")
    if failed:
        bad(f"{name}: {len(failed)} request(s) failed: {failed[0][:90]}")
    else:
        ok(f"{name}: no failed requests")


# --------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Check a design directory before calling it done.")
    ap.add_argument("directory")
    ap.add_argument("--brand", help="expected accent, e.g. '#C1552E'")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()

    root = os.path.abspath(a.directory)
    if not os.path.isdir(root):
        sys.exit(f"not a directory: {a.directory}")

    pages = sorted(glob.glob(os.path.join(root, "**", "*.html"), recursive=True))
    # vendor/ is the kit; figma/ is export_figma.py's output, not a page.
    pages = [p for p in pages if not {"vendor", "figma"} & set(os.path.relpath(p, root).split(os.sep))]
    if not pages:
        sys.exit(f"no .html in {a.directory}. The deliverable is a working "
                 f"screen; a directory of notes is not one.")

    css = check_theme(root)
    brand = a.brand
    if not brand and css:
        m = re.search(r"--[a-z0-9-]+-accent:\s*(#[0-9A-Fa-f]{6})", css)
        brand = m.group(1) if m else None

    for p in pages:
        html = open(p, encoding="utf-8").read()
        check_link_order(p, html)
        check_offline(p, html)
        check_local_refs(p, html)
        check_states(p, html)
        check_hardcoded(p, html)
        check_glyph_icons(p, html)
        check_token_overrides(p, html)
        check_uses_kit(p, html)
        check_content_first(p, html)
        check_prototype_data(p, html)
        if is_android(p, html):
            check_icons_named(p, html)
        else:
            check_symbols_named(p, html)
        if not a.no_browser:
            check_browser(p, brand)

    for m in PASS:
        print(f"  ok   {m}")
    for m in WARN:
        print(f"  warn {m}")
    for m in FAIL:
        print(f"  FAIL {m}")

    n = len(PASS) + len(FAIL)
    print(f"\n{len(PASS)}/{n} passed, {len(WARN)} warning(s)")
    if FAIL:
        print(f"{len(FAIL)} failure(s) -- not ready to ship.")
        return 1
    print("ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

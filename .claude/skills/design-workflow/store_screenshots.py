#!/usr/bin/env python3
"""Turn a design's screens into App Store screenshots, at Apple's sizes.

    python3 store_screenshots.py ./design                 # captioned, the platform's sizes
    python3 store_screenshots.py ./design --plain         # the bare screens
    python3 store_screenshots.py ./design --sizes iphone,iphone-large
    python3 store_screenshots.py ./design --size 1080x1920@3   # any other store

Sizes, from Apple's App Store Connect "Screenshot specifications"
(developer.apple.com/help/app-store-connect/reference/screenshot-specifications/):

  iphone        1206 x 2622  iPhone with Dynamic Island (medium display) --
                             the one size Apple requires for an iPhone app.
                             The kit's 402 x 874pt screen at 3x.
  iphone-large  1320 x 2868  iPhone with Dynamic Island (large display)
  ipad          2752 x 2064  iPad 13-inch display, landscape -- required for
                             an app that runs on iPad
  ipad-portrait 2064 x 2752  iPad 13-inch display, portrait
  mac           2880 x 1800  Mac, 16:10

Apple scales the required size down for the smaller displays, takes .png or
.jpeg, up to 10 per size, and no alpha channel; every file written here is
checked for all three. Google Play's limits are not built in: pass --size
from Play Console's current requirements.

What each screenshot shows comes from store.json in the design folder:

    {"shots": [
      {"screen": "plants", "caption": "See what needs water today"},
      {"click": "[data-item=\\"plants.fern\\"]", "caption": "Every plant, its own schedule"},
      {"sheet": "add", "caption": "Add a plant in seconds", "subtitle": "Reminders included"}
    ]}

"screen" shows a screen by its data-screen-id, "click" taps through the
prototype first (a selector or a list of them), "sheet" opens a sheet.
Without store.json every screen is taken in order with its title as a
placeholder caption, and a starter store.json is written to edit.

The captioned style sets the screen on the brand colour with the caption
above it and draws no device: a rounded screen needs no Apple artwork.
Output goes to store-screenshots/ beside the design folder, one folder per
size, so it never ships inside the design.
"""

import argparse
import base64
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_design  # noqa: E402
from build_theme import contrast, hex_to_rgb  # noqa: E402
from stress_test import SHOW_JS  # noqa: E402

SIZES = {
    "iphone": ("iPhone with Dynamic Island (medium display)", 1206, 2622, 3),
    "iphone-large": ("iPhone with Dynamic Island (large display)", 1320, 2868, 3),
    "ipad": ("iPad 13-inch display, landscape", 2752, 2064, 2),
    "ipad-portrait": ("iPad 13-inch display, portrait", 2064, 2752, 2),
    "mac": ("Mac, 16:10", 2880, 1800, 2),
}
DEFAULTS = {"iphone": ["iphone", "iphone-large"], "ipad": ["ipad"], "mac": ["mac"], "android": []}
MAX_PER_SIZE = 10

# The design without its review chrome, its screen filling the frame.
BARE_CSS = """
.demo__bar { display: none !important; }
.stage { padding: 0 !important; place-items: stretch !important; background: var(--ios-bg) !important; }
.device { width: 100% !important; height: 100vh !important; border-radius: 0 !important; box-shadow: none !important; }
.ipad-stage { padding: 0 !important; gap: 0 !important; }
.ipad { width: 100vw !important; height: 100vh !important; border: 0 !important; border-radius: 0 !important;
        box-shadow: none !important; }
.mac-desktop { min-height: 100vh !important; }
"""

COMPOSE = """<!doctype html><meta charset="utf-8">
__FONTS__
<style>
  html, body { margin: 0; width: __W__px; height: __H__px; overflow: hidden; }
  body { position: relative; display: flex; flex-direction: column; align-items: center;
         background: linear-gradient(165deg, color-mix(in oklab, __BRAND__ 82%, #fff), __BRAND__ 45%,
                                     color-mix(in oklab, __BRAND__ 72%, #000));
         color: __INK__; font-family: __FAMILY__; -webkit-font-smoothing: antialiased; }
  .cap { margin: __TOP__px __SIDE__px 0; text-align: center; }
  h1 { margin: 0; font-size: __CAP__px; line-height: 1.1; font-weight: 700; letter-spacing: -0.01em;
       text-wrap: balance; }
  p { margin: __GAP__px 0 0; font-size: __SUB__px; line-height: 1.25; font-weight: 500; opacity: .86;
      text-wrap: balance; }
  img { display: block; width: __IMGW__px; margin-top: __IMGTOP__px; border-radius: __RADIUS__px;
        box-shadow: 0 __SHADOW__px __BLUR__px rgba(0, 0, 0, .28); }
</style>
<div class="cap"><h1>__CAPTION__</h1>__SUBTITLE__</div>
<img src="data:image/png;base64,__IMG__" alt="">
"""


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def brand_of(root):
    """The brand colour theme.css carries: the accent, or Material's primary."""
    p = os.path.join(root, "theme.css")
    css = open(p, encoding="utf-8").read() if os.path.isfile(p) else ""
    m = (re.search(r"--[a-z0-9-]+-accent:\s*(#[0-9A-Fa-f]{6})", css)
         or re.search(r"--md-sys-color-primary:\s*(#[0-9A-Fa-f]{6})", css))
    return m.group(1) if m else "#0088FF"


def fonts_of(root, plat):
    links = []
    for name in ("inter.css", "roboto.css"):
        f = os.path.join(root, "vendor", "fonts", name)
        if os.path.isfile(f):
            links.append(f'<link rel="stylesheet" href="file://{f}">')
    family = ('"Roboto", system-ui, sans-serif' if plat == "android"
              else '-apple-system, BlinkMacSystemFont, "Inter", system-ui, sans-serif')
    return "\n".join(links), family


def plan(root, page):
    """The shots: store.json's, or every screen with its title."""
    path = os.path.join(root, "store.json")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            shots = json.load(f).get("shots", [])
        return shots, False
    html = open(page, encoding="utf-8", errors="replace").read()
    shots = []
    for sid in dict.fromkeys(re.findall(r'data-screen-id="([^"]+)"', html)):
        shots.append({"screen": sid, "caption": sid.replace("-", " ").title()})
    if not shots:
        shots = [{"caption": "Your headline here"}]
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"shots": shots[:MAX_PER_SIZE]}, f, indent=2)
        f.write("\n")
    return shots, True


def flatten(png_bytes, out_path):
    """Write the screenshot without an alpha channel, as Apple requires.

    Pillow when it's there; otherwise the PNG is re-encoded as RGB by hand,
    which needs nothing but zlib."""
    try:
        from PIL import Image
        import io
        Image.open(io.BytesIO(png_bytes)).convert("RGB").save(out_path, "PNG", optimize=True)
        return
    except ImportError:
        pass
    import struct
    import zlib
    pos, chunks = 8, []
    while pos < len(png_bytes):
        n = struct.unpack(">I", png_bytes[pos:pos + 4])[0]
        kind = png_bytes[pos + 4:pos + 8]
        chunks.append((kind, png_bytes[pos + 8:pos + 8 + n]))
        pos += 12 + n
    ihdr = dict(chunks)[b"IHDR"]
    w, h, depth, ctype = struct.unpack(">IIBB", ihdr[:10])
    if ctype != 6 or depth != 8:
        open(out_path, "wb").write(png_bytes)
        return
    raw = zlib.decompress(b"".join(d for k, d in chunks if k == b"IDAT"))
    stride, bpp, prev, rows = w * 4, 4, bytearray(w * 4), []
    i = 0
    for _ in range(h):
        f, line = raw[i], bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b, c = prev[x], prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        rows.append(b"\0" + bytes(v for k, v in enumerate(line) if k % 4 != 3))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    with open(out_path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))


def png_info(path):
    """(width, height, has_alpha) read from the file's own header."""
    import struct
    with open(path, "rb") as fh:
        head = fh.read(26)
    w, h = struct.unpack(">II", head[16:24])
    return w, h, head[25] in (4, 6)


def capture(b, url, shot, plat, w, h, scale, element=None):
    pg = b.new_page(viewport={"width": w // scale, "height": h // scale},
                    device_scale_factor=scale, color_scheme=shot.get("appearance", "light"))
    try:
        pg.goto(url, wait_until="load")
        pg.add_style_tag(content=BARE_CSS)
        pg.evaluate("document.fonts.ready.then(() => true)")
        pg.wait_for_timeout(250)
        clicks = shot.get("click") or []
        for sel in [clicks] if isinstance(clicks, str) else clicks:
            pg.locator(sel).filter(visible=True).first.click()
            pg.wait_for_timeout(450)
        if shot.get("screen") and not clicks:
            pg.evaluate(SHOW_JS, ["screen", shot["screen"]])
        if shot.get("sheet"):
            pg.evaluate(SHOW_JS, ["sheet", shot["sheet"]])
        pg.wait_for_timeout(250)
        target = pg.query_selector(element) if element else None
        return (target or pg).screenshot(type="png")
    finally:
        pg.close()


def run(root, sizes, plain, out):
    from playwright.sync_api import sync_playwright
    page = os.path.join(root, "index.html")
    html = open(page, encoding="utf-8", errors="replace").read()
    plat = ("mac" if check_design.is_mac(page, html) else "ipad" if check_design.is_ipad(page, html)
            else "android" if check_design.is_android(page, html) else "iphone")
    shots, fresh = plan(root, page)
    if len(shots) > MAX_PER_SIZE:
        print(f"  warn {len(shots)} shots in store.json; the App Store takes {MAX_PER_SIZE} per size, "
              f"so only the first {MAX_PER_SIZE} are made")
        shots = shots[:MAX_PER_SIZE]
    brand = brand_of(root)
    ink = "#FFFFFF" if contrast((255, 255, 255), hex_to_rgb(brand)) >= 3 else "#111111"
    links, family = fonts_of(root, plat)
    url = "file://" + os.path.abspath(page) + "?state=populated"
    written = []
    launch = {"args": ["--no-sandbox"]}
    exe = check_design.chrome_path()
    if exe:
        launch["executable_path"] = exe
    with sync_playwright() as p:
        b = p.chromium.launch(**launch)
        for key in sizes:
            label, W, H, scale = SIZES[key]
            folder = os.path.join(out, key)
            os.makedirs(folder, exist_ok=True)
            for n, shot in enumerate(shots, 1):
                slug = re.sub(r"[^a-z0-9]+", "-", (shot.get("screen") or shot.get("sheet") or
                                                   shot.get("caption") or "shot").lower()).strip("-")[:32]
                dest = os.path.join(folder, f"{n:02d}-{slug}.png")
                if plain:
                    png = capture(b, url, shot, plat, W, H, scale)
                else:
                    # The screen at the size it is shown at, then set on the
                    # brand colour under its caption at the store's size.
                    landscape = W > H
                    if plat == "mac":
                        raw = capture(b, url, shot, plat, 2880, 1800, 2, element=".mac-window")
                        imgw = round(W * 0.84)
                    else:
                        imgw = round(W * (0.80 if landscape else 0.84))
                        raw = capture(b, url, shot, plat, W, H, scale)
                    cap = W * (0.044 if landscape else 0.074)
                    radius = 0 if plat == "mac" else W * (0.022 if landscape else 0.075)
                    body = (COMPOSE.replace("__FONTS__", links).replace("__FAMILY__", family)
                            .replace("__W__", str(W)).replace("__H__", str(H))
                            .replace("__BRAND__", brand).replace("__INK__", ink)
                            .replace("__TOP__", str(round(H * (0.06 if landscape else 0.055))))
                            .replace("__SIDE__", str(round(W * 0.07)))
                            .replace("__CAP__", f"{cap:.1f}").replace("__SUB__", f"{cap * 0.5:.1f}")
                            .replace("__GAP__", f"{cap * 0.3:.1f}")
                            .replace("__IMGW__", str(imgw))
                            .replace("__IMGTOP__", str(round(H * (0.045 if landscape else 0.04))))
                            .replace("__RADIUS__", f"{radius:.1f}")
                            .replace("__SHADOW__", f"{W * 0.01:.1f}").replace("__BLUR__", f"{W * 0.04:.1f}")
                            .replace("__CAPTION__", esc(shot.get("caption", "")))
                            .replace("__SUBTITLE__", f"<p>{esc(shot['subtitle'])}</p>" if shot.get("subtitle") else "")
                            .replace("__IMG__", base64.b64encode(raw).decode()))
                    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
                        f.write(body)
                    try:
                        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
                        pg.goto("file://" + f.name, wait_until="load")
                        pg.evaluate("document.fonts.ready.then(() => true)")
                        pg.wait_for_timeout(150)
                        png = pg.screenshot(type="png")
                        pg.close()
                    finally:
                        os.unlink(f.name)
                flatten(png, dest)
                written.append((key, label, W, H, dest))
        b.close()
    return plat, written, fresh


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("design", nargs="?", default="design")
    ap.add_argument("--sizes", help=f"comma-separated: {', '.join(SIZES)} (default: the platform's)")
    ap.add_argument("--size", action="append", default=[],
                    help="another size, WxH@scale, e.g. 1080x1920@3 for a store whose rules you've checked")
    ap.add_argument("--plain", action="store_true", help="the bare screens, without caption or background")
    ap.add_argument("-o", "--out", help="output folder (default: store-screenshots/ beside the design)")
    a = ap.parse_args()
    root = os.path.abspath(a.design)
    if not os.path.isfile(os.path.join(root, "index.html")):
        sys.exit(f"no index.html in {a.design}")
    for s in a.size:
        m = re.fullmatch(r"(\d+)x(\d+)@(\d)", s)
        if not m:
            sys.exit(f"--size {s}: use WxH@scale, e.g. 1080x1920@3")
        w, h, sc = map(int, m.groups())
        if w % sc or h % sc:
            sys.exit(f"--size {s}: {w}x{h} isn't a whole number of points at {sc}x")
        SIZES[s] = (f"{w} x {h}", w, h, sc)
    page = os.path.join(root, "index.html")
    html = open(page, encoding="utf-8", errors="replace").read()
    plat = ("mac" if check_design.is_mac(page, html) else "ipad" if check_design.is_ipad(page, html)
            else "android" if check_design.is_android(page, html) else "iphone")
    sizes = [s.strip() for s in a.sizes.split(",")] if a.sizes else list(DEFAULTS[plat])
    sizes += [s for s in a.size if s not in sizes]
    unknown = [s for s in sizes if s not in SIZES]
    if unknown:
        sys.exit(f"unknown size {', '.join(unknown)}; known: {', '.join(SIZES)}, or --size WxH@scale")
    if not sizes:
        sys.exit("an Android design has no built-in size: Google Play's limits aren't built in. "
                 "Pass --size from Play Console's current requirements, e.g. --size 1080x1920@3.")
    out = os.path.abspath(a.out or os.path.join(os.path.dirname(root), "store-screenshots"))
    try:
        plat, written, fresh = run(root, sizes, a.plain, out)
    except ImportError:
        sys.exit("needs playwright: pip install playwright && playwright install chromium")
    bad = 0
    for key, label, W, H, dest in written:
        w, h, alpha = png_info(dest)
        ok = (w, h) == (W, H) and not alpha
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {os.path.relpath(dest)}  {w} x {h}"
              + ("" if ok else f" (want {W} x {H}, no alpha)"))
    print(f"\n{len(written)} screenshot(s) for {', '.join(dict.fromkeys(k for k, *_ in written))}, "
          f"in {os.path.relpath(out)}/")
    if fresh:
        print(f"  The captions are placeholders. Edit {os.path.relpath(os.path.join(root, 'store.json'))} "
              f"-- what each shot shows and says -- and run this again.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

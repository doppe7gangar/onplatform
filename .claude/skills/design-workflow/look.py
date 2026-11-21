#!/usr/bin/env python3
"""Every screen of a design on one sheet, the way a person first sees them.

The checks measure a design; they can't say whether it looks good. That
takes eyes, on all of it at once: a colour used on every screen, one
card style too many, a tab bar sitting on the content only show when the
screens are side by side. This renders every screen and sheet at the
device's size, light and dark, and lays them out on one contact sheet:

    .visual-review/look.png           every screen, light above dark
    .visual-review/look/<mode>-<kind>-<id>.png   each one on its own

    python3 look.py ./design
    python3 look.py ./design --light-only

Open look.png and judge it against references/taste.md before calling a
design done. Nothing here passes or fails.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_design  # noqa: E402  (browser path)
import stress_test  # noqa: E402  (platform, screens and sheets)

GAP, PAD, LABEL = 28, 36, 30


def render(root, modes):
    from playwright.sync_api import sync_playwright
    page = os.path.join(root, "index.html")
    html = open(page, encoding="utf-8", errors="replace").read()
    plat, (w, h), _ = stress_test.platform(page, html)
    out = os.path.join(root, ".visual-review", "look")
    os.makedirs(out, exist_ok=True)
    url = "file://" + os.path.abspath(page) + "?state=populated"
    launch = {"args": ["--no-sandbox"]}
    exe = check_design.chrome_path()
    if exe:
        launch["executable_path"] = exe
    shots = {m: [] for m in modes}
    with sync_playwright() as p:
        b = p.chromium.launch(**launch)
        for mode in modes:
            pg = b.new_page(viewport={"width": w, "height": h}, color_scheme=mode, device_scale_factor=1)
            pg.goto(url, wait_until="load")
            pg.evaluate("document.fonts.ready.then(() => true)")
            pg.wait_for_timeout(200)
            targets = pg.evaluate(stress_test.TARGETS_JS)
            places = [("screen", s) for s in targets["screens"]] or [("screen", None)]
            places += [("sheet", s) for s in targets["sheets"]]
            for kind, ident in places:
                pg.evaluate(stress_test.SHOW_JS, [kind, ident])
                pg.wait_for_timeout(120)
                name = f"{mode}-{kind}-{ident or 'page'}.png"
                frame = pg.query_selector(".device, .ipad, .mac-window, .m3-device")
                (frame or pg).screenshot(path=os.path.join(out, name))
                shots[mode].append((f"{ident or 'page'}{' (sheet)' if kind == 'sheet' else ''}",
                                    os.path.join(out, name)))
            pg.close()
        b.close()
    return plat, shots


def sheet(root, shots):
    from PIL import Image, ImageDraw, ImageFont
    rows = [r for r in shots.values() if r]
    imgs = [[(label, Image.open(path).convert("RGB")) for label, path in row] for row in rows]
    cw = max(i.width for row in imgs for _, i in row)
    ch = max(i.height for row in imgs for _, i in row)
    cols = max(len(row) for row in imgs)
    W = PAD * 2 + cols * cw + (cols - 1) * GAP
    H = PAD * 2 + len(imgs) * (ch + LABEL) + (len(imgs) - 1) * GAP
    canvas = Image.new("RGB", (W, H), (236, 238, 242))
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.load_default(size=20)
    except TypeError:
        font = ImageFont.load_default()
    for r, row in enumerate(imgs):
        y = PAD + r * (ch + LABEL + GAP)
        for c, (label, im) in enumerate(row):
            x = PAD + c * (cw + GAP)
            d.text((x, y + 6), label, fill=(70, 74, 84), font=font)
            canvas.paste(im, (x, y + LABEL))
    path = os.path.join(root, ".visual-review", "look.png")
    canvas.save(path)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("directory")
    ap.add_argument("--light-only", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.directory)
    modes = ["light"] if a.light_only else ["light", "dark"]
    plat, shots = render(root, modes)
    path = sheet(root, shots)
    n = sum(len(v) for v in shots.values())
    print(f"{n} renders of the {plat} design on one sheet: {path}")
    print("Open it and judge it against references/taste.md before calling the design done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""store_screenshots.py writes App Store screenshots Apple will take.

For an iPhone, iPad and Mac starter: every file has to be exactly the
size Apple's screenshot specifications list for that display and carry
no alpha channel; without store.json a starter one is written; --plain
and a custom --size work; an Android design without --size is refused
with the reason; and the PNG writer works without Pillow. The design
folder still passes the publish audit with store.json in it.
"""

import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DESIGN = os.path.join(ROOT, ".claude", "skills", "design-workflow")
TOOL = os.path.join(DESIGN, "store_screenshots.py")
FAILED = []
# Apple's App Store Connect "Screenshot specifications", written in here
# rather than read from the tool, so the tool can't drift from them.
APPLE = {"iphone": (1206, 2622), "iphone-large": (1320, 2868), "ipad": (2752, 2064), "mac": (2880, 1800)}


def c(ok, label, got=""):
    print(f"  {'ok  ' if ok else 'FAIL'} {label}" + ("" if ok else f"\n       {str(got)[-700:]}"))
    if not ok:
        FAILED.append(label)


def info(path):
    import struct
    with open(path, "rb") as fh:
        head = fh.read(26)
    return struct.unpack(">II", head[16:24]) + (head[25] in (4, 6),)


def pngs(folder):
    return sorted(os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".png")) \
        if os.path.isdir(folder) else []


def scaffold(tmp, kind, model):
    out = os.path.join(tmp, kind, "design")
    subprocess.run([sys.executable, os.path.join(DESIGN, "new_project.py"), "--name", "Supper",
                    "--brand", "#C1552E", "--kind", kind, "--model", model, "--screens", "Tonight,Recipes",
                    "--thing", "recipes", "-o", out], check=True, capture_output=True)
    return out


def main():
    tmp = tempfile.mkdtemp(prefix="store-")
    try:
        for kind, model, sizes in (("ios", "tabs", ("iphone", "iphone-large")), ("ipados", "sidebar", ("ipad",)),
                                   ("macos", "sidebar", ("mac",))):
            d = scaffold(tmp, kind, model)
            p = subprocess.run([sys.executable, TOOL, d], capture_output=True, text=True)
            c(p.returncode == 0, f"{kind}: runs", p.stdout + p.stderr)
            c(os.path.isfile(os.path.join(d, "store.json")) and "placeholders" in p.stdout,
              f"{kind}: writes a starter store.json and says the captions are placeholders")
            for size in sizes:
                files = pngs(os.path.join(os.path.dirname(d), "store-screenshots", size))
                dims = {info(f)[:2] for f in files}
                c(files and dims == {APPLE[size]}, f"{kind}: {size} screenshots are {APPLE[size][0]} x {APPLE[size][1]}", dims)
                c(files and not any(info(f)[2] for f in files), f"{kind}: {size} has no alpha channel")

        d = os.path.join(tmp, "ios", "design")
        out = os.path.join(tmp, "plain")
        p = subprocess.run([sys.executable, TOOL, d, "--plain", "--sizes", "iphone", "-o", out], capture_output=True, text=True)
        files = pngs(os.path.join(out, "iphone"))
        c(p.returncode == 0 and files and {info(f)[:2] for f in files} == {APPLE["iphone"]}, "--plain at the required iPhone size", p.stdout)
        p = subprocess.run([sys.executable, TOOL, d, "--sizes", "iphone", "--size", "1080x1920@3", "-o", out],
                           capture_output=True, text=True)
        c(p.returncode == 0 and {info(f)[:2] for f in pngs(os.path.join(out, "1080x1920@3"))} == {(1080, 1920)},
          "a custom --size", p.stdout + p.stderr)
        p = subprocess.run([sys.executable, TOOL, d, "--sizes", "watch"], capture_output=True, text=True)
        c(p.returncode != 0 and "unknown size" in p.stderr, "an unknown size is refused", p.stderr)

        a = scaffold(tmp, "android", "tabs")
        p = subprocess.run([sys.executable, TOOL, a], capture_output=True, text=True)
        c(p.returncode != 0 and "Google Play" in p.stderr and "--size" in p.stderr,
          "an Android design without --size is refused, with why", p.stderr)

        p = subprocess.run([sys.executable, os.path.join(DESIGN, "check_distribution.py"), d, "--purpose", "publish"],
                           capture_output=True, text=True)
        c(p.returncode == 0, "the design still passes the publish audit with store.json in it", p.stdout)

        # The writer without Pillow: the hand-rolled PNG re-encoder.
        code = ("import sys; sys.modules['PIL'] = None; sys.path.insert(0, %r); import store_screenshots as s; "
                "from playwright.sync_api import sync_playwright\n"
                "with sync_playwright() as p:\n"
                "    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 120, 'height': 90}, device_scale_factor=2)\n"
                "    pg.set_content('<body style=\"margin:0;background:linear-gradient(90deg,#C1552E,#123)\">x</body>')\n"
                "    s.flatten(pg.screenshot(type='png'), %r); b.close()\n"
                "print(s.png_info(%r))") % (DESIGN, os.path.join(tmp, "nopil.png"), os.path.join(tmp, "nopil.png"))
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        c(p.returncode == 0 and "(240, 180, False)" in p.stdout, "without Pillow it still writes an opaque PNG", p.stdout + p.stderr)
        try:
            from PIL import Image
            im = Image.open(os.path.join(tmp, "nopil.png"))
            im.load()
            px = im.getpixel((5, 90))
            c(im.mode == "RGB" and abs(px[0] - 0xC1) < 12 and abs(px[1] - 0x55) < 12,
              "and the picture survives the re-encoding", (im.mode, px))
        except ImportError:
            pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if FAILED:
        print(f"\n{len(FAILED)} failed")
        return 1
    print("\nall passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

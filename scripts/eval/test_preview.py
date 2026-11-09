#!/usr/bin/env python3
"""preview.py serves a design and reloads it, in a real browser, when it changes.

Scaffolds a design, starts the preview on a free port, and checks that the
page arrives with its reload script, that other files arrive untouched,
that nothing outside the folder can be read, that an open page in Chromium
reloads by itself after a file in the design changes, and that --phone
prints an address for a phone.

Needs Playwright with Chromium.
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DESIGN = os.path.join(ROOT, ".claude", "skills", "design-workflow")
FAILED = []


def expect(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    if not ok:
        FAILED.append(label)
        if detail:
            print("       " + str(detail)[-600:])


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""


def start(design, *extra):
    port = free_port()
    p = subprocess.Popen([sys.executable, os.path.join(DESIGN, "preview.py"), design,
                          "--port", str(port), *extra], stdout=subprocess.PIPE, text=True)
    first = p.stdout.readline()
    lines = [first]
    if extra:
        lines.append(p.stdout.readline())
    return p, port, lines


def main():
    base = tempfile.mkdtemp(prefix="preview-")
    design = os.path.join(base, "design")
    subprocess.run([sys.executable, os.path.join(DESIGN, "new_project.py"), "--name", "Pantry",
                    "--brand", "#C1552E", "--kind", "ios", "--model", "tabs", "-o", design],
                   check=True, capture_output=True)
    open(os.path.join(base, "secret.txt"), "w").write("not for the page")
    server, port, lines = start(design)
    url = f"http://127.0.0.1:{port}/"
    try:
        expect("it says where the preview is", lines[0].startswith(f"preview: {url}"), lines)
        code, html = get(url)
        expect("the page arrives with its reload script",
               code == 200 and "preview.py: reload" in html, html[-300:])
        code, css = get(url + "vendor/ios-components.css")
        expect("other files arrive as they are", code == 200 and "preview.py" not in css)
        code, _ = get(url + "../secret.txt")
        expect("nothing outside the design folder can be read", code == 404, code)

        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(url, wait_until="load")
            page.evaluate("window.__marker = 1")
            time.sleep(1.0)
            with open(os.path.join(design, "theme.css"), "a") as f:
                f.write("\n/* edited */\n")
            reloaded = False
            for _ in range(30):
                time.sleep(0.2)
                try:
                    if page.evaluate("window.__marker === undefined"):
                        reloaded = True
                        break
                except Exception:
                    continue  # mid-navigation
            expect("an open page reloads itself after the design changes", reloaded)
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)

    phone, _, lines = start(design, "--phone")
    try:
        expect("--phone prints an address for a phone on the network",
               "on a phone on this network" in lines[1] or "network address" in lines[1], lines)
    finally:
        phone.terminate()
        phone.wait(timeout=5)
    shutil.rmtree(base, ignore_errors=True)

    if FAILED:
        print(f"\n{len(FAILED)} failed")
        return 1
    print("\nall passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

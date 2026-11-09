#!/usr/bin/env python3
"""Do the React components work from a keyboard and a screen reader?

Bundles ui-kit-for-apple-platforms/react/example.jsx, which uses every component,
serves it, and drives it in Chromium the way a person without a mouse
would: Tab to a row and press Enter, arrow through the segmented control
and the tabs, Space on the switch, open the sheet and try to Tab out of
it, Escape, and check focus comes back to what opened it. axe-core then
audits the page with and without each modal open, and the page is
rendered light and dark with no console errors.

Needs node and npm. The first run installs react, react-dom, esbuild and
axe-core into scripts/eval/out/react-deps (ignored by git).

    python3 scripts/eval/test_react_kit.py
    python3 scripts/eval/test_react_kit.py --save /tmp/react   # keep screenshots
"""

import argparse
import functools
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, "..", "..", ".claude", "skills", "ui-kit-for-apple-platforms"))
DEPS = os.path.join(HERE, "out", "react-deps")
PACKAGES = ["react@18.3.1", "react-dom@18.3.1", "esbuild@0.24.0", "axe-core@4.10.2"]

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Kit in React</title>
<link rel="stylesheet" href="ios-tokens.css"><link rel="stylesheet" href="ios-components.css">
<link rel="stylesheet" href="ios-react.css">
<style>body{margin:0;background:var(--ios-bg);padding-bottom:100px}
.ios-tabbar{position:fixed;bottom:12px;left:50%;transform:translateX(-50%)}</style>
</head><body><div id="root"></div><script type="module" src="app.js"></script></body></html>
"""


def install():
    if all(os.path.isdir(os.path.join(DEPS, "node_modules", p.rsplit("@", 1)[0]))
           for p in PACKAGES):
        return
    os.makedirs(DEPS, exist_ok=True)
    if not os.path.exists(os.path.join(DEPS, "package.json")):
        open(os.path.join(DEPS, "package.json"), "w").write('{"private": true}\n')
    subprocess.run(["npm", "install", "--silent", "--no-audit", "--no-fund", *PACKAGES],
                   cwd=DEPS, check=True)


def build(site):
    esbuild = os.path.join(DEPS, "node_modules", ".bin", "esbuild")
    subprocess.run([esbuild, os.path.join(KIT, "react", "example.jsx"), "--bundle",
                    "--jsx=automatic", "--format=esm", "--log-level=warning",
                    "--define:process.env.NODE_ENV=\"development\"",
                    "--outfile=" + os.path.join(site, "app.js")],
                   env=dict(os.environ, NODE_PATH=os.path.join(DEPS, "node_modules")), check=True)
    for f in (os.path.join("tokens", "ios-tokens.css"), "ios-components.css",
              os.path.join("react", "ios-react.css")):
        shutil.copy(os.path.join(KIT, f), site)
    shutil.copy(os.path.join(DEPS, "node_modules", "axe-core", "axe.min.js"), site)
    open(os.path.join(site, "index.html"), "w").write(PAGE)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(site):
    httpd = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=site))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/index.html"


def run_checks(url, save):
    from playwright.sync_api import sync_playwright
    results = []

    def check(label, ok, detail=""):
        results.append(bool(ok))
        print(f"{'ok  ' if ok else 'FAIL'} {label}" + (f": {detail}" if detail and not ok else ""))

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        errors = []
        for scheme in ("light", "dark"):
            ctx = browser.new_context(viewport={"width": 402, "height": 874},
                                      color_scheme=scheme, device_scale_factor=2)
            page = ctx.new_page()
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(url)
            page.wait_for_selector(".ios-navbar")
            if save:
                page.screenshot(path=os.path.join(save, f"{scheme}.png"), full_page=True)
            if scheme == "dark":
                ctx.close()
                continue

            active = lambda: page.evaluate("document.activeElement && (document.activeElement.getAttribute('aria-label') || document.activeElement.textContent || document.activeElement.tagName)")
            log = lambda: page.inner_text("#log")
            # Contrast is left out of the gate and counted on its own: the
            # kit keeps Apple's light palette, which ios-components.css
            # documents as under 4.5:1 in places, Apple's own values.
            axe = lambda: page.evaluate("""async () => {
                const r = await axe.run(document, {resultTypes: ['violations'],
                                                   rules: {'color-contrast': {enabled: false}}});
                return r.violations.filter(v => ['serious', 'critical'].includes(v.impact))
                         .map(v => v.id + ' (' + v.nodes.length + ')'); }""")
            page.add_script_tag(url=url.replace("index.html", "axe.min.js"))

            # The kit's look arrived: measured row height, real classes.
            h = page.eval_on_selector(".ios-list__row", "e => e.getBoundingClientRect().height")
            check("rows take the kit's 52pt height", h >= 52, f"{h}px")
            check("kit components rendered",
                  all(page.query_selector(s) for s in (".ios-navbar", ".ios-segmented",
                      ".ios-switch", ".ios-stepper", ".ios-slider", ".ios-tabbar", ".ios-chip")))

            # Content first: whole cards are one tap, named by their title;
            # figures are images a screen reader can name.
            check("content parts rendered",
                  all(page.query_selector(s) for s in (".ios-hero", ".ios-card", ".ios-ring", ".ios-bars",
                      ".ios-tile", ".ios-stats", ".ios-carousel", ".ios-sectionhead", ".ios-progress")))
            card = page.get_by_role("button", name="Budget", exact=True)
            check("a tappable card is a button named by its title", card.count() == 1)
            card.focus()
            page.keyboard.press("Enter")
            check("Enter on a focused card opens it", "open budget" in log(), log())
            tile = page.get_by_role("button", name="Food, 12")
            check("a tile is a button named by its title and count", tile.count() == 1)
            page.get_by_role("button", name="See Budget").click()
            check("the hero's own action is reachable above its cover",
                  "budget" in log().split("|")[-1] and "open month" not in log(), log())
            check("a ring is an image with its value in words",
                  page.get_by_role("img", name="82% of the budget spent").count() == 1)
            check("progress reports its value",
                  page.get_by_role("progressbar", name="Budget used").get_attribute("aria-valuenow") == "82")
            cols = page.evaluate("[...document.querySelectorAll('.ios-tile')].map(e => Math.round(e.getBoundingClientRect().left))")
            check("tiles sit two across", len(set(cols)) == 2, cols)
            tint = page.evaluate("getComputedStyle(document.querySelector('.ios-card.ios-tint-orange .ios-ring__value')).stroke")
            orange = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--ios-orange').trim()")
            check("a card's tint reaches the ring inside it",
                  tint == "rgb(%d, %d, %d)" % tuple(int(orange[i:i + 2], 16) for i in (1, 3, 5)), (tint, orange))
            check("the carousel can be reached and scrolled from the keyboard",
                  page.get_by_role("region", name="Accounts").get_attribute("tabindex") == "0")

            # Rows: a real button, named "title, value", from the keyboard.
            row = page.get_by_role("button", name="Lunch at Kiln, £18.40")
            check("a tappable row is a button named by its title and value", row.count() == 1)
            row.focus()
            page.keyboard.press("Enter")
            check("Enter on a focused row activates it", "open Lunch at Kiln" in log(), log())

            # Switch: named by its row, Space toggles.
            sw = page.get_by_role("switch", name="Daily nudge")
            check("the switch is a switch named by its row", sw.count() == 1)
            was = sw.is_checked()
            sw.focus()
            page.keyboard.press("Space")
            check("Space toggles the switch", sw.is_checked() != was)

            # Segmented: arrow keys move the selection.
            month = page.get_by_role("radio", name="Month")
            month.focus()
            page.keyboard.press("ArrowLeft")
            check("arrow keys move the segmented selection",
                  page.get_by_role("radio", name="Week").is_checked())

            # Stepper: stops at its bounds.
            dec = page.get_by_role("button", name="Decrease people")
            dec.click()
            check("the stepper stops at its minimum", dec.is_disabled())

            # Slider: arrows step it and the fill follows.
            sl = page.get_by_role("slider", name="Budget used")
            sl.focus()
            page.keyboard.press("ArrowRight")
            fill = sl.evaluate("e => e.style.getPropertyValue('--ios-slider-value')")
            check("arrow keys step the slider and its fill follows",
                  sl.input_value() == "61" and fill.strip() == "61", f"{sl.input_value()} / {fill}")

            # Tabs: arrows, Home/End, roving focus.
            page.get_by_role("tab", name="Expenses").focus()
            page.keyboard.press("ArrowRight")
            check("ArrowRight selects and focuses the next tab",
                  page.get_by_role("tab", name="Budgets").get_attribute("aria-selected") == "true"
                  and active().strip().endswith("Budgets"), active())
            page.keyboard.press("End")
            check("End jumps to the last tab",
                  page.get_by_role("tab", name="Settings").get_attribute("aria-selected") == "true")

            check("axe: no serious or critical issues on the screen", not axe(), axe())
            low = page.evaluate("""async () => (await axe.run(document, {runOnly: ['color-contrast']}))
                .violations.flatMap(v => v.nodes).length""")
            print(f"note {low} elements under 4.5:1 contrast. The kit keeps Apple's light "
                  "palette, which falls short in places; ios-components.css says where")

            # Sheet: opens on the field, traps Tab, Escape closes, focus returns.
            add = page.get_by_role("button", name="Add Expense").first
            add.focus()
            page.keyboard.press("Enter")
            dialog = page.get_by_role("dialog", name="New Expense")
            check("the sheet opens as a dialog named by its title", dialog.count() == 1)
            check("focus starts in the sheet's first field", active() == "Description", active())
            check("the page behind stops scrolling",
                  page.evaluate("document.body.style.overflow") == "hidden")
            inside = True
            for _ in range(6):
                page.keyboard.press("Tab")
                inside &= page.evaluate("!!document.activeElement.closest('[role=dialog]')")
            for _ in range(3):
                page.keyboard.press("Shift+Tab")
                inside &= page.evaluate("!!document.activeElement.closest('[role=dialog]')")
            check("Tab and Shift+Tab stay inside the sheet", inside)
            check("Add is disabled until there's a description",
                  page.get_by_role("button", name="Add", exact=True).is_disabled())
            check("axe: no serious or critical issues with the sheet open", not axe(), axe())
            page.keyboard.press("Escape")
            check("Escape closes the sheet", dialog.count() == 0)
            check("focus returns to what opened the sheet", active() == "Add Expense", active())
            check("scrolling comes back", page.evaluate("document.body.style.overflow") != "hidden")

            add.click()
            page.get_by_role("textbox", name="Description").fill("Coffee")
            page.get_by_role("button", name="Add", exact=True).click()
            check("the sheet's confirm button commits", "added Coffee" in log(), log())

            # Alert: focus on Cancel, Escape is Cancel.
            tram = page.get_by_role("button", name="Monthly tram pass, £42.00")
            tram.focus()
            page.keyboard.press("Enter")
            check("the alert is an alertdialog",
                  page.get_by_role("alertdialog", name="Delete this expense?").count() == 1)
            check("focus starts on Cancel, the safe choice", active() == "Cancel", active())
            check("axe: no serious or critical issues with the alert open", not axe(), axe())
            page.keyboard.press("Escape")
            check("Escape cancels the alert and focus returns to the row",
                  page.get_by_role("alertdialog").count() == 0
                  and active() == "Monthly tram pass, £42.00" and "deleted" not in log(), active())

            # Action sheet.
            page.get_by_role("button", name="Share Report").click()
            check("axe: no serious or critical issues with the action sheet open", not axe(), axe())
            page.get_by_role("button", name="Copy Link").click()
            check("an action sheet choice runs and closes it",
                  "copied" in log() and page.get_by_role("dialog").count() == 0, log())

            # Empty state.
            page.get_by_role("button", name="Toggle Empty").click()
            check("the empty state names its heading and action",
                  page.get_by_role("heading", name="No expenses yet").count() == 1
                  and page.get_by_role("button", name="Add Expense").count() == 2)
            ctx.close()
        browser.close()
    check("no console errors, light or dark", not errors, "; ".join(errors[:3]))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", metavar="DIR", help="keep the built page and screenshots here")
    a = ap.parse_args()
    if not shutil.which("npm"):
        print("needs node and npm; skipped")
        return 0
    install()
    site = a.save or tempfile.mkdtemp(prefix="hig-react-")
    os.makedirs(site, exist_ok=True)
    build(site)
    httpd, url = serve(site)
    try:
        results = run_checks(url, a.save)
    finally:
        httpd.shutdown()
        if not a.save:
            shutil.rmtree(site, ignore_errors=True)
    print(f"\n{sum(results)}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())

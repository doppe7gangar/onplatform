#!/usr/bin/env python3
"""prototype.js opens each row's own record, in a real browser.

A small page with two rows that push one detail screen, a sheet and a
list: tapping each row has to show that row's name, colour, badge and
history, back has to return, and a sheet has to fill from its record.
Then check_design.py has to pass the page's references and fail a
reference to a record that doesn't exist.
"""

import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DESIGN = os.path.join(ROOT, ".claude", "skills", "design-workflow")
FAILED = []

PAGE = """<!doctype html>
<meta charset="utf-8">
<style>[data-screen-id][hidden], [data-sheet-id][hidden] { display: none; }</style>
<div data-state="populated">
<div data-screen-id="list">
  <ul>
    <li class="ios-list__row--tappable" data-push="plant" data-item="plants.fig" id="fig">Fiddle-leaf fig</li>
    <li class="ios-list__row--tappable" data-push="plant" data-item="plants.fern" id="fern">Boston fern</li>
    <li class="ios-list__row--tappable" data-push="plant" data-item='{"name": "Inline palm", "history": []}' id="palm">Palm</li>
  </ul>
  <button data-sheet="edit" data-item="plants.fern" id="edit">Edit</button>
</div>
<div data-screen-id="plant" hidden>
  <button data-back id="back">Back</button>
  <header id="hero" data-field-tint="tint"><h1 data-field="name">Fiddle-leaf fig</h1>
    <span class="badge" data-show="overdue" data-field="overdue">2 days late</span>
    <img data-field-src="photo" data-field-alt="name" alt="" src=""></header>
  <ul data-each="history" id="history">
    <li>31 Oct</li><li>24 Oct</li>
    <template><li><span data-field="date"></span> <span data-field="note"></span></li></template>
  </ul>
</div>
<div data-sheet-id="edit" hidden><input id="nm" data-field-value="name"><span data-field="care.light" id="light"></span></div>
</div>
<script type="application/json" id="prototype-data">
{"plants": {
  "fig":  {"name": "Fiddle-leaf fig", "tint": "rgb(52, 199, 89)", "overdue": "2 days late", "photo": "fig.png",
           "history": [{"date": "31 Oct", "note": "On time"}, {"date": "24 Oct", "note": "On time"}, {"date": "17 Oct", "note": "Late"}]},
  "fern": {"name": "Boston fern", "tint": "rgb(0, 136, 255)", "overdue": "", "photo": "fern.png",
           "care": {"light": "Low"}, "history": [{"date": "2 Nov", "note": "On time"}]}
}}
</script>
<script src="prototype.js"></script>
"""


def c(ok, label, got=""):
    print(f"  {'ok  ' if ok else 'FAIL'} {label}" + ("" if ok else f"  ({got})"))
    if not ok:
        FAILED.append(label)


def main():
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="prototype-")
    try:
        shutil.copy(os.path.join(DESIGN, "prototype.js"), tmp)
        page = os.path.join(tmp, "index.html")
        open(page, "w", encoding="utf-8").write(PAGE)
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            errors = []
            # The fixture's photo names point at nothing; only the script's own errors count.
            pg.on("console", lambda m: errors.append(m.text)
                  if m.type == "error" and "Failed to load resource" not in m.text else None)
            pg.goto("file://" + page)
            text = lambda sel: pg.locator(sel).inner_text()
            visible = lambda sel: pg.locator(sel).is_visible()

            pg.click("#fig")
            c(visible("[data-screen-id=plant]") and not visible("[data-screen-id=list]"), "a row pushes the detail")
            c(text("#hero h1") == "Fiddle-leaf fig", "the detail shows the tapped row's name", text("#hero h1"))
            tint = pg.evaluate("getComputedStyle(document.getElementById('hero')).getPropertyValue('--tint').trim()")
            c(tint == "rgb(52, 199, 89)", "its tint", tint)
            c(visible(".badge") and text(".badge") == "2 days late", "a badge shown when the record has a value")
            c(pg.get_attribute("#hero img", "src") == "fig.png" and pg.get_attribute("#hero img", "alt") == "Fiddle-leaf fig",
              "attributes from the record")
            rows = pg.locator("#history > li").all_inner_texts()
            c(rows == ["31 Oct On time", "24 Oct On time", "17 Oct Late"], "the list repeats per item, replacing the static rows", rows)

            pg.click("#back")
            c(visible("[data-screen-id=list]"), "back returns to the list")
            pg.click("#fern")
            c(text("#hero h1") == "Boston fern", "another row opens its own record", text("#hero h1"))
            c(not visible(".badge"), "the badge hides when the record's value is empty")
            rows = pg.locator("#history > li").all_inner_texts()
            c(rows == ["2 Nov On time"], "and its own history, with the last one's rows gone", rows)

            pg.click("#back")
            pg.click("#palm")
            c(text("#hero h1") == "Inline palm" and pg.locator("#history > li").count() == 0,
              "an inline record, and an empty list")

            pg.click("#back")
            pg.click("#edit")
            c(pg.input_value("#nm") == "Boston fern" and text("#light") == "Low", "a sheet fills from its record, paths included")
            c(not errors, "no console errors", errors)
            b.close()

        check = os.path.join(DESIGN, "check_design.py")
        out = subprocess.run([sys.executable, check, tmp, "--no-browser"], capture_output=True, text=True).stdout
        c("every data-item names a record" in out, "check_design accepts the references", out[-400:])
        open(page, "w", encoding="utf-8").write(PAGE.replace('data-item="plants.fern" id="fern"', 'data-item="plants.ferm" id="fern"'))
        out = subprocess.run([sys.executable, check, tmp, "--no-browser"], capture_output=True, text=True).stdout
        c("plants.ferm" in out and "isn't in" in out, "and fails a record that isn't there", out[-400:])
        open(page, "w", encoding="utf-8").write(PAGE.replace(' data-item="plants.fig"', "").replace(' data-item="plants.fern"', "")
                                                .replace(""" data-item='{"name": "Inline palm", "history": []}'""", ""))
        out = subprocess.run([sys.executable, check, tmp, "--no-browser"], capture_output=True, text=True).stdout
        c("every one shows the same content" in out, "and warns when every row opens the same thing", out[-400:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if FAILED:
        print(f"\n{len(FAILED)} failed")
        return 1
    print("\nall passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

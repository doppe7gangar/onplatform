#!/usr/bin/env python3
"""stress_test.py passes the starters and catches each thing it looks for.

Scaffolds an iPhone, iPad, Mac and Android design and requires each to
come through the largest text, right to left and long text with no
failure. Then plants in the iPhone design: a box that fits one line at
the default size, text set in pixels, two labels placed side by side
that collide once the text grows, a fixed-width label that long text
overflows, and a chevron named for a fixed direction -- and requires
each to be reported, under the right condition.
"""

import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DESIGN = os.path.join(ROOT, ".claude", "skills", "design-workflow")
FAILED = []

SEEDS = """
        <p id="seed-box" style="height:24px;overflow:hidden;margin:8px 4px;font:var(--ios-text-body)">Fits at the default size</p>
        <p style="font-size:15px;margin:8px 4px">A note in fixed pixels</p>
        <div style="position:relative;height:30px;margin:8px 4px">
          <span style="position:absolute;left:0;font:var(--ios-text-body)">Left label</span>
          <span style="position:absolute;left:150px;font:var(--ios-text-body)">Right label</span></div>
        <span style="display:inline-block;width:150px;white-space:nowrap;overflow:hidden;margin:0 4px;font:var(--ios-text-body)">Water all now</span>
        <span data-sf-symbol="chevron.right" style="display:inline-block">›</span>
        <span data-sf-symbol="chevron.backward" style="display:inline-block">‹</span>
"""


def c(ok, label, got=""):
    print(f"  {'ok  ' if ok else 'FAIL'} {label}" + ("" if ok else f"\n       {got[-900:]}"))
    if not ok:
        FAILED.append(label)


def stress(path):
    p = subprocess.run([sys.executable, os.path.join(DESIGN, "stress_test.py"), path],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    tmp = tempfile.mkdtemp(prefix="stress-")
    try:
        for kind, model in (("ios", "tabs"), ("ipados", "sidebar"), ("macos", "sidebar"), ("android", "tabs")):
            out = os.path.join(tmp, kind)
            subprocess.run([sys.executable, os.path.join(DESIGN, "new_project.py"), "--name", "Supper",
                            "--brand", "#C1552E", "--kind", kind, "--model", model,
                            "--screens", "Tonight,Recipes", "--thing", "recipes", "-o", out],
                           check=True, capture_output=True)
            code, log = stress(out)
            c(code == 0, f"the {kind} starter comes through with no failure", log)
        ios = os.path.join(tmp, "ios")
        c(os.path.exists(os.path.join(ios, "STRESS_TEST.md")) and
          os.path.exists(os.path.join(ios, ".visual-review", "stress", "text-screen-tonight.png")),
          "it writes STRESS_TEST.md and a screenshot per condition and screen")

        page = os.path.join(ios, "index.html")
        html = open(page, encoding="utf-8").read()
        marker = '<p class="sectionhead">Today'
        assert marker in html
        open(page, "w", encoding="utf-8").write(html.replace(marker, SEEDS + marker, 1))
        code, log = stress(ios)
        c(code == 1, "a planted breakage fails the run", log)
        lines = log.splitlines()
        has = lambda cond, *words: any(l.strip().startswith(("FAIL " + cond, "warn " + cond))
                                       and all(w in l for w in words) for l in lines)
        c(has("text", "cut off", "Fits at the default size"), "large text: a one-line box cuts its text off", log)
        c(has("text", "now overlap", "Left label", "Right label"), "large text: labels side by side collide", log)
        c(has("text", "don't grow", "A note in fixed pixels"), "large text: text in pixels doesn't grow", log)
        c(not has("base") and not has("text", "Sheet-pan chicken"), "the starter's own text isn't reported", log)
        c(has("long", "cut off", "Wat"), "long text: a fixed-width label overflows", log)
        c(not has("rtl", "cut off"), "right to left: nothing is cut off", log)
        c(has("rtl", "fixed direction", "chevron.right"), "right to left: chevron.right is named for one direction", log)
        c(not has("rtl", "chevron.backward"), "right to left: chevron.backward mirrors, as SF Symbols does", log)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if FAILED:
        print(f"\n{len(FAILED)} failed")
        return 1
    print("\nall passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

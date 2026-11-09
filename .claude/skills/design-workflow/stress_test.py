#!/usr/bin/env python3
"""Put a design through what real use does to it, before a reviewer does.

A design is drawn at the default text size, in English, left to right,
and that is the one condition it is never used in for long. Three more:

  text   the largest text the platform's own setting reaches before it
         asks for its accessibility sizes in earnest: iOS's AX3 (body at
         40pt, 235%), Android's 200% font scale. Not run on a Mac, which
         has no system-wide text size.
  rtl    right to left, as in Arabic or Hebrew: the layout mirrors, and
         symbols that point along the line have to mirror with it.
  long   every string 40% longer, words included -- German and Finnish
         run that much longer than English, in single words that don't
         wrap.

Every screen and sheet is rendered in each, and what breaks is measured:
text cut off, text running off the screen, text overlapping text it
didn't overlap before, the page scrolling sideways (failures); text
truncated with an ellipsis, text that doesn't grow with the text size,
and arrows that don't turn round (warnings). Screenshots of every
render go to .visual-review/stress/ to look at, and the findings to
STRESS_TEST.md.

    python3 stress_test.py ./design
    python3 stress_test.py ./design --only rtl,long
    python3 stress_test.py ./design --text-scale 3.12      # iOS's AX5

Exit status 1 means something broke.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_design  # noqa: E402  (platform detection, browser path)

# Bars don't scale with text on either platform -- iOS shows the large
# content viewer on a long press instead -- and the status bar never does.
BARS = (".ios-tabbar, .ios-navbar, .ipad-tabbar, .ipad-statusbar, .ios-statusbar, .m3-statusbar, "
        ".m3-navbar, .m3-navrail, .m3-topappbar, .mac-toolbar, .mac-sidebar, .proto-toast, .demo__bar")

# For the screenshot only: the frame grows to its content's height.
EXPAND_CSS = (".device, .ipad, .mac-window, .m3-device { height: auto !important; max-height: none !important; }"
              ".phone, .ios-body, .m3-body, .ipad-content, .ipad-body, .mac-content, .mac-main"
              " { overflow: visible !important; height: auto !important; max-height: none !important; flex: none !important; }")

SETUP_JS = """([cond, scale]) => {
  const de = document.documentElement;
  if (cond === 'text') de.style.fontSize = (16 * scale) + 'px';
  if (cond === 'rtl') { de.dir = 'rtl'; de.lang = 'ar'; }
  if (cond === 'long') {
    const skip = n => n.parentElement && n.parentElement.closest(
        'script, style, template, [aria-hidden="true"], .ios-statusbar, .ipad-statusbar, .m3-statusbar, .demo__bar');
    const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walk.nextNode()) nodes.push(walk.currentNode);
    for (const n of nodes) {
      if (!n.textContent.trim() || skip(n)) continue;
      // Each word grows by 40% of itself, so the expansion lands inside
      // words that can't break, the way a compound noun does.
      n.textContent = n.textContent.replace(/[\\p{L}]{2,}/gu,
        w => w + w.slice(0, Math.ceil(w.length * 0.4)).toLowerCase());
    }
  }
  const root = document.querySelector('[data-state]');
  if (root) root.dataset.state = 'populated';
}"""

TARGETS_JS = """() => ({
  screens: [...document.querySelectorAll('[data-screen-id]')].map(e => e.getAttribute('data-screen-id')),
  sheets: [...document.querySelectorAll('[data-sheet-id]')].map(e => e.getAttribute('data-sheet-id')),
})"""

SHOW_JS = """([kind, id]) => {
  document.querySelectorAll('[data-sheet-id]').forEach(s => { s.hidden = true; });
  if (kind === 'screen' && id) {
    const t = document.querySelector('[data-screen-id="' + id + '"]');
    let n = t;
    // Show it and every screen it sits inside, hiding their siblings.
    while (n) {
      if (n.hasAttribute && n.hasAttribute('data-screen-id')) {
        [...n.parentElement.children].forEach(c => {
          if (c !== n && c.hasAttribute('data-screen-id')) c.hidden = true; });
        n.hidden = false;
      }
      n = n.parentElement;
    }
  }
  if (kind === 'sheet') {
    const s = document.querySelector('[data-sheet-id="' + id + '"]');
    if (s) s.hidden = false;
  }
  document.querySelectorAll('.phone, .ios-body, .m3-body, .ipad-content, .mac-content')
    .forEach(s => { s.scrollTop = 0; });
}"""

MEASURE_JS = r"""([bars]) => {
  const all = [...document.querySelectorAll('*')];
  const index = new Map(all.map((e, i) => [e, i]));
  const box = e => {
    let L = Infinity, T = Infinity, R = -Infinity, B = -Infinity;
    for (const n of e.childNodes) {
      if (n.nodeType !== 3 || !n.textContent.trim()) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      for (const r of rg.getClientRects()) {
        if (!r.width || !r.height) continue;
        L = Math.min(L, r.left); T = Math.min(T, r.top); R = Math.max(R, r.right); B = Math.max(B, r.bottom);
      }
    }
    return R > L ? {l: L, t: T, r: R, b: B} : null;
  };
  const scrollsX = e => /(auto|scroll)/.test(getComputedStyle(e).overflowX);
  const clips = (e, axis) => {
    const o = getComputedStyle(e)[axis === 'x' ? 'overflowX' : 'overflowY'];
    return o === 'hidden' || o === 'clip';
  };
  const texts = [];
  for (const e of all) {
    if (/^(SCRIPT|STYLE|TEMPLATE|TITLE|HEAD|OPTION)$/.test(e.tagName)) continue;
    if (!e.getClientRects().length || e.closest('[aria-hidden="true"]')) continue;
    if (getComputedStyle(e).visibility === 'hidden' || +getComputedStyle(e).opacity === 0) continue;
    let b = box(e);
    if (!b) continue;
    const cs = getComputedStyle(e);
    // A truncated run's range still measures the hidden text: what shows
    // is what its own box lets through.
    if (clips(e, 'x') || clips(e, 'y')) {
      const r = e.getBoundingClientRect();
      b = {l: Math.max(b.l, r.left), t: Math.max(b.t, r.top), r: Math.min(b.r, r.right), b: Math.min(b.b, r.bottom)};
    }
    const frame = e.closest('.device, .ipad, .mac-window, .m3-device');
    const fr = frame ? frame.getBoundingClientRect() : {left: 0, right: innerWidth};
    const inScroller = (() => { for (let n = e.parentElement; n && n !== frame; n = n.parentElement)
      if (scrollsX(n) && n.scrollWidth > n.clientWidth + 1) return true; return false; })();
    // Cut off by its own box or by an ancestor that hides what overflows.
    let cut = null;
    const own = (clips(e, 'x') && e.scrollWidth > e.clientWidth + 1) ||
                (clips(e, 'y') && e.scrollHeight > e.clientHeight + 2);
    const ellipsis = own && cs.textOverflow === 'ellipsis';
    if (own && !ellipsis) cut = 'its own box';
    if (!cut) for (let n = e.parentElement; n && n !== document.body; n = n.parentElement) {
      if (scrollsX(n) || /(auto|scroll)/.test(getComputedStyle(n).overflowY)) break;
      const r = n.getBoundingClientRect();
      if ((clips(n, 'x') && (b.r > r.right + 1 || b.l < r.left - 1)) ||
          (clips(n, 'y') && (b.b > r.bottom + 2 || b.t < r.top - 2))) {
        cut = (n.className && n.className.baseVal === undefined ? String(n.className).split(' ')[0] : '') || n.tagName.toLowerCase();
        break;
      }
    }
    texts.push({i: index.get(e), t: e.textContent.trim().replace(/\s+/g, ' ').slice(0, 40),
      b, fs: parseFloat(cs.fontSize), bar: !!e.closest(bars),
      cut, ellipsis, off: !inScroller && (b.r > fr.right + 1 || b.l < fr.left - 1)});
  }
  const overlaps = [];
  const free = texts.filter(x => !x.bar);
  for (let a = 0; a < free.length; a++) for (let c = a + 1; c < free.length; c++) {
    const p = free[a], q = free[c];
    const ea = all[p.i], eb = all[q.i];
    if (ea.contains(eb) || eb.contains(ea)) continue;
    const w = Math.min(p.b.r, q.b.r) - Math.max(p.b.l, q.b.l);
    const h = Math.min(p.b.b, q.b.b) - Math.max(p.b.t, q.b.t);
    if (w > 2 && h > 2) overlaps.push([p.i, q.i]);
  }
  const directional = [];
  for (const e of document.querySelectorAll('[data-sf-symbol], [data-icon]')) {
    if (!e.getClientRects().length || e.closest('[hidden]')) continue;
    const name = e.getAttribute('data-sf-symbol') || e.getAttribute('data-icon');
    const fixed = /(^|\.)(left|right)(\.|$)/.test(name) && e.hasAttribute('data-sf-symbol');
    const turns = /\.(backward|forward|leading|trailing)(\.|$)/.test(name) ||
      /^(arrow_back|arrow_forward|arrow_back_ios|arrow_forward_ios|chevron_left|chevron_right|navigate_before|navigate_next|send|reply|undo|redo)$/.test(name);
    let mirrored = false;
    for (let n = e, k = 0; n && k < 3; n = n.parentElement, k++) {
      const m = getComputedStyle(n).transform;
      if (m && m !== 'none' && parseFloat(m.replace(/^matrix\(/, '')) < 0) { mirrored = true; break; }
    }
    if (fixed || (turns && !mirrored)) directional.push({name, fixed});
  }
  const se = document.scrollingElement;
  return {overflow: Math.max(0, se.scrollWidth - innerWidth), texts, overlaps, directional};
}"""


def platform(path, html):
    if check_design.is_mac(path, html):
        return "mac", (1280, 800), None
    if check_design.is_ipad(path, html):
        return "ipad", (1180, 820), 2.35
    if check_design.is_android(path, html):
        return "android", (412, 915), 2.0
    return "iphone", (390, 844), 2.35


def run(root, only, scale_override):
    from playwright.sync_api import sync_playwright
    page = os.path.join(root, "index.html")
    html = open(page, encoding="utf-8", errors="replace").read()
    plat, (w, h), scale = platform(page, html)
    if scale_override:
        scale = scale_override
    conds = [c for c in ("text", "rtl", "long") if c in only and not (c == "text" and scale is None)]
    out = os.path.join(root, ".visual-review", "stress")
    os.makedirs(out, exist_ok=True)
    url = "file://" + os.path.abspath(page) + "?state=populated"
    findings = []          # (severity, condition, where, message)
    shots = []

    launch = {"args": ["--no-sandbox"]}
    exe = check_design.chrome_path()
    if exe:
        launch["executable_path"] = exe
    with sync_playwright() as p:
        b = p.chromium.launch(**launch)

        def render(cond):
            pg = b.new_page(viewport={"width": w, "height": h}, color_scheme="light")
            pg.goto(url, wait_until="load")
            pg.wait_for_timeout(200)
            if cond != "base":
                pg.evaluate(SETUP_JS, [cond, scale or 1])
                pg.wait_for_timeout(120)
            return pg

        probe = render("base")
        targets = probe.evaluate(TARGETS_JS)
        probe.close()
        places = [("screen", s) for s in targets["screens"]] or [("screen", None)]
        places += [("sheet", s) for s in targets["sheets"]]

        base = {}
        pg = render("base")
        for kind, ident in places:
            pg.evaluate(SHOW_JS, [kind, ident])
            pg.wait_for_timeout(60)
            base[(kind, ident)] = pg.evaluate(MEASURE_JS, [BARS])
        pg.close()

        for cond in conds:
            pg = render(cond)
            for kind, ident in places:
                pg.evaluate(SHOW_JS, [kind, ident])
                pg.wait_for_timeout(80)
                m = pg.evaluate(MEASURE_JS, [BARS])
                where = (f"sheet {ident}" if kind == "sheet" else f"screen {ident}" if ident else "the page")
                shot = f"{cond}-{kind}-{ident or 'page'}.png"
                # The screenshot runs the screen's whole length: what breaks
                # at large text is mostly below the first screenful.
                tall = pg.add_style_tag(content=EXPAND_CSS) if kind == "screen" else None
                pg.wait_for_timeout(60)
                frame = pg.query_selector(".m3-sheet, .ios-sheet, .ipad-sheet, .mac-sheet") if kind == "sheet" else None
                frame = frame or pg.query_selector(".device, .ipad, .mac-window, .m3-device")
                (frame or pg).screenshot(path=os.path.join(out, shot), **({} if frame else {"full_page": True}))
                if tall:
                    tall.evaluate("e => e.remove()")
                shots.append(shot)
                was = base[(kind, ident)]
                if m["overflow"] > 1:
                    findings.append(("FAIL", cond, where, f"the page scrolls sideways by {m['overflow']}px"))
                cut = [t for t in m["texts"] if t["cut"]]
                if cut:
                    findings.append(("FAIL", cond, where, f"{len(cut)} text run(s) cut off: " + "; ".join(
                        f"\"{t['t']}\" by {t['cut']}" for t in cut[:4])))
                off = [t for t in m["texts"] if t["off"] and not t["cut"]]
                if off:
                    findings.append(("FAIL", cond, where, f"{len(off)} text run(s) run off the screen: " + "; ".join(
                        f"\"{t['t']}\"" for t in off[:4])))
                before = {tuple(x) for x in was["overlaps"]}
                label = {t["i"]: t["t"] for t in m["texts"]}
                new = [x for x in m["overlaps"] if tuple(x) not in before]
                if new:
                    findings.append(("FAIL", cond, where, f"{len(new)} pair(s) of text now overlap: " + "; ".join(
                        f"\"{label.get(a, '?')}\" and \"{label.get(c, '?')}\"" for a, c in new[:3])))
                trunc = [t for t in m["texts"] if t["ellipsis"]]
                if trunc:
                    findings.append(("warn", cond, where, f"{len(trunc)} text run(s) truncated with an ellipsis: " +
                                     "; ".join(f"\"{t['t']}\"" for t in trunc[:4])))
                if cond == "text":
                    fs0 = {t["i"]: t["fs"] for t in was["texts"]}
                    still = [t for t in m["texts"] if not t["bar"] and t["i"] in fs0
                             and t["fs"] < fs0[t["i"]] * 1.2]
                    if still:
                        findings.append(("warn", cond, where, f"{len(still)} text run(s) don't grow with the text "
                                         "size -- set in px rather than the type tokens: " +
                                         "; ".join(f"\"{t['t']}\" {t['fs']:.0f}px" for t in still[:4])))
                if cond == "rtl" and m["directional"]:
                    fixed = sorted({d["name"] for d in m["directional"] if d["fixed"]})
                    stuck = sorted({d["name"] for d in m["directional"] if not d["fixed"]})
                    if fixed:
                        findings.append(("warn", cond, where, "symbols named for a fixed direction, which "
                                         "won't turn round in a right-to-left language: " + ", ".join(fixed) +
                                         ". Use the .backward / .forward or .leading / .trailing names."))
                    if stuck:
                        findings.append(("warn", cond, where, "symbols that should mirror and don't: " +
                                         ", ".join(stuck) + ". Load the kit's stylesheet, which mirrors them."))
            pg.close()
        b.close()
    # The same symbol reported on every screen is one finding.
    seen, uniq = set(), []
    for f in findings:
        key = (f[0], f[1], f[3]) if "symbols" in f[3] else f
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return plat, scale, conds, uniq, shots


def report(root, plat, scale, conds, findings, shots):
    names = {"text": f"Text at {scale * 100:.0f}%" if scale else "Text", "rtl": "Right to left",
             "long": "Long text"}
    lines = ["# Stress test", "",
             f"Every screen and sheet of this {plat} design, rendered " +
             ", ".join({"text": f"at {scale * 100:.0f}% text" if scale else "",
                        "rtl": "right to left", "long": "with every string 40% longer"}[c] for c in conds) +
             ". Generated by stress_test.py; look at the screenshots too.", "",
             "| | " + " | ".join(names[c] for c in conds) + " |",
             "|---|" + "---|" * len(conds),
             "| Failures | " + " | ".join(str(sum(1 for f in findings if f[0] == "FAIL" and f[1] == c)) for c in conds) + " |",
             "| Warnings | " + " | ".join(str(sum(1 for f in findings if f[0] == "warn" and f[1] == c)) for c in conds) + " |",
             "", "## Findings", ""]
    lines += [f"- **{'Fails' if s == 'FAIL' else 'Warning'}** · {names[c]} · {where}: {msg}"
              for s, c, where, msg in findings] or ["Nothing broke."]
    lines += ["", "## Screenshots", ""] + [f"- `.visual-review/stress/{s}`" for s in shots]
    with open(os.path.join(root, "STRESS_TEST.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("design", nargs="?", default="design")
    ap.add_argument("--only", default="text,rtl,long", help="conditions to run: text, rtl, long")
    ap.add_argument("--text-scale", type=float, help="text size multiple (iOS AX3 2.35, AX5 3.12; Android 2.0)")
    a = ap.parse_args()
    root = os.path.abspath(a.design)
    if not os.path.isfile(os.path.join(root, "index.html")):
        sys.exit(f"no index.html in {a.design}")
    try:
        plat, scale, conds, findings, shots = run(root, {c.strip() for c in a.only.split(",")}, a.text_scale)
    except ImportError:
        sys.exit("needs playwright: pip install playwright && playwright install chromium")
    report(root, plat, scale, conds, findings, shots)
    for s, c, where, msg in findings:
        print(f"  {'FAIL' if s == 'FAIL' else 'warn'} {c} · {where}: {msg}")
    fails = sum(1 for f in findings if f[0] == "FAIL")
    print(f"\n{len(shots)} renders, {fails} failure(s), {len(findings) - fails} warning(s); "
          f"STRESS_TEST.md and .visual-review/stress/")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

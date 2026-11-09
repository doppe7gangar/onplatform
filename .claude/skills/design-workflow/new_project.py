#!/usr/bin/env python3
"""Scaffold a working design project without choosing its composition by accident.

The generator owns infrastructure:
- vendored fonts and measured UI-kit files
- brand theme + --ios-* bridge
- reachable populated/loading/empty/error states
- a starter composition chosen explicitly by spatial model

It does not own art direction. The caller chooses the spatial model after the
product hierarchy is understood. Web projects therefore require --model
instead of silently defaulting to "sidebar + cards".
"""

import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.dirname(HERE)
KIT = os.path.join(SKILLS, "ui-kit-for-apple-platforms")
ANDROID_KIT = os.path.join(SKILLS, "ui-kit-for-android")

sys.path.insert(0, HERE)
import build_theme  # noqa: E402


HEAD = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__NAME__</title>

<!-- Order is load-bearing: fonts, measured tokens, component recipes,
     then the brand theme LAST so its bridge wins. -->
<link rel="stylesheet" href="vendor/fonts/inter.css">
<link rel="stylesheet" href="vendor/ios-tokens.css">
<link rel="stylesheet" href="vendor/ios-components.css">
<link rel="stylesheet" href="theme.css">
"""

STATE_CSS = """
  /* Screens and sheets prototype.js switches between. A kit's own display
     rule would otherwise beat the hidden attribute. The iPhone's screen
     wrapper takes no box of its own, so the bars keep their layout. */
  [data-screen-id][hidden], [data-sheet-id][hidden] { display: none !important; }
  .tabscreen { display: contents; }
  .demo { min-height: 100vh; display: flex; flex-direction: column;
          background: var(--ios-bg); color: var(--ios-label);
          font: var(--ios-text-body); }
  .demo > :not(.demo__bar) { flex: 1; min-height: 0; }
  .demo__bar { display: flex; gap: 6px; flex-wrap: wrap; padding: 10px 16px;
               border-bottom: 1px solid var(--ios-separator);
               background: var(--ios-bg-card); }
  .demo__bar button { min-height: 32px; padding: 6px 12px; border-radius: 999px;
                      border: 1px solid var(--ios-separator); background: transparent;
                      color: var(--ios-label-secondary); cursor: pointer;
                      font: var(--ios-text-footnote); }
  .demo__bar button[aria-pressed="true"] {
      background: color-mix(in srgb, var(--ios-accent) 16%, transparent);
      border-color: color-mix(in srgb, var(--ios-accent) 45%, transparent);
      color: var(--ios-label); font-weight: 590; }

  /* Any button that is not filled is accent-coloured *text* -- plain,
     tinted, a bare navigation-bar action -- so it needs 4.5:1, while
     --ios-accent is tuned for the 3:1 a fill needs. Scoping this to
     --tinted alone left a navigation-bar "+" at 3.73:1 on a dark brand.
     Shared, so a new spatial model cannot be written without it. */
  .ios-btn:not(.ios-btn--filled):not(.ios-btn--destructive) {
      color: var(--accent-text-safe); }
  /* And a filled button takes the label the contrast pass chose, rather
     than the kit's hard-coded white. */
  .ios-btn--filled:not(.ios-btn--destructive) { color: var(--ios-on-accent); }

  .state { display: none; }
  [data-state="populated"] .state--populated,
  [data-state="loading"] .state--loading,
  [data-state="empty"] .state--empty,
  [data-state="error"] .state--error { display: block; }

  .skel { height: 1em; border-radius: 6px; background: var(--ios-fill-control);
          animation: skel 1.4s ease-in-out infinite; }
  @keyframes skel { 0%,100% { opacity: .55 } 50% { opacity: .25 } }
  @media (prefers-reduced-motion: reduce) { .skel { animation: none; } }

  .unavailable { max-width: 460px; margin: 0 auto; padding: 72px 28px;
                 text-align: center; }
  .unavailable__glyph { font-size: 42px; line-height: 1;
                        color: var(--ios-label-tertiary); }
  .unavailable__title { margin: 14px 0 5px; font: var(--ios-text-headline); }
  .unavailable__body { max-width: 34ch; margin: 0 auto 20px;
                       color: var(--ios-label-secondary);
                       font: var(--ios-text-subhead); }
"""

STATE_JS = """
<script>
  // The large title collapses into the bar on scroll, the way the
  // platform does it. Shown rather than described, because "it
  // collapses" is the sort of claim a static mockup makes and never has
  // to honour.
  for (const ph of document.querySelectorAll('.phone')) {
    const dev = ph.closest('.device');
    if (!dev) continue;
    const sync = () => { dev.dataset.scrolled = ph.scrollTop > 24 ? '1' : '0'; };
    ph.addEventListener('scroll', sync, {passive: true});
    sync();
  }

  const root = document.querySelector('[data-state]');
  const initial = new URLSearchParams(location.search).get('state');
  if (initial) root.dataset.state = initial;
  for (const b of document.querySelectorAll('.demo__bar button')) {
    b.addEventListener('click', () => {
      root.dataset.state = b.dataset.set;
      for (const o of document.querySelectorAll('.demo__bar button'))
        o.setAttribute('aria-pressed', String(o === b));
    });
    b.setAttribute('aria-pressed', String(b.dataset.set === root.dataset.state));
  }
</script>
"""

SWITCHER = """<div class="demo__bar" role="group" aria-label="Preview state">
  <button data-set="populated">Populated</button>
  <button data-set="loading">Loading</button>
  <button data-set="empty">Empty</button>
  <button data-set="error">Error</button>
</div>"""

EMPTY_PANEL = """      <section class="state state--empty">
        <div class="ios-empty">
          <div class="ios-empty__glyph" data-sf-symbol="tray"
               aria-hidden="true">
            <svg viewBox="0 0 24 24" width="38" height="38" fill="none"
                 stroke="currentColor" stroke-width="1.4" stroke-linecap="round"
                 stroke-linejoin="round"><path d="M3 13h5l2 3h4l2-3h5"/><path d="M5 5l-2 8v5a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1v-5l-2-8z"/></svg>
          </div>
          <h2 class="ios-empty__title">No __THING__ yet</h2>
          <p class="ios-empty__body">__EMPTY_BODY__</p>
          <button class="ios-btn ios-btn--filled ios-empty__action">__EMPTY_CTA__</button>
        </div>
      </section>
"""

ERROR_PANEL = """      <section class="state state--error">
        <div class="ios-empty">
          <div class="ios-empty__glyph" data-sf-symbol="exclamationmark.triangle"
               aria-hidden="true">
            <svg viewBox="0 0 24 24" width="38" height="38" fill="none"
                 stroke="currentColor" stroke-width="1.4" stroke-linecap="round"
                 stroke-linejoin="round"><path d="M12 3 2 20h20z"/><path d="M12 9v5m0 3v.5"/></svg>
          </div>
          <h2 class="ios-empty__title">Couldn't load __THING__</h2>
          <p class="ios-empty__body">Check your connection and try again.</p>
          <button class="ios-btn ios-btn--filled ios-empty__action">Try Again</button>
        </div>
      </section>
"""


# ---------------------------------------------------------------- iOS

IOS_CSS = """
  /* The deliverable is an app screen, not a board of artboards. The same
     markup shown as a stack of panels with commentary between them reads
     as a specification; shown once, in a device, with a status bar, it
     reads as the product. Nothing about the design changes -- only what
     a reviewer is looking at, which turned out to be a large share of
     why finished work did not look like iOS. The commentary belongs in
     DESIGN.md, where it already lives. */
  .stage { min-height: 100vh; display: grid; place-items: center;
           padding: 32px 16px; background: #0E0E10; }
  /* The iPhone in Apple's iOS 27 kit: 402 x 874 with 50pt corners. */
  .device { width: 402px; max-width: 100%; height: 874px; position: relative;
            display: flex; flex-direction: column; overflow: hidden;
            border-radius: 50px; background: var(--ios-bg);
            box-shadow: 0 0 0 11px #1C1C1E, 0 0 0 13px #3A3A3C,
                        0 26px 60px rgba(0,0,0,.45); }
  .phone { flex: 1; min-height: 0; width: 100%; display: flex;
           flex-direction: column; background: var(--ios-bg);
           overflow-y: auto; }
  @media (max-width: 460px) {
    /* On a phone the bezel goes -- a phone drawn inside a phone is a
       costume -- but the screen keeps its status bar, Dynamic Island
       and home indicator. Without them the same design read as a web
       page: those three are most of what says "iPhone app" at a glance,
       in a preview pane, a screenshot or a phone's browser. */
    .stage { padding: 0; background: var(--ios-bg); place-items: stretch; }
    .device { width: 100%; height: 100vh; height: 100dvh; border-radius: 0; box-shadow: none; }
  }
  /* Opened from the Home Screen it is the app itself, and the real
     status bar is already there. */
  @media (display-mode: standalone) { .ios-statusbar { display: none; } }
  .screen { flex: 1; padding: 16px var(--ios-gutter, 16px) 88px; }
  /* The kit's 11px row padding is measured for a text row: a 22px line
     box plus 11 above and below is exactly the 44pt target. A 29px icon
     does not fit that arithmetic and pushed every row to 51. iOS keeps
     the row at 44 and lets the icon take the padding, so the row with
     an icon gets 7px and lands back on the measured height. */
  .ios-list__row:has(.rowicon) { padding-top: 7px; padding-bottom: 7px; }
  /* A tinted symbol on nothing, which is what Apple's rows carry --
     Tips, Maps, Health all show a coloured glyph with no plate behind
     it. A filled tile with a letter in it is a Notion habit and reads
     as one. Replace the glyph with the real symbol when you have it. */
  .rowicon { width: 29px; height: 29px; flex: none; display: grid;
             place-items: center; color: var(--accent-text-safe);
             font: var(--ios-text-title3); }
  /* iOS 26 sets a section header as a title, not as a caption: 22pt
     bold, primary label, sentence case. The small uppercase grey
     footnote is the previous generation's grouped-list header -- see
     Tips ("Get Started", "Next Steps") and Pages ("Included with Apple
     Creator Studio"), all large and white. Getting this wrong makes a
     screen read as a settings pane whatever else is right. */
  .sectionhead { display: flex; align-items: baseline;
                 justify-content: space-between; gap: 12px;
                 margin: 22px 4px 8px; color: var(--ios-label);
                 font: var(--ios-text-title2);
                 font-weight: var(--ios-weight-bold);
                 letter-spacing: var(--ios-track-title2); }
  /* Apple pairs the header with an accent action rather than burying the
     rest of the list behind a chevron on the last row. */
  .sectionhead__action { font: var(--ios-text-body);
                         font-weight: var(--ios-weight-regular);
                         color: var(--accent-text-safe);
                         text-decoration: none;
                         /* An inline link is 15px tall and reads as text
                            rather than a control. Padded to the target
                            and pulled back out with a negative margin so
                            the baseline still lines up with the title. */
                         display: inline-flex; align-items: center;
                         min-height: var(--ios-hit-target);
                         padding: 0 4px; margin: -14px -4px; }
  /* The large title is the most recognisable thing about an iOS screen
     and the scaffold did not have one: a 17pt headline in the bar is the
     *collapsed* state, which is what you see after scrolling, not what a
     screen opens as. 34pt bold, left, under the bar, with the compact
     title in the bar hidden until it is earned. Real iOS swaps them on
     scroll; the script below does that so the collapse is visible rather
     than described. */
  /* At rest the bar carries no material: the large title is the screen's
     title and the area above it is just background, which is why Calendar
     and Health show content running straight up to the status bar. The
     kit's .ios-navbar brings in the scroll edge effect once the script
     below marks the device scrolled, together with the compact title. */
  .ios-navbar { padding-top: 6px; padding-bottom: 6px; }
  /* Calendar and Pages float their actions rather than seating them in a
     bar: the capsule carries the material, the bar behind it is only
     there to hold the compact title once the large one has gone. */
  .ios-navbar .ios-controls { margin-left: auto; }
  .ios-navbar__title { opacity: 0; transition: opacity .18s ease; }
  .device[data-scrolled="1"] .ios-navbar__title { opacity: 1; }
  /* The kit's large title (ios-largetitle) sets the type and spacing,
     measured from Apple's example screens. Lists sit 4pt inside the
     screen's 16pt gutter: Apple's 20pt inset. */
  .ios-list { margin: 0 4px 22px; }
  .ios-tabbar__item[aria-selected="true"] { color: var(--accent-text-safe); }
  /* A screen that opens on a picture (.ios-headerhero) runs it up under
     the status bar, which turns white over it. */
  .device:has(.tabscreen:not([hidden]) > .ios-headerhero) .ios-statusbar,
  .device:has([data-screen-id]:not([hidden]) > .ios-headerhero) .ios-statusbar {
      position: absolute; top: 0; left: 0; right: 0; z-index: 4; color: #fff; }
  .ios-hero + .ios-card { margin-top: 12px; }
"""

IOS_BODY = """<div class="demo">
__SWITCHER__
 <div class="stage">
  <div class="device" data-state="populated">
   <div class="ios-statusbar" aria-hidden="true">
     <span>9:41</span>
     <span class="ios-statusbar__island"></span>
     <span class="ios-statusbar__indicators">
       <svg width="19" height="13" viewBox="0 0 19 13" fill="currentColor"
            data-sf-symbol="cellularbars" aria-hidden="true">
         <rect x="0"  y="9"   width="3" height="4"  rx="1"/>
         <rect x="5"  y="6.5" width="3" height="6.5" rx="1"/>
         <rect x="10" y="3.5" width="3" height="9.5" rx="1"/>
         <rect x="15" y="0"   width="3" height="13" rx="1"/>
       </svg>
       <svg width="17" height="13" viewBox="0 0 17 13" fill="none"
            stroke="currentColor" stroke-linecap="round"
            data-sf-symbol="wifi" aria-hidden="true">
         <path d="M1.4 4.6a10 10 0 0 1 14.2 0" stroke-width="2.1"/>
         <path d="M4.4 7.9a5.8 5.8 0 0 1 8.2 0" stroke-width="2.1"/>
         <circle cx="8.5" cy="11.3" r="1.5" fill="currentColor" stroke="none"/>
       </svg>
       <svg width="27" height="13" viewBox="0 0 27 13"
            data-sf-symbol="battery.75" aria-hidden="true">
         <rect x="0.6" y="0.6" width="23.3" height="11.8" rx="3.8"
               fill="none" stroke="currentColor" stroke-opacity=".38"
               stroke-width="1.1"/>
         <rect x="2.2" y="2.2" width="16" height="8.6" rx="2.4"
               fill="currentColor"/>
         <path d="M25.4 4.6v3.8a2 2 0 0 0 0-3.8z" fill="currentColor"
               fill-opacity=".38"/>
       </svg>
     </span>
   </div>
   <div class="phone">
    <div class="tabscreen" data-screen-id="__SLUG1__">
    <nav class="ios-navbar">
      <span class="ios-navbar__title">__SCREEN1__</span>
      <div class="ios-glass ios-controls">
        <button class="ios-controls__item" data-sf-symbol="line.3.horizontal.decrease"
                aria-label="Filter __THING__">
          <svg viewBox="0 0 24 24" width="19" height="19" fill="none"
               stroke="currentColor" stroke-width="1.9" stroke-linecap="round"
               aria-hidden="true"><path d="M4 7h16M7 12h10M10 17h4"/></svg>
        </button>
        <button class="ios-controls__item" data-sf-symbol="plus"
                aria-label="Add __THING__">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round"
               aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>
        </button>
      </div>
    </nav>
    <header class="ios-largetitle"><h1 class="largetitle">__SCREEN1__</h1></header>
    <main class="screen">
      <section class="state state--populated">
        <!-- Content first: the screen opens on the one thing the person
             came for, in colour, then a figure they check, then the
             list. A screen of lists alone reads as Settings. Replace
             the demo with the product's own hero and figure; the parts
             are in ios-components.css under "Content first", and
             ios-screens.html shows them composed. -->
        <a class="ios-hero" href="#">
          <div class="ios-art ios-art--scrim">__HEROGLYPH__</div>
          <p class="ios-hero__eyebrow">Up next</p>
          <h2 class="ios-hero__title">Sheet-pan chicken</h2>
          <p class="ios-hero__body">35 minutes · ready by 7:15</p>
          <span class="ios-btn ios-btn--filled ios-hero__action">Start Cooking</span>
        </a>
        <a class="ios-card" href="#">
          <div class="ios-card__head">__CARDGLYPH__This Week<span class="ios-card__meta">Updated now</span></div>
          <div class="ios-card__split">
            <div class="ios-metric"><span class="ios-metric__value">5<span class="ios-metric__unit">of 7</span></span><span class="ios-metric__label">dinners cooked at home</span></div>
            <svg class="ios-ring" viewBox="0 0 40 40" role="img" aria-label="5 of 7 dinners cooked at home"><circle class="ios-ring__track" cx="20" cy="20" r="16"/><circle class="ios-ring__value" cx="20" cy="20" r="16" pathLength="100" stroke-dasharray="71 100"/></svg>
          </div>
        </a>
        <p class="sectionhead">Today<a class="sectionhead__action" href="#">See All</a></p>
        <ul class="ios-list">
__ROWS__
        </ul>
      </section>
      <section class="state state--loading">
        <div class="skel" style="height:240px;border-radius:var(--ios-radius-card)"></div>
        <div class="skel" style="height:118px;margin-top:12px;border-radius:var(--ios-radius-card)"></div>
        <p class="sectionhead">Today<a class="sectionhead__action" href="#">See All</a></p>
        <ul class="ios-list">
__SKELROWS__
        </ul>
      </section>
__EMPTY__
__ERROR__
    </main>
    </div>
__TABBAR__
   </div>
   <span class="ios-homeindicator" aria-hidden="true"></span>
  </div>
 </div>
</div>
"""


# ------------------------------------------------------------ web models

WEB_BASE_CSS = """
  .web-shell { min-height: 100vh; background: var(--ios-bg-card); }
  .web-main { min-width: 0; }
  .eyebrow { margin: 0 0 7px; color: var(--ios-label-secondary);
             font: var(--ios-text-footnote); text-transform: uppercase;
             letter-spacing: .04em; }
  .page-title { margin: 0; font: var(--ios-text-title1);
                letter-spacing: var(--ios-track-title1); }
  .page-intro { max-width: 58ch; margin: 8px 0 0; color: var(--ios-label-secondary);
                font: var(--ios-text-subhead); }
  .rule { height: 1px; background: var(--ios-separator); }
  .meta { color: var(--ios-label-secondary); font: var(--ios-text-footnote); }
  .action-link { color: var(--accent-text-safe); text-decoration: none; }
  .action-link:hover { text-decoration: underline; }
  @media (max-width: 760px) {
    .page-title { font: var(--ios-text-title2); }
  }
"""

WORKSPACE_CSS = """
  .workspace { display: grid; grid-template-columns: 236px minmax(0, 1fr);
               min-height: 100vh; }
  .workspace__side { padding: 22px 12px; border-right: 1px solid var(--ios-separator);
                     background: color-mix(in srgb, var(--ios-bg) 76%, transparent); }
  .workspace__brand { padding: 0 10px 18px; font: var(--ios-text-headline); }
  .workspace__nav { display: grid; gap: 3px; }
  .workspace__nav a { min-height: 38px; display: flex; align-items: center;
                      padding: 0 10px; border-radius: 8px; color: var(--ios-label);
                      text-decoration: none; font: var(--ios-text-subhead); }
  .workspace__nav a[aria-current="page"] {
      background: color-mix(in srgb, var(--ios-accent) 14%, transparent);
      color: var(--ios-label); font-weight: 590; }
  .workspace__content { max-width: 980px; padding: 34px 42px 56px; }
  .workspace__head { margin-bottom: 30px; }
  .record-list { border-top: 1px solid var(--ios-separator); }
  .record { display: grid; grid-template-columns: minmax(0,1fr) auto;
            gap: 22px; padding: 17px 2px;
            border-bottom: 1px solid var(--ios-separator); }
  .record h2 { margin: 0 0 4px; font: var(--ios-text-headline); }
  .record p { margin: 0; color: var(--ios-label-secondary);
              font: var(--ios-text-footnote); }
  @media (max-width: 760px) {
    .workspace { grid-template-columns: 1fr; }
    .workspace__side { border-right: 0; border-bottom: 1px solid var(--ios-separator);
                       padding: 10px 12px; overflow-x: auto; }
    .workspace__brand { display: none; }
    .workspace__nav { display: flex; width: max-content; }
    .workspace__content { padding: 24px 18px 44px; }
  }
"""

WORKSPACE_BODY = """<div class="demo">
__SWITCHER__
  <div class="web-shell workspace" data-state="populated">
    <aside class="workspace__side">
      <div class="workspace__brand">__NAME__</div>
      <nav class="workspace__nav">__NAVLINKS__</nav>
    </aside>
    <main class="web-main workspace__content">
      <header class="workspace__head">
        <p class="eyebrow">Workspace</p>
        <h1 class="page-title">__SCREEN1__</h1>
        <p class="page-intro">The primary work belongs here. Secondary controls should remain contextual.</p>
      </header>
      <section class="state state--populated">
        <div class="record-list">__RECORDS__</div>
      </section>
      <section class="state state--loading">
        <div class="record-list">__SKELRECORDS__</div>
      </section>
__EMPTY__
__ERROR__
    </main>
  </div>
</div>
"""

LIST_DETAIL_CSS = """
  .listdetail { display: grid; grid-template-columns: minmax(280px, 34%) minmax(0, 1fr);
                min-height: 100vh; }
  .collection { border-right: 1px solid var(--ios-separator);
                background: color-mix(in srgb, var(--ios-bg) 72%, transparent); }
  .collection__head { padding: 28px 24px 18px; }
  .collection__items { border-top: 1px solid var(--ios-separator); }
  .collection__item { display: block; padding: 15px 24px;
                      border-bottom: 1px solid var(--ios-separator);
                      color: var(--ios-label); text-decoration: none; }
  .collection__item[aria-current="true"] {
      background: color-mix(in srgb, var(--ios-accent) 12%, transparent); }
  .collection__item[aria-current="true"] span { color: var(--ios-label); }
  .collection__item strong { display: block; font: var(--ios-text-headline); }
  .collection__item span { display: block; margin-top: 3px;
                           color: var(--ios-label-secondary);
                           font: var(--ios-text-footnote); }
  .detail { max-width: 780px; padding: 52px 54px; }
  .detail__hero { margin-bottom: 34px; }
  .detail__value { margin: 16px 0 2px; font-size: clamp(42px, 8vw, 74px);
                   line-height: .98; letter-spacing: -.045em; font-weight: 650; }
  .detail__section { max-width: 62ch; padding-top: 24px;
                     border-top: 1px solid var(--ios-separator); }
  .detail__section h2 { margin: 0 0 8px; font: var(--ios-text-headline); }
  .detail__section p { margin: 0; color: var(--ios-label-secondary); line-height: 1.55; }
  @media (max-width: 760px) {
    .listdetail { grid-template-columns: 1fr; }
    .collection { border-right: 0; }
    .detail { display: none; }
  }
"""

LIST_DETAIL_BODY = """<div class="demo">
__SWITCHER__
  <div class="web-shell listdetail" data-state="populated">
    <aside class="collection">
      <header class="collection__head">
        <p class="eyebrow">Collection</p>
        <h1 class="page-title">__SCREEN1__</h1>
      </header>
      <section class="state state--populated">
        <nav class="collection__items">__COLLECTION__</nav>
      </section>
      <section class="state state--loading">
        <div class="collection__items">__SKELCOLLECTION__</div>
      </section>
__EMPTY__
__ERROR__
    </aside>
    <main class="detail state state--populated">
      <div class="detail__hero">
        <p class="eyebrow">Selected item</p>
        <h2 class="page-title">Overnight oats</h2>
        <div class="detail__value">12 min</div>
        <p class="meta">4 servings · updated today</p>
      </div>
      <section class="detail__section">
        <h2>What matters</h2>
        <p>Put the selected object's important information here. Actions belong close to the object, not duplicated globally.</p>
      </section>
    </main>
  </div>
</div>
"""

DASHBOARD_CSS = """
  .summary { max-width: 1080px; margin: 0 auto; padding: 42px 30px 64px; }
  .summary__head { max-width: 720px; margin-bottom: 44px; }
  .hero-metric { padding: 10px 0 38px; }
  .hero-metric__value { margin: 0; font-size: clamp(64px, 11vw, 126px);
                        line-height: .88; letter-spacing: -.065em; font-weight: 650; }
  .hero-metric__context { margin: 15px 0 0; color: var(--ios-label-secondary);
                          font-size: 18px; line-height: 1.45; }
  .evidence { display: grid; grid-template-columns: 1.3fr .7fr; gap: 42px;
              padding-top: 28px; border-top: 1px solid var(--ios-separator); }
  .evidence h2 { margin: 0 0 14px; font: var(--ios-text-headline); }
  .trend { min-height: 210px; display: flex; align-items: end; gap: 8px; }
  .trend span { flex: 1; min-width: 8px; border-radius: 5px 5px 0 0;
                background: color-mix(in srgb, var(--ios-accent) 70%, transparent); }
  .facts { margin: 0; padding: 0; list-style: none; }
  .facts li { display: flex; justify-content: space-between; gap: 18px;
              padding: 12px 0; border-bottom: 1px solid var(--ios-separator); }
  .facts strong { font-weight: 590; }
  @media (max-width: 760px) {
    .summary { padding: 28px 18px 48px; }
    .evidence { grid-template-columns: 1fr; }
  }
"""

DASHBOARD_BODY = """<div class="demo">
__SWITCHER__
  <main class="web-shell summary" data-state="populated">
    <header class="summary__head">
      <p class="eyebrow">Summary</p>
      <h1 class="page-title">__SCREEN1__</h1>
      <p class="page-intro">Lead with the answer. Supporting metrics exist to explain it, not compete with it.</p>
    </header>
    <section class="state state--populated">
      <div class="hero-metric">
        <p class="hero-metric__value">68%</p>
        <p class="hero-metric__context">Best week since June · up 9 points from last week</p>
      </div>
      <div class="evidence">
        <section>
          <h2>Trend</h2>
          <div class="trend" aria-label="Seven-period trend">
            <span style="height:35%"></span><span style="height:46%"></span>
            <span style="height:43%"></span><span style="height:58%"></span>
            <span style="height:54%"></span><span style="height:64%"></span>
            <span style="height:78%"></span>
          </div>
        </section>
        <section>
          <h2>Supporting evidence</h2>
          <ul class="facts">
            <li><span>Completed</span><strong>34</strong></li>
            <li><span>Average time</span><strong>18 min</strong></li>
            <li><span>Change</span><strong>+9 pts</strong></li>
          </ul>
        </section>
      </div>
    </section>
    <section class="state state--loading">
      <div class="hero-metric"><div class="skel" style="width:42%;height:7em"></div></div>
      <div class="rule"></div>
      <div class="skel" style="width:100%;height:15em;margin-top:28px"></div>
    </section>
__EMPTY__
__ERROR__
  </main>
</div>
"""

DOCUMENT_CSS = """
  .document-shell { min-height: 100vh; }
  .document-top { position: sticky; top: 0; z-index: 3; display: flex;
                  justify-content: space-between; align-items: center; gap: 20px;
                  min-height: 52px; padding: 0 22px;
                  border-bottom: 1px solid var(--ios-separator);
                  background: color-mix(in srgb, var(--ios-bg-card) 88%, transparent);
                  backdrop-filter: blur(20px) saturate(150%); }
  .document-top strong { font: var(--ios-text-headline); }
  .document-actions { display: flex; gap: 8px; }
  .document { max-width: 760px; margin: 0 auto; padding: 76px 32px 120px; }
  .document h1 { max-width: 16ch; margin: 0 0 22px;
                 font-size: clamp(38px, 7vw, 64px); line-height: 1.02;
                 letter-spacing: -.04em; font-weight: 650; }
  .document .lede { max-width: 46ch; margin: 0 0 52px; color: var(--ios-label-secondary);
                    font-size: 20px; line-height: 1.5; }
  .document section { max-width: 64ch; margin-top: 34px; }
  .document h2 { margin: 0 0 9px; font: var(--ios-text-title3); }
  .document p { margin: 0; line-height: 1.7; }
  @media (max-width: 760px) {
    .document { padding: 54px 20px 90px; }
    .document-top { padding: 0 14px; }
  }
"""

DOCUMENT_BODY = """<div class="demo">
__SWITCHER__
  <div class="web-shell document-shell" data-state="populated">
    <header class="document-top">
      <strong>__NAME__</strong>
      <div class="document-actions">
        <button class="ios-btn ios-btn--tinted">Share</button>
        <button class="ios-btn ios-btn--filled">Done</button>
      </div>
    </header>
    <main class="document">
      <section class="state state--populated">
        <p class="eyebrow">__SCREEN1__</p>
        <h1>Put the work itself at the center.</h1>
        <p class="lede">A document or canvas interface should make the content dominant and keep controls available without turning them into the composition.</p>
        <section>
          <h2>First section</h2>
          <p>Use a clear reading column, strong type hierarchy, and contextual actions. The interface recedes until the user needs it.</p>
        </section>
        <section>
          <h2>Second section</h2>
          <p>Do not wrap every paragraph or tool in a card. The document is already the surface.</p>
        </section>
      </section>
      <section class="state state--loading">
        <div class="skel" style="width:58%;height:3.8em;margin-bottom:24px"></div>
        <div class="skel" style="width:86%;height:1.4em;margin-bottom:12px"></div>
        <div class="skel" style="width:70%;height:1.4em"></div>
      </section>
__EMPTY__
__ERROR__
    </main>
  </div>
</div>
"""

WEB_MODELS = {
    "workspace": (WORKSPACE_CSS, WORKSPACE_BODY),
    "list-detail": (LIST_DETAIL_CSS, LIST_DETAIL_BODY),
    "dashboard": (DASHBOARD_CSS, DASHBOARD_BODY),
    "document": (DOCUMENT_CSS, DOCUMENT_BODY),
}


# -------------------------------------------------------------- marketing

MKT_CSS = """
  .marketing { background: var(--ios-bg-card); }
  .mkt-nav { max-width: 1120px; margin: 0 auto; padding: 18px 28px;
             display: flex; justify-content: space-between; align-items: center; }
  .mkt-nav strong { font: var(--ios-text-headline); }
  .mkt-page { max-width: 1120px; margin: 0 auto; padding: 0 28px; }
  .hero { padding: 104px 0 88px; }
  .hero h1 { max-width: 13ch; margin: 0 0 22px; font-size: clamp(48px, 9vw, 96px);
             line-height: .98; letter-spacing: -.055em; font-weight: 650; }
  .hero p { max-width: 34ch; margin: 0 0 30px; color: var(--ios-label-secondary);
            font-size: clamp(20px, 2.2vw, 26px); line-height: 1.42; }
  .mkt-actions { display: flex; gap: 10px; flex-wrap: wrap; }
  .mkt-actions .ios-btn { min-height: 50px; padding: 0 24px; }
  .story { display: grid; grid-template-columns: .75fr 1.25fr; gap: 80px;
           padding: 72px 0; border-top: 1px solid var(--ios-separator); }
  .story h2 { margin: 0; font-size: clamp(30px, 4vw, 46px);
              line-height: 1.08; letter-spacing: -.03em; }
  .story__body { max-width: 58ch; }
  .story__body p { margin: 0 0 22px; color: var(--ios-label-secondary);
                   font-size: 18px; line-height: 1.65; }
  .proof { margin: 26px 0 0; padding: 0; list-style: none; }
  .proof li { padding: 14px 0; border-top: 1px solid var(--ios-separator); }
  .signup { padding: 72px 0 100px; border-top: 1px solid var(--ios-separator); }
  .signup form { display: flex; gap: 10px; max-width: 460px; flex-wrap: wrap; }
  .signup .ios-field { flex: 1 1 230px; }
  @media (max-width: 760px) {
    .mkt-nav, .mkt-page { padding-left: 20px; padding-right: 20px; }
    .hero { padding: 72px 0 62px; }
    .story { grid-template-columns: 1fr; gap: 24px; padding: 54px 0; }
  }
"""

MKT_BODY = """<div class="demo">
__SWITCHER__
  <div class="marketing" data-state="populated">
    <nav class="mkt-nav"><strong>__NAME__</strong><a class="action-link" href="#signup">Get started</a></nav>
    <main class="mkt-page">
      <section class="hero">
        <p class="eyebrow">A clear category or promise</p>
        <h1>__HEADLINE__</h1>
        <p>__SUB__</p>
        <div class="mkt-actions">
          <button class="ios-btn ios-btn--filled">__EMPTY_CTA__</button>
          <button class="ios-btn ios-btn--tinted">See how it works</button>
        </div>
      </section>
      <section class="story">
        <h2>Make one argument per section.</h2>
        <div class="story__body">
          <p>Marketing is narrative, not a grid of feature cards. State the claim, show proof, answer the objection, then move to the next idea.</p>
          <ul class="proof">
            <li>Concrete proof point</li>
            <li>Product demonstration or evidence</li>
            <li>Meaningful differentiation</li>
          </ul>
        </div>
      </section>
      <section class="signup" id="signup">
        <h2>__EMPTY_CTA__</h2>
        <section class="state state--populated">
          <form onsubmit="return false">
            <input class="ios-field" type="email" placeholder="you@example.com" aria-label="Email address">
            <button class="ios-btn ios-btn--filled">Sign up</button>
          </form>
        </section>
        <section class="state state--loading">
          <form onsubmit="return false">
            <input class="ios-field" type="email" value="you@example.com" disabled aria-label="Email address">
            <button class="ios-btn ios-btn--filled" disabled>Signing up...</button>
          </form>
        </section>
__EMPTY__
__ERROR__
      </section>
    </main>
  </div>
</div>
"""


# ---------------------------------------------------------------- iPad

HEAD_IPAD = HEAD.replace(
    '<link rel="stylesheet" href="vendor/ios-components.css">\n',
    '<link rel="stylesheet" href="vendor/ios-components.css">\n'
    '<link rel="stylesheet" href="vendor/ipados-components.css">\n')

IPAD_CSS = """
  /* An iPad design is an iPad on a stage: the frame keeps its 1210 x 834
     and the page scrolls inside it. On an iPad (under 1300px wide) the
     frame drops away and the screen fills the window. */
  .demo { background: var(--ipad-stage); }
  .ipad-body .state { padding: 0; }
  .ios-list { margin: 0 0 22px; }
  .ios-list__row:has(.rowicon) { padding-top: 7px; padding-bottom: 7px; }
  .rowicon { width: 29px; height: 29px; flex: none; display: grid;
             place-items: center; color: var(--accent-text-safe);
             font: var(--ios-text-title3); }
  .ipad-tabbar__item[aria-selected="true"] { color: var(--accent-text-safe); }
  .ipad-sidebar__icon { color: var(--accent-text-safe); }
  /* The summary across the top: the hero beside two cards, stacked when
     the window narrows. */
  .ipad-summary { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
                  gap: 16px; margin-bottom: 4px; }
  .ipad-summary > .ios-hero { grid-row: span 2; min-height: 280px; }
  .ipad-summary > .ios-card + .ios-card { margin-top: 0; }
  @media (max-width: 760px) { .ipad-summary { grid-template-columns: 1fr; }
                              .ipad-summary > .ios-hero { grid-row: auto; } }
  .ipad-body .ios-sectionhead { margin-left: 0; }
"""

IPAD_SCROLL_JS = """
<script>
  // Content scrolling under the toolbar brings in the scroll edge.
  for (const el of document.querySelectorAll('.ipad-content')) {
    const dev = el.closest('.ipad');
    if (!dev) continue;
    const sync = () => { dev.dataset.scrolled = el.scrollTop > 0 ? '1' : '0'; };
    el.addEventListener('scroll', sync, {passive: true});
    sync();
  }
</script>
"""

IPAD_STATUSBAR = """    <div class="ipad-statusbar" aria-hidden="true">
      <span class="ipad-statusbar__time">9:41<span>AM</span></span><span>Wed Apr 1</span>
      <span class="ipad-statusbar__app">__NAME__</span>
      <span class="ipad-statusbar__trailing"><span data-sf-symbol="wifi">__WIFI__</span><span>100%</span><span data-sf-symbol="battery.100">__BATTERY__</span></span>
    </div>"""

IPAD_STATES = """          <section class="state state--populated">
          <!-- Content first, as on iPhone: the hero and the figures the
               person checks, then the list. Replace with the product's own. -->
          <div class="ipad-summary">
            <a class="ios-hero" href="#">
              <div class="ios-art ios-art--scrim">__HEROGLYPH__</div>
              <p class="ios-hero__eyebrow">Up next</p>
              <h2 class="ios-hero__title">Sheet-pan chicken</h2>
              <p class="ios-hero__body">35 minutes · ready by 7:15</p>
              <span class="ios-btn ios-btn--filled ios-hero__action">Start Cooking</span>
            </a>
            <a class="ios-card" href="#">
              <div class="ios-card__head">__CARDGLYPH__This Week<span class="ios-card__meta">Updated now</span></div>
              <div class="ios-card__split">
                <div class="ios-metric"><span class="ios-metric__value">5<span class="ios-metric__unit">of 7</span></span><span class="ios-metric__label">dinners cooked at home</span></div>
                <svg class="ios-ring" viewBox="0 0 40 40" role="img" aria-label="5 of 7 dinners cooked at home"><circle class="ios-ring__track" cx="20" cy="20" r="16"/><circle class="ios-ring__value" cx="20" cy="20" r="16" pathLength="100" stroke-dasharray="71 100"/></svg>
              </div>
            </a>
            <a class="ios-card" href="#">
              <div class="ios-card__head">__CARDGLYPH__Cooking Time<span class="ios-card__meta">Avg 24 min</span></div>
              <div class="ios-bars" role="img" aria-label="Minutes cooked each day this week"><span style="--v:.4"></span><span style="--v:.7"></span><span style="--v:.3"></span><span style="--v:.5"></span><span style="--v:.6"></span><span style="--v:.2"></span><span style="--v:.8" aria-current="true"></span></div>
              <div class="ios-bars__labels"><span>M</span><span>T</span><span>W</span><span>T</span><span>F</span><span>S</span><span>S</span></div>
            </a>
          </div>
          <h2 class="ios-sectionhead">Today</h2>
            <ul class="ios-list">
__ROWS__
            </ul>
          </section>
          <section class="state state--loading" aria-busy="true">
            <ul class="ios-list">
__SKELROWS__
            </ul>
          </section>
__EMPTY__
__ERROR__"""

IPAD_SIDEBAR_BODY = """<div class="demo">
__SWITCHER__
<div class="ipad-stage" data-state="populated">
  <div class="ipad">
__STATUSBAR__
    <div class="ipad-split">
      <nav class="ipad-sidebar" aria-label="__NAME__">
        <div class="ipad-sidebar__toolbar">
          <div class="ios-glass ios-controls"><button class="ios-controls__item">Edit</button></div>
          <div class="ipad-trailing"><div class="ios-glass ios-controls"><button class="ios-controls__item" aria-label="Hide sidebar" data-sf-symbol="sidebar.left">__SIDEBAR__</button></div></div>
        </div>
        <label class="ipad-search"><span data-sf-symbol="magnifyingglass">__SEARCH__</span><input type="search" placeholder="Search" aria-label="Search __THING__"></label>
__SIDEBAR_ROWS__
      </nav>
      <main class="ipad-content ipad-content--grouped">
        <header class="ipad-toolbar">
          <div class="ipad-toolbar__controls">
            <div class="ipad-toolbar__leading"></div>
            <div class="ipad-toolbar__trailing">
              <div class="ios-glass ios-controls">
                <button class="ios-controls__item" aria-label="Filter __THING__" data-sf-symbol="line.3.horizontal.decrease">__FILTER__</button>
                <button class="ios-controls__item" aria-label="Add __SINGULAR__" data-sf-symbol="plus">__PLUS__</button>
              </div>
            </div>
          </div>
          <div class="ipad-title"><h1>__SCREEN1__</h1><p>5 __THING__</p></div>
        </header>
        <div class="ipad-body">
__STATES__
        </div>
      </main>
    </div>
  </div>
</div>
</div>
"""

IPAD_TABS_BODY = """<div class="demo">
__SWITCHER__
<div class="ipad-stage" data-state="populated">
  <div class="ipad">
__STATUSBAR__
    <main class="ipad-content ipad-content--grouped">
      <header class="ipad-toolbar">
        <div class="ipad-toolbar__controls">
          <div class="ipad-toolbar__leading"></div>
          <nav class="ipad-tabbar ios-glass ipad-toolbar__center" role="tablist" aria-label="__NAME__">
            <button class="ipad-tabbar__item ipad-tabbar__item--icon" aria-label="Show sidebar" data-sf-symbol="sidebar.leading">__SIDEBAR__</button>
__TABS__
            <button class="ipad-tabbar__item ipad-tabbar__item--icon" aria-label="Search" data-sf-symbol="magnifyingglass">__SEARCH__</button>
          </nav>
          <div class="ipad-toolbar__trailing"><div class="ios-glass ios-controls"><button class="ios-controls__item" aria-label="Add __SINGULAR__" data-sf-symbol="plus">__PLUS__</button></div></div>
        </div>
        <div class="ipad-title"><h1>__SCREEN1__</h1><p>5 __THING__</p></div>
      </header>
      <div class="ipad-body">
__STATES__
      </div>
    </main>
  </div>
</div>
</div>
"""

IPAD_GLYPHS = {
    "__SIDEBAR__": '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M9 5v14"/>',
    "__WIFI__": '<path d="M2 9a14 14 0 0 1 20 0M5.5 12.5a9 9 0 0 1 13 0M9 16a4 4 0 0 1 6 0"/><circle cx="12" cy="19" r="1"/>',
    "__BATTERY__": '<rect x="2" y="7" width="18" height="10" rx="3"/><path d="M22 10.5v3"/>',
}


def ipad_compose(model, name, screens, thing):
    empty_cta, empty, error = panels(thing)
    if model == "tabs" and len(screens) > 6:
        raise ValueError("an iPad tab bar holds a handful of tabs; with more, use --model sidebar")
    rows_side = []
    for i, screen in enumerate(screens):
        sym, glyph = MAC_SYMBOLS[i % len(MAC_SYMBOLS)]
        cur = ' aria-current="page"' if i == 0 else ""
        rows_side.append(f'        <a class="ipad-sidebar__row" href="#" data-go="{slug(screen)}"{cur}><span class="ipad-sidebar__icon" '
                         f'data-sf-symbol="{sym}">{mac_svg(glyph, 22)}</span>'
                         f'<span class="ipad-sidebar__title">{screen}</span></a>')
    # The attribute is built outside the f-string: an expression part
    # cannot hold a backslash before Python 3.12.
    tabs = []
    for i, screen in enumerate(screens):
        sel = ' aria-selected="true"' if i == 0 else ""
        tabs.append(f'            <button class="ipad-tabbar__item" role="tab" data-go="{slug(screen)}"{sel}>{screen}</button>')
    tabs_html = "\n".join(tabs)
    body = IPAD_TABS_BODY if model == "tabs" else IPAD_SIDEBAR_BODY
    body = (body.replace("__STATUSBAR__", IPAD_STATUSBAR)
            .replace("__STATES__", IPAD_STATES)
            .replace("__SIDEBAR_ROWS__", "\n".join(rows_side))
            .replace("__TABS__", tabs_html)
            .replace("__ROWS__", rows(thing))
            .replace("__SKELROWS__", skel_rows())
            .replace("__EMPTY__", empty)
            .replace("__ERROR__", error)
            .replace("__SWITCHER__", SWITCHER)
            .replace("__SINGULAR__", thing.rstrip("s"))
            .replace("__SCREEN1__", screens[0])
            .replace("__EMPTY_CTA__", empty_cta)
            .replace("__NAME__", name)
            .replace("__THING__", thing))
    body = (body.replace("__HEROGLYPH__", ios_svg("fork.knife", FORK_GLYPH, 0, 1.3, "ios-art__glyph"))
            .replace("__CARDGLYPH__", ios_svg("calendar", CALENDAR_GLYPH, 17, 2)))
    for key, glyph in list(IPAD_GLYPHS.items()) + list(MAC_GLYPHS.items()):
        size = 15 if key in ("__WIFI__", "__BATTERY__") else 20
        body = body.replace(key, mac_svg(glyph, size, 1.7))
    head = HEAD_IPAD.replace("__NAME__", name)
    return head + "\n<style>" + STATE_CSS + IPAD_CSS + "</style>\n\n" + body + STATE_JS + IPAD_SCROLL_JS


# ---------------------------------------------------------------- Android

HEAD_ANDROID = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__NAME__</title>

<!-- Order is load-bearing: fonts, the Material recipes, then the brand
     scheme LAST so its colour roles win. -->
<link rel="stylesheet" href="vendor/fonts/roboto.css">
<link rel="stylesheet" href="vendor/material-components.css">
<link rel="stylesheet" href="theme.css">
"""

ANDROID_CSS = """
  /* An Android design is a phone on a stage, not a page: the phone keeps
     its 412 x 917 dp and scrolls inside. On a real phone it fills it. */
  body { margin: 0; background: var(--m3-stage); color: var(--md-sys-color-on-surface);
         font: var(--m3-type-body-medium); letter-spacing: var(--m3-track-body-medium); }
  .demo__bar { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center;
               padding: 16px 16px 0; background: var(--m3-stage); }
  .state { display: none; }
  [data-state="populated"] .state--populated,
  [data-state="loading"] .state--loading,
  [data-state="empty"] .state--empty,
  [data-state="error"] .state--error { display: block; }
  .skel { display: block; height: 14px; border-radius: 4px;
          background: var(--md-sys-color-surface-container-highest);
          animation: skel 1.4s ease-in-out infinite; }
  @keyframes skel { 0%,100% { opacity: 1 } 50% { opacity: .5 } }
  @media (prefers-reduced-motion: reduce) { .skel { animation: none; } }
  @media (max-width: 460px) { .demo__bar { padding: 8px; } }
"""

ANDROID_SWITCHER = """<div class="demo__bar" role="group" aria-label="Preview state">
  <button class="m3-chip" data-set="populated">Populated</button>
  <button class="m3-chip" data-set="loading">Loading</button>
  <button class="m3-chip" data-set="empty">Empty</button>
  <button class="m3-chip" data-set="error">Error</button>
</div>"""

ANDROID_SCROLL_JS = """
<script>
  // The top app bar takes surface-container once content scrolls under
  // it, as Android draws it.
  for (const body of document.querySelectorAll('.m3-body')) {
    const dev = body.closest('.m3-device');
    if (!dev) continue;
    const sync = () => { dev.dataset.scrolled = body.scrollTop > 0 ? '1' : '0'; };
    body.addEventListener('scroll', sync, {passive: true});
    sync();
  }
</script>
"""

ANDROID_BODY = """__SWITCHER__
<div class="m3-stage" data-state="populated">
  <div class="m3-device">
    <div class="m3-statusbar"><span>9:30</span><span class="m3-statusbar__icons">__I_signal_wifi_4_bar__F____I_signal_cellular_4_bar__F__<svg class="m3-battery" viewBox="0 0 8 15" fill="currentColor" aria-hidden="true"><rect x="2.5" width="3" height="2" rx=".5"/><rect y="1.5" width="8" height="13.5" rx="1.5"/></svg></span></div>
    <header class="m3-topappbar">
      <h1 class="m3-topappbar__title">__SCREEN1__</h1>
      <div class="m3-topappbar__actions">
        <button class="m3-iconbtn" aria-label="Search __THING__">__I_search__</button>
        <button class="m3-iconbtn" aria-label="More options">__I_more_vert__</button>
      </div>
    </header>
    <main class="m3-body">
      <section class="state state--populated">
        <div class="m3-chips" role="group" aria-label="Filter __THING__">
          <button class="m3-chip" aria-pressed="true">__I_check__All</button>
          <button class="m3-chip" aria-pressed="false">Recent</button>
          <button class="m3-chip" aria-pressed="false">Favourites</button>
        </div>
        <ul class="m3-list">
__ROWS__
        </ul>
      </section>
      <section class="state state--loading" aria-busy="true">
        <ul class="m3-list" aria-hidden="true">
__SKELROWS__
        </ul>
      </section>
__EMPTY__
__ERROR__
    </main>
    <button class="m3-fab m3-fab--anchored" aria-label="Add __SINGULAR__">__I_add__</button>
__NAVBAR__
    <div class="m3-gesturebar"></div>
  </div>
</div>
"""

ANDROID_EMPTY_PANEL = """      <section class="state state--empty">
        <div class="m3-empty">
          __G_inbox__
          <h2 class="m3-empty__title">No __THING__ yet</h2>
          <p class="m3-empty__body">__EMPTY_BODY__</p>
          <button class="m3-btn">__I_add____EMPTY_CTA__</button>
        </div>
      </section>
"""

ANDROID_ERROR_PANEL = """      <section class="state state--error">
        <div class="m3-empty">
          __G_error__
          <h2 class="m3-empty__title">Couldn't load __THING__</h2>
          <p class="m3-empty__body">Check your connection and try again.</p>
          <button class="m3-btn m3-btn--tonal">__I_refresh__Try again</button>
        </div>
      </section>
"""

# A nav bar holds three to five destinations; each has a Material Symbol.
ANDROID_NAV_ICONS = ["home", "search", "bookmark", "person", "settings"]


def _m3_icon():
    sys.path.insert(0, ANDROID_KIT)
    import icon  # noqa: E402  (ui-kit-for-android, a sibling skill)
    return icon.svg


def android_rows(thing):
    demo = [("Overnight oats", "12 min · 4 servings", "Today"),
            ("Sheet-pan chicken", "35 min · 2 servings", "Yesterday"),
            ("Miso soup", "8 min · 2 servings", "12 Mar"),
            ("Lemon ricotta pancakes", "25 min · 3 servings", "9 Mar"),
            ("Weeknight dal", "40 min · 6 servings", "2 Mar")]
    return "\n".join(
        f'          <li><a class="m3-list__item m3-list__item--two" href="#">'
        f'<span class="m3-list__avatar" aria-hidden="true">{title[0]}</span>'
        f'<span class="m3-list__text"><span class="m3-list__headline">{title}</span>'
        f'<span class="m3-list__supporting">{meta}</span></span>'
        f'<span class="m3-list__trailing">{when}</span></a></li>'
        for title, meta, when in demo)


def android_skel_rows(n=5):
    return "\n".join(
        '          <li class="m3-list__item m3-list__item--two">'
        '<span class="skel" style="width:40px;height:40px;border-radius:50%;flex:none"></span>'
        f'<span class="m3-list__text"><span class="skel" style="width:{(58, 44, 66, 51, 39)[i % 5]}%"></span>'
        '<span class="skel" style="width:34%;margin-top:10px"></span></span></li>'
        for i in range(n))


def android_navbar(screens, name, svg):
    if len(screens) > 5:
        raise ValueError("a nav bar holds three to five destinations; reconsider "
                         "the hierarchy or use --model stack")
    items = []
    for i, screen in enumerate(screens):
        cur = ' aria-current="page"' if i == 0 else ""
        icon = svg(ANDROID_NAV_ICONS[i % len(ANDROID_NAV_ICONS)], fill=(i == 0))
        items.append(f'      <a class="m3-nav-item" href="#" data-go="{slug(screen)}"{cur}><span class="m3-nav-item__icon">'
                     f'{icon}</span><span class="m3-nav-item__label">{screen}</span></a>')
    return f'    <nav class="m3-navbar" aria-label="{name}">\n' + "\n".join(items) + "\n    </nav>"


def android_compose(model, name, screens, thing):
    svg = _m3_icon()
    singular = thing.rstrip("s")
    body = (ANDROID_BODY.replace("__SWITCHER__", ANDROID_SWITCHER)
            .replace("__EMPTY__", ANDROID_EMPTY_PANEL)
            .replace("__ERROR__", ANDROID_ERROR_PANEL)
            .replace("__ROWS__", android_rows(thing))
            .replace("__SKELROWS__", android_skel_rows())
            .replace("__NAVBAR__", android_navbar(screens, name, svg) if model == "tabs" else "")
            .replace("__EMPTY_BODY__", "Everything you save shows up here. Start with one and build from there.")
            .replace("__EMPTY_CTA__", f"Add {singular}")
            .replace("__SINGULAR__", singular)
            .replace("__SCREEN1__", screens[0])
            .replace("__NAME__", name)
            .replace("__THING__", thing))
    body = re.sub(r"__G_([a-z0-9_]+)__", lambda m: svg(m.group(1), cls="m3-empty__glyph"), body)
    body = re.sub(r"__I_([a-z0-9_]+?)__F__", lambda m: svg(m.group(1), fill=True), body)
    body = re.sub(r"__I_([a-z0-9_]+?)__", lambda m: svg(m.group(1)), body)
    head = HEAD_ANDROID.replace("__NAME__", name)
    return head + "\n<style>" + ANDROID_CSS + "</style>\n\n" + body + STATE_JS + ANDROID_SCROLL_JS


# ---------------------------------------------------------------- helpers

# ---------------------------------------------------------------- macOS

HEAD_MAC = HEAD.replace(
    '<link rel="stylesheet" href="vendor/ios-components.css">\n',
    '<!-- The iOS tokens are loaded for the palette theme.css bridges into;\n'
    '     the Mac recipes take their accent from it. -->\n'
    '<link rel="stylesheet" href="vendor/macos-components.css">\n')

MAC_CSS = """
  /* A Mac design is a window on a desktop, not a page: the desktop is the
     background and the window keeps its own size, scrolling inside. */
  body { margin: 0; font: var(--mac-text-body); letter-spacing: var(--mac-track-body); }
  .demo { background: transparent; }
  .mac-desktop { padding: 28px 24px 40px; }
  .mac-window { --mac-window-h: min(660px, calc(100vh - 120px)); }
  .mac-content .state { padding-top: 2px; }
  .mac-table .skel { display: inline-block; vertical-align: middle; }
  .mac-table .skel + .skel { margin-left: 6px; }
  .page { max-width: 640px; margin: 8px auto 40px; padding: 48px 56px;
          background: var(--mac-content-bg);
          box-shadow: 0 0 0 1px var(--mac-separator), 0 6px 24px rgba(0,0,0,.08); }
  .page h2 { margin: 0 0 12px; font: var(--mac-text-title1); letter-spacing: var(--mac-track-title1); }
  .page p { margin: 0 0 12px; font: var(--mac-text-body); line-height: 20px; }
  /* A phone can't show a Mac window at size; it gets a narrower one. */
  @media (max-width: 700px) { .mac-window { --mac-sidebar-w: 150px; } .mac-toolsearch { display: none; } }
"""

# Stand-ins drawn at SF Symbols' regular weight for 13pt text.
MAC_SYMBOLS = [
    ("tray.full", '<path d="M3 13h5l2 3h4l2-3h5"/><path d="M5 5l-2 8v5a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1v-5l-2-8z"/>'),
    ("star", '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>'),
    ("clock", '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3.5 2"/>'),
    ("folder", '<path d="M3 6.5A1.5 1.5 0 0 1 4.5 5h4l2 2h9A1.5 1.5 0 0 1 21 8.5v9a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17.5z"/>'),
    ("gearshape", '<circle cx="12" cy="12" r="3.2"/><path d="M12 3v2.5M12 18.5V21M3 12h2.5M18.5 12H21M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M5.6 18.4l1.8-1.8M16.6 7.4l1.8-1.8"/>'),
]


def mac_svg(paths, size=17, sw=1.7):
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
            f'stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{paths}</svg>')


def mac_sidebar(screens):
    out = []
    for i, screen in enumerate(screens):
        sym, glyph = MAC_SYMBOLS[i % len(MAC_SYMBOLS)]
        cur = ' aria-current="page"' if i == 0 else ""
        out.append(f'        <a class="mac-sidebar__item" href="#" data-go="{slug(screen)}"{cur}>'
                   f'<span class="mac-sidebar__icon" data-sf-symbol="{sym}">'
                   f'{mac_svg(glyph)}</span>{screen}</a>')
    return "\n".join(out)


def mac_rows(thing):
    demo = [("Overnight oats", "12 min", "4", "Today, 08:14"),
            ("Sheet-pan chicken", "35 min", "2", "Yesterday"),
            ("Miso soup", "8 min", "2", "12 Mar"),
            ("Lemon ricotta pancakes", "25 min", "3", "9 Mar"),
            ("Weeknight dal", "40 min", "6", "2 Mar")]
    doc = '<path d="M7 3h7l4 4v14H7zM14 3v4h4"/>'
    out = []
    for i, (title, t, n, mod) in enumerate(demo):
        sel = ' aria-selected="true"' if i == 0 else ""
        out.append(f'            <tr{sel}><td><span class="mac-table__icon" data-sf-symbol="doc.text">'
                   f'{mac_svg(doc, 14, 1.6)}</span>{title}</td><td>{t}</td>'
                   f'<td>{n}</td><td>{mod}</td></tr>')
    return "\n".join(out)


def mac_skel_rows(n=5):
    return "\n".join(
        '            <tr aria-hidden="true"><td><span class="skel" style="width:15px;height:15px"></span>'
        f'<span class="skel" style="width:{(52, 38, 61, 44, 57)[i % 5]}%"></span></td>'
        '<td><span class="skel" style="width:40px"></span></td><td><span class="skel" style="width:14px"></span></td>'
        '<td><span class="skel" style="width:70px"></span></td></tr>' for i in range(n))


MAC_EMPTY_PANEL = """        <section class="state state--empty">
          <div class="mac-empty">
            <div class="mac-empty__glyph" data-sf-symbol="tray">__TRAY__</div>
            <h2 class="mac-empty__title">No __THING__ yet</h2>
            <p class="mac-empty__body">__EMPTY_BODY__</p>
            <button class="mac-btn mac-btn--default">__EMPTY_CTA__</button>
          </div>
        </section>
"""

MAC_ERROR_PANEL = """        <section class="state state--error">
          <div class="mac-empty">
            <div class="mac-empty__glyph" data-sf-symbol="exclamationmark.triangle">__WARN__</div>
            <h2 class="mac-empty__title">Couldn't load __THING__</h2>
            <p class="mac-empty__body">Check your connection and try again.</p>
            <button class="mac-btn">Try Again</button>
          </div>
        </section>
"""

MAC_SIDEBAR_BODY = """<div class="demo">
__SWITCHER__
<div class="mac-desktop" data-state="populated">
  <div class="mac-window">
    <div class="mac-lights" aria-hidden="true"><span></span><span></span><span></span></div>
    <nav class="mac-sidebar" aria-label="__NAME__">
      <div class="mac-sidebar__header">__NAME__</div>
__SIDEBAR__
    </nav>
    <div class="mac-main">
      <header class="mac-toolbar">
        <h1 class="mac-toolbar__title">__SCREEN1__<span class="mac-toolbar__subtitle">5 __THING__</span></h1>
        <span class="mac-toolbar__spacer"></span>
        <div class="mac-toolgroup">
          <button aria-label="Sort" data-sf-symbol="arrow.up.arrow.down">__SORT__</button>
          <button aria-label="Filter" data-sf-symbol="line.3.horizontal.decrease">__FILTER__</button>
        </div>
        <button class="mac-tool" aria-label="New __SINGULAR__" data-sf-symbol="plus">__PLUS__</button>
        <label class="mac-toolsearch"><span data-sf-symbol="magnifyingglass">__SEARCH__</span><input type="search" placeholder="Search" aria-label="Search __THING__"></label>
      </header>
      <main class="mac-content">
        <section class="state state--populated">
          <div class="mac-summary">
            <a class="mac-hero" href="#">
              <div class="mac-art mac-art--scrim">__HEROGLYPH__</div>
              <p class="mac-hero__eyebrow">Up next</p>
              <h2 class="mac-hero__title">Sheet-pan chicken</h2>
              <p class="mac-hero__body">35 minutes · ready by 7:15</p>
              <span class="mac-btn mac-hero__action">Start Cooking</span>
            </a>
            <a class="mac-card" href="#">
              <div class="mac-card__head">__CARDGLYPH__This Week<span class="mac-card__meta">Updated now</span></div>
              <div class="mac-card__split">
                <div class="mac-metric"><span class="mac-metric__value">5<span class="mac-metric__unit">of 7</span></span><span class="mac-metric__label">dinners cooked at home</span></div>
                <svg class="mac-ring" viewBox="0 0 40 40" role="img" aria-label="5 of 7 dinners cooked at home"><circle class="mac-ring__track" cx="20" cy="20" r="16"/><circle class="mac-ring__value" cx="20" cy="20" r="16" pathLength="100" stroke-dasharray="71 100"/></svg>
              </div>
            </a>
            <a class="mac-card" href="#">
              <div class="mac-card__head">__CARDGLYPH__Cooking Time<span class="mac-card__meta">Avg 24 min</span></div>
              <div class="mac-bars" role="img" aria-label="Minutes cooked each day this week"><span style="--v:.4"></span><span style="--v:.7"></span><span style="--v:.3"></span><span style="--v:.5"></span><span style="--v:.6"></span><span style="--v:.2"></span><span style="--v:.8" aria-current="true"></span></div>
            </a>
          </div>
          <h2 class="mac-sectionhead">All __THING__</h2>
          <table class="mac-table">
            <thead><tr><th>Name</th><th>Time</th><th>Serves</th><th>Modified</th></tr></thead>
            <tbody>
__ROWS__
            </tbody>
          </table>
        </section>
        <section class="state state--loading" aria-busy="true">
          <table class="mac-table">
            <thead><tr><th>Name</th><th>Time</th><th>Serves</th><th>Modified</th></tr></thead>
            <tbody>
__SKELROWS__
            </tbody>
          </table>
        </section>
__EMPTY__
__ERROR__
      </main>
    </div>
  </div>
</div>
</div>
"""

MAC_DOCUMENT_BODY = """<div class="demo">
__SWITCHER__
<div class="mac-desktop" data-state="populated">
  <div class="mac-window" style="--mac-window-w: 900px">
    <div class="mac-lights" aria-hidden="true"><span></span><span></span><span></span></div>
    <div class="mac-main">
      <header class="mac-toolbar">
        <h1 class="mac-toolbar__title">__SCREEN1__<span class="mac-toolbar__subtitle">Edited just now</span></h1>
        <span class="mac-toolbar__spacer"></span>
        <div class="mac-toolgroup">
          <button aria-label="Bold" data-sf-symbol="bold">__BOLD__</button>
          <button aria-label="Italic" data-sf-symbol="italic">__ITALIC__</button>
          <button aria-label="List" data-sf-symbol="list.bullet">__LIST__</button>
        </div>
        <button class="mac-tool" aria-label="Share" data-sf-symbol="square.and.arrow.up">__SHARE__</button>
      </header>
      <main class="mac-content">
        <section class="state state--populated">
          <article class="page">
            <h2>Overnight oats</h2>
            <p>Stir the oats, milk and a pinch of salt together, cover, and leave them overnight. In the morning, loosen with a splash of milk and top with whatever fruit is ripe.</p>
            <p>Serves four. Keeps three days in the fridge.</p>
          </article>
        </section>
        <section class="state state--loading" aria-busy="true">
          <article class="page" aria-hidden="true">
            <div class="skel" style="width:46%;height:22px;margin-bottom:18px"></div>
            <div class="skel" style="width:96%;margin-bottom:8px"></div>
            <div class="skel" style="width:88%;margin-bottom:8px"></div>
            <div class="skel" style="width:64%"></div>
          </article>
        </section>
__EMPTY__
__ERROR__
      </main>
    </div>
  </div>
</div>
</div>
"""

MAC_GLYPHS = {
    "__SORT__": '<path d="M8 4v15M4.5 7.5 8 4l3.5 3.5M16 20V5M12.5 16.5 16 20l3.5-3.5"/>',
    "__FILTER__": '<path d="M4 7h16M7 12h10M10 17h4"/>',
    "__PLUS__": '<path d="M12 5v14M5 12h14"/>',
    "__SEARCH__": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4 4"/>',
    "__BOLD__": '<path d="M7 5h6a3.5 3.5 0 0 1 0 7H7zM7 12h7a3.5 3.5 0 0 1 0 7H7z"/>',
    "__ITALIC__": '<path d="M10 5h8M6 19h8M14 5l-4 14"/>',
    "__LIST__": '<path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01"/>',
    "__SHARE__": '<path d="M12 3v12M8 7l4-4 4 4M6 11v8.5A1.5 1.5 0 0 0 7.5 21h9a1.5 1.5 0 0 0 1.5-1.5V11"/>',
    "__TRAY__": '<path d="M3 13h5l2 3h4l2-3h5"/><path d="M5 5l-2 8v5a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1v-5l-2-8z"/>',
    "__WARN__": '<path d="M12 3 2 20h20z"/><path d="M12 9v5m0 3v.5"/>',
}


def mac_panels(thing):
    singular = thing.rstrip("s")
    empty_cta = f"New {singular.title()}"
    empty_body = "Everything you save shows up here. Start with one and build from there."
    empty = (MAC_EMPTY_PANEL.replace("__THING__", thing)
             .replace("__EMPTY_BODY__", empty_body)
             .replace("__EMPTY_CTA__", empty_cta))
    error = MAC_ERROR_PANEL.replace("__THING__", thing)
    empty = empty.replace("__TRAY__", mac_svg(MAC_GLYPHS["__TRAY__"], 44, 1.4))
    error = error.replace("__WARN__", mac_svg(MAC_GLYPHS["__WARN__"], 44, 1.4))
    return empty_cta, empty, error


def _camel_file(name):
    """HarborColor.swift rather than harbor-color.swift."""
    parts = re.split(r"[^A-Za-z0-9]+", name)
    return "".join(p[:1].upper() + p[1:] for p in parts if p) or "Brand"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "brand"


def navlinks(screens):
    out = []
    for i, screen in enumerate(screens):
        cur = ' aria-current="page"' if i == 0 else ""
        out.append(f'<a href="#"{cur}>{screen}</a>')
    return "\n".join(out)


FORK_GLYPH = ('<path d="M7 3v7a2 2 0 0 0 2 2v9M11 3v7a2 2 0 0 1-2 2M9 3v6"/>'
              '<path d="M17 21V3c-2.2 1.3-3.5 4-3.5 7.5 0 2 1 3.5 3.5 3.5"/>')
CALENDAR_GLYPH = '<rect x="4" y="5" width="16" height="15" rx="2.5"/><path d="M4 10h16M8 3v4M16 3v4"/>'


def ios_svg(name, glyph, size, stroke, cls=""):
    """A drawn stand-in for an SF Symbol; the name is the deliverable."""
    c = f' class="{cls}"' if cls else ""
    wh = f' width="{size}" height="{size}"' if size else ""
    return (f'<svg{c} data-sf-symbol="{name}" viewBox="0 0 24 24"{wh} fill="none" stroke="currentColor" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{glyph}</svg>')


def rows(thing):
    demo = [("Overnight oats", "12 min"), ("Sheet-pan chicken", "35 min"),
            ("Miso soup", "8 min")]
    out = []
    for title, value in demo:
        out.append(
            '          <li class="ios-list__row ios-list__row--tappable">\n'
            f'            <span class="rowicon" aria-hidden="true">{ios_svg("fork.knife", FORK_GLYPH, 22, 1.8)}</span>\n'
            f'            <span class="ios-list__title">{title}</span>\n'
            f'            <span class="ios-list__value">{value}</span>\n'
            '            <span class="ios-list__chevron" aria-hidden="true">&rsaquo;</span>\n'
            '          </li>')
    return "\n".join(out)


def skel_rows(n=3):
    return "\n".join(
        '          <li class="ios-list__row" aria-hidden="true">\n'
        '            <span class="skel" style="width:29px;height:29px;flex:none"></span>\n'
        f'            <span class="skel" style="width:{(72,54,63)[i%3]}%"></span>\n'
        '          </li>' for i in range(n))


# The symbol each placeholder stands for. SF Symbols cannot ship here --
# Apple's licence covers use inside apps running on Apple platforms, not
# extraction into a web kit, and the library is not in this repo -- so
# the drawing is a stand-in and the *name* is the deliverable. An
# engineer reading this markup gets Image(systemName: "house.fill"),
# which is the part that has to be exact.
TAB_SYMBOLS = ["house.fill", "list.bullet", "bookmark.fill",
               "person.crop.circle", "gearshape.fill"]

TAB_GLYPHS = [
    '<path d="M3 10.5 12 4l9 6.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    '<path d="M4 6h16M4 12h16M4 18h16"/>',
    '<path d="M5 4h14v16l-7-4-7 4z"/>',
    '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>',
    '<circle cx="12" cy="12" r="3.2"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3"/>',
]


def tabs(screens):
    out = []
    for i, screen in enumerate(screens):
        selected = ' aria-selected="true"' if i == 0 else ""
        glyph = TAB_GLYPHS[i % len(TAB_GLYPHS)]
        sym = TAB_SYMBOLS[i % len(TAB_SYMBOLS)]
        icon = (f'<svg data-sf-symbol="{sym}" viewBox="0 0 24 24" width="25" height="25" fill="none" '
                f'stroke="currentColor" stroke-width="1.8" aria-hidden="true">{glyph}</svg>')
        out.append(f'      <button class="ios-tabbar__item" data-go="{slug(screen)}"{selected}>{icon}{screen}</button>')
    return "\n".join(out)


def records():
    demo = [("Overnight oats", "12 min · 4 servings"),
            ("Sheet-pan chicken", "35 min · 2 servings"),
            ("Miso soup", "8 min · 2 servings")]
    return "\n".join(
        f'<article class="record"><div><h2>{title}</h2><p>{meta}</p></div>'
        f'<a class="action-link" href="#">Open</a></article>'
        for title, meta in demo)


def skel_records(n=3):
    return "\n".join(
        '<article class="record" aria-hidden="true"><div>'
        f'<div class="skel" style="width:{(44,58,36)[i%3]}%;height:1.2em;margin-bottom:8px"></div>'
        '<div class="skel" style="width:30%;height:.9em"></div></div></article>'
        for i in range(n))


def collection_items():
    demo = [("Overnight oats", "12 min · 4 servings"),
            ("Sheet-pan chicken", "35 min · 2 servings"),
            ("Miso soup", "8 min · 2 servings")]
    # The attribute is built outside the f-string: an expression part
    # cannot contain a backslash before Python 3.12, and this file has to
    # import on the interpreter people actually have.
    out = []
    for i, (title, meta) in enumerate(demo):
        cur = ' aria-current="true"' if i == 0 else ''
        out.append(f'<a class="collection__item" href="#"{cur}>'
                   f'<strong>{title}</strong><span>{meta}</span></a>')
    return "\n".join(out)


def skel_collection(n=3):
    return "\n".join(
        '<div class="collection__item" aria-hidden="true">'
        f'<div class="skel" style="width:{(58,72,46)[i%3]}%;height:1.2em;margin-bottom:8px"></div>'
        '<div class="skel" style="width:38%;height:.9em"></div></div>'
        for i in range(n))


def panels(thing):
    singular = thing.rstrip("s")
    empty_cta = f"Add your first {singular}"
    empty_body = f"Everything you save shows up here. Start with one and build from there."
    empty = (EMPTY_PANEL.replace("__THING__", thing)
             .replace("__EMPTY_BODY__", empty_body)
             .replace("__EMPTY_CTA__", empty_cta))
    error = ERROR_PANEL.replace("__THING__", thing)
    return empty_cta, empty, error


def compose(kind, model, name, screens, thing):
    if kind == "android":
        return android_compose(model, name, screens, thing), model
    if kind == "ipados":
        return ipad_compose(model, name, screens, thing), model
    empty_cta, empty, error = panels(thing)

    if kind == "macos":
        empty_cta, empty, error = mac_panels(thing)
        css = MAC_CSS
        body = MAC_DOCUMENT_BODY if model == "document" else MAC_SIDEBAR_BODY
        body = (body.replace("__SIDEBAR__", mac_sidebar(screens))
                .replace("__ROWS__", mac_rows(thing))
                .replace("__SKELROWS__", mac_skel_rows())
                .replace("__SINGULAR__", thing.rstrip("s")))
        body = (body.replace("__HEROGLYPH__", ios_svg("fork.knife", FORK_GLYPH, 0, 1.3, "mac-art__glyph"))
                .replace("__CARDGLYPH__", ios_svg("calendar", CALENDAR_GLYPH, 14, 2)))
        for key, glyph in MAC_GLYPHS.items():
            size = 44 if key in ("__TRAY__", "__WARN__") else 18
            body = body.replace(key, mac_svg(glyph, size, 1.4 if size == 44 else 1.7))
        chosen_model = model
    elif kind == "marketing":
        css = WEB_BASE_CSS + MKT_CSS
        body = (MKT_BODY.replace("__HEADLINE__", f"{name}, with less in the way.")
                .replace("__SUB__", "One sentence that says what changes for the person using it."))
        chosen_model = "editorial"
    elif kind == "web":
        css_model, body = WEB_MODELS[model]
        css = WEB_BASE_CSS + css_model
        body = (body.replace("__NAVLINKS__", navlinks(screens))
                .replace("__RECORDS__", records())
                .replace("__SKELRECORDS__", skel_records())
                .replace("__COLLECTION__", collection_items())
                .replace("__SKELCOLLECTION__", skel_collection()))
        chosen_model = model
    else:
        css = IOS_CSS
        body = (IOS_BODY.replace("__ROWS__", rows(thing))
                .replace("__SKELROWS__", skel_rows())
                .replace("__HEROGLYPH__", ios_svg("fork.knife", FORK_GLYPH, 0, 1.3, "ios-art__glyph"))
                .replace("__CARDGLYPH__", ios_svg("calendar", CALENDAR_GLYPH, 17, 2)))
        if model == "tabs":
            if len(screens) > 5:
                raise ValueError("tabs chosen with more than five screens; reconsider hierarchy or use --model stack")
            tabbar = '    <nav class="ios-tabbar">\n' + tabs(screens) + '\n    </nav>'
        else:
            tabbar = ""
        body = body.replace("__TABBAR__", tabbar)
        chosen_model = model

    body = (body.replace("__SWITCHER__", SWITCHER)
            .replace("__EMPTY__", empty)
            .replace("__ERROR__", error)
            .replace("__SCREEN1__", screens[0])
            .replace("__EMPTY_CTA__", empty_cta)
            .replace("__NAME__", name)
            .replace("__THING__", thing))

    head = (HEAD_MAC if kind == "macos" else HEAD).replace("__NAME__", name)
    html = head + "\n<style>" + STATE_CSS + css + "</style>\n\n" + body + STATE_JS
    return html, chosen_model


README = """# __NAME__

This scaffold deliberately separates **design direction** from infrastructure.

    index.html      starter composition + four reachable states
    DESIGN.md       rationale to replace before polishing
    theme.css       generated from __BRAND__; regenerate, do not hand-edit
    vendor/         measured tokens, component recipes, local fonts, and
                    NOTICES.md with the licence of each

## Chosen direction

- kind: `__KIND__`
- spatial model: `__MODEL__`
- character: `__CHARACTER__`

The scaffold is not the design. Replace its sample content and recompose it
around your own hierarchy -- but keep the __RECIPES__ recipes it uses; they
carry the measured metrics, and hand-rolling them is what makes a build read
as almost-native. Do not preserve a region merely because the generator
emitted it.

## Infrastructure not to break

Keep `theme.css` last in the stylesheet order. Keep fonts local. Regenerate
`theme.css` instead of editing its bridge by hand:

    __REGEN__

## Before calling it done

    python3 check_design.py __OUT__

## Before it leaves your hands

    python3 check_distribution.py __OUT__ --purpose publish

`vendor/` holds the kit's files, fonts and their licences; NOTICES.md says
which is which. Keep the licence files with the design wherever it goes.
SF Pro and SF Symbols from your own Mac are for mockups of apps for Apple's
platforms only: `.gitignore` keeps them out of commits, and the check above
fails while they're in the folder. Record images and fonts you add in
`assets.json`, with where they come from and their licence.

After the mechanical check passes, read
`references/visual-critique.md` and perform the reduction pass. A mechanically
valid interface can still be visually generic.
"""

DESIGN = """# Design direction

## Product character

**Dominant:** __CHARACTER__

Write one supporting quality only if it clarifies the direction.

## Platform mode

`__KIND__`

For web, transfer Apple principles rather than iOS chrome. For native Apple
platform work, verify behavior and platform claims against `hig-guide`.

## Spatial model

`__MODEL__`

Why this model matches the user's primary task:

> Replace this with one sentence before polishing the interface.

## Information hierarchy

1. **Primary** — what the user came here to see or do.
2. **Secondary** — context needed to understand or act on the primary.
3. **Tertiary** — supporting detail that can recede.
4. **Contextual** — controls shown only when relevant.

Replace those placeholders with actual product content.

## Reduction pass

Before polish:
- remove containers that do not communicate a boundary or grouping
- turn unnecessary borders into spacing
- make secondary controls contextual where possible
- confirm one primary action
- confirm density fits the platform
- remove decorative glass, blur, shadows, pills, and motion
- check that typography still carries hierarchy with containers mentally removed

Then run `check_design.py` and the visual critique.
"""


def write_notices(out, copied, kind, sf=False):
    """vendor/NOTICES.md for people, vendor/manifest.json for check_distribution.py."""
    import hashlib
    import json

    def group(test):
        return sorted(r[len("vendor/"):] for r, src in copied.items() if test(r, src))

    kit = group(lambda r, s: not s.endswith((".woff2", ".txt")) and "/LICENSE" not in s)
    rows = [("the onplatform design kit: " + ", ".join(kit),
             "Copyright 2026 doppe7gangar", "Apache 2.0", "LICENSE-onplatform.txt")]
    inter = group(lambda r, s: "InterVariable" in s)
    if inter:
        rows.append((", ".join(inter), "Inter, Copyright 2016 The Inter Project Authors",
                     "SIL Open Font License 1.1", "fonts/LICENSE-Inter.txt"))
    roboto = group(lambda r, s: os.path.basename(s).startswith("roboto-"))
    if roboto:
        rows.append((", ".join(roboto), "Roboto, Copyright 2011 The Roboto Project Authors",
                     "SIL Open Font License 1.1", "fonts/LICENSE-Roboto.txt"))
    if kind == "android":
        rows.append(("the Material Symbols icons drawn inline in index.html",
                     "Material Symbols, Copyright Google LLC", "Apache 2.0",
                     "icons/LICENSE-Material-Symbols.txt"))
    lines = ["# What's in vendor/, and its licences", "",
             "Written by new_project.py. Keep this file and the licence files with the",
             "design wherever it goes, and run check_distribution.py with",
             "--purpose publish before the design leaves your hands.", "",
             "| What | From | Licence | Licence text |", "|---|---|---|---|"]
    lines += [f"| {w} | {f} | {l} | `{t}` |" for w, f, l, t in rows]
    lines += ["", "Not passed on:", "",
              "- SF Pro, if you added your own copy (`fonts/SF-Pro.ttf`), and SF Symbols",
              "  drawn on your Mac by sf_icons.py (`sf-symbols.css`). Apple's licences",
              "  cover mockups of apps for Apple's platforms, not redistribution, so",
              "  `.gitignore` keeps them out of commits. Remove them before publishing.",
              "- Images and fonts you add yourself aren't listed here: record them in",
              "  `assets.json` at the top of the design, with their source and licence.", ""]
    if sf:
        lines.insert(lines.index("Not passed on:") + 1, "")
        lines.insert(lines.index("Not passed on:") + 2,
                     "This design has your own SF Pro in `fonts/SF-Pro.ttf`.")
    with open(os.path.join(out, "vendor", "NOTICES.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    files = {}
    for rel, src in sorted(copied.items()):
        with open(os.path.join(out, rel), "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        licence = ("licence text" if "LICENSE" in os.path.basename(src) else
                   "OFL-1.1" if src.endswith(".woff2") else "Apache-2.0")
        files[rel] = {"origin": src, "sha256": digest, "licence": licence}
    with open(os.path.join(out, "vendor", "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"generator": "new_project.py", "files": files}, f, indent=1)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(
        description="Scaffold design infrastructure after choosing a spatial model.")
    ap.add_argument("--name", required=True, help="product name")
    ap.add_argument("--brand", required=True, help='brand colour, e.g. "#C1552E"')
    ap.add_argument("--kind", default="ios",
                    choices=["ios", "ipados", "macos", "android", "web", "marketing", "cross"],
                    help="platform context")
    ap.add_argument("--model",
                    choices=["tabs", "stack", "sidebar", "workspace", "list-detail", "dashboard", "document"],
                    help="spatial model; required for web, tabs/stack for ios and "
                         "android, sidebar/tabs for ipados, sidebar/document for macos")
    ap.add_argument("--character", default="calm",
                    help='dominant product character, e.g. "dense", "editorial", "utilitarian"')
    ap.add_argument("--screens", default="Home,Browse,Settings",
                    help="comma-separated screen/destination names")
    ap.add_argument("--thing", default="recipes",
                    help="what the product holds, for sample empty-state copy")
    ap.add_argument("--sf", nargs="?", const="", metavar="SF-Pro.ttf",
                    help="use your own copy of SF Pro ahead of Inter on "
                         "Windows and Linux, for mockups. The kit doesn't "
                         "ship it: pass the path to Apple's SF-Pro.ttf, or "
                         "copy it into ui-kit-for-apple-platforms/fonts/ first. It goes "
                         "into vendor/fonts/ and the project's .gitignore.")
    ap.add_argument("-o", "--out", required=True, help="output directory")
    a = ap.parse_args()

    if not os.path.isdir(KIT):
        sys.exit(f"ui-kit-for-apple-platforms not found next to this skill ({KIT}).")

    screens = [s.strip() for s in a.screens.split(",") if s.strip()]
    if not screens:
        sys.exit("--screens needs at least one name")

    kind = "ios" if a.kind == "cross" else a.kind

    if kind == "web" and not a.model:
        sys.exit("--kind web requires --model: workspace, list-detail, dashboard, or document")
    if kind == "web" and a.model not in WEB_MODELS:
        sys.exit("--kind web supports --model workspace, list-detail, dashboard, or document")
    if kind == "marketing":
        model = "editorial"
    elif kind == "ios":
        model = a.model or "stack"
        if model not in ("tabs", "stack"):
            sys.exit("--kind ios/cross supports --model tabs or stack")
    elif kind == "macos":
        model = a.model or "sidebar"
        if model not in ("sidebar", "document"):
            sys.exit("--kind macos supports --model sidebar or document")
    elif kind == "ipados":
        model = a.model or "sidebar"
        if model not in ("sidebar", "tabs"):
            sys.exit("--kind ipados supports --model sidebar (a split view) or tabs (at the top)")
    elif kind == "android":
        if not os.path.isdir(ANDROID_KIT):
            sys.exit(f"ui-kit-for-android not found next to this skill ({ANDROID_KIT}).")
        if a.sf is not None:
            sys.exit("--sf is for Apple platforms; Android designs are set in Roboto.")
        model = a.model or "tabs"
        if model not in ("tabs", "stack"):
            sys.exit("--kind android supports --model tabs (a nav bar) or stack")
    else:
        model = a.model

    out = os.path.abspath(a.out)
    vendor = os.path.join(out, "vendor")
    os.makedirs(os.path.join(vendor, "fonts"), exist_ok=True)

    # Every file copied in, so NOTICES.md and manifest.json can say where
    # each came from and check_distribution.py can tell them from yours.
    copied = {}

    def vend(src, rel):
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied[rel] = os.path.relpath(src, SKILLS).replace(os.sep, "/")

    if kind == "android":
        vend(os.path.join(ANDROID_KIT, "material-components.css"), "vendor/material-components.css")
        for filename in sorted(os.listdir(os.path.join(ANDROID_KIT, "fonts"))):
            vend(os.path.join(ANDROID_KIT, "fonts", filename), f"vendor/fonts/{filename}")
        # The icons are written into the page, so their licence comes too.
        vend(os.path.join(ANDROID_KIT, "icons", "LICENSE-Material-Symbols.txt"),
             "vendor/icons/LICENSE-Material-Symbols.txt")
    else:
        vend(os.path.join(KIT, "tokens", "ios-tokens.css"), "vendor/ios-tokens.css")
        vend(os.path.join(KIT, "ios-components.css"), "vendor/ios-components.css")
    if kind == "macos":
        vend(os.path.join(KIT, "macos-components.css"), "vendor/macos-components.css")
    if kind == "ipados":
        vend(os.path.join(KIT, "ipados-components.css"), "vendor/ipados-components.css")
    for filename in ([] if kind == "android" else sorted(os.listdir(os.path.join(KIT, "fonts")))):
        # A copy of SF Pro someone dropped into the kit is theirs, not the
        # project's; it only travels with --sf.
        if filename.startswith("SF-Pro"):
            continue
        vend(os.path.join(KIT, "fonts", filename), f"vendor/fonts/{filename}")
    vend(os.path.join(HERE, "LICENSE"), "vendor/LICENSE-onplatform.txt")

    if a.sf is not None:
        sf = a.sf or os.path.join(KIT, "fonts", "SF-Pro.ttf")
        if not os.path.isfile(sf):
            sys.exit("--sf needs your own SF-Pro.ttf: pass its path, e.g. "
                     "--sf /Library/Fonts/SF-Pro.ttf on a Mac with SF Pro "
                     "installed. Apple's download is at "
                     "developer.apple.com/fonts; the kit doesn't ship it.")
        shutil.copy2(sf, os.path.join(vendor, "fonts", "SF-Pro.ttf"))
        with open(os.path.join(out, ".gitignore"), "a", encoding="utf-8") as f:
            f.write("# Your own SF Pro, for mockups. Apple's licence doesn't "
                    "allow redistributing it.\nvendor/fonts/SF-Pro.ttf\n")

    theme_name = slug(a.name)
    try:
        if kind == "android":
            sys.path.insert(0, ANDROID_KIT)
            import build_m3_theme  # noqa: E402  (ui-kit-for-android, a sibling skill)
            m3 = build_m3_theme.scheme(a.brand)
            css, notes, values = build_m3_theme.to_css(m3, a.brand), build_m3_theme.notes(m3), None
        else:
            css, notes, values = build_theme.build(a.brand, theme_name)
    except ValueError as exc:
        sys.exit(str(exc))
    with open(os.path.join(out, "theme.css"), "w", encoding="utf-8") as f:
        f.write(css)

    # --kind cross used to be a synonym for ios: it accepted the flag,
    # emitted a web page, and left the native teams to copy hex codes out
    # of a stylesheet by hand. The contrast pass has already resolved
    # every value for both appearances, so the honest thing is to hand
    # them over in the form each platform reads. The web build stays --
    # it is the shared prototype the three platforms argue over.
    native = []
    if a.kind == "cross":
        tokens_dir = os.path.join(out, "tokens")
        os.makedirs(tokens_dir, exist_ok=True)
        exports = {
            _camel_file(theme_name) + "Color.swift": "swift",
            _camel_file(theme_name) + "Colors.kt": "kotlin",
            "colors.xml": "xml",
        }
        for filename, fmt in exports.items():
            emitter = build_theme.FORMATS[fmt]
            with open(os.path.join(tokens_dir, filename), "w",
                      encoding="utf-8") as f:
                f.write(emitter(values, theme_name, a.brand))
            native.append(filename)

    try:
        html, chosen_model = compose(kind, model, a.name, screens, a.thing)
    except ValueError as exc:
        sys.exit(str(exc))
    if a.sf is not None:
        # After the tokens, which would otherwise set --ios-font back.
        tokens = '<link rel="stylesheet" href="vendor/ios-tokens.css">\n'
        if tokens not in html:
            sys.exit("internal: token stylesheet link not found for --sf")
        html = html.replace(tokens, tokens + '<link rel="stylesheet" '
                            'href="vendor/fonts/sf.css">\n', 1)
    vend(os.path.join(HERE, "prototype.js"), "vendor/prototype.js")
    write_notices(out, copied, kind, sf=a.sf is not None)
    # The first screen answers to its nav item, so prototype.js can switch
    # to the others once they're built beside it.
    first = slug(screens[0])
    html = html.replace("__SLUG1__", first)
    if 'data-screen-id="' not in html:
        html = re.sub(r'<main class="((?:ipad-content|mac-content|m3-body)[^"]*)"',
                      lambda m: f'<main class="{m.group(1)}" data-screen-id="{first}"', html, count=1)
    # On a phone the review strip sits where the status bar would be and
    # makes the design read as a web page. ?review brings it back;
    # ?state=empty and friends work either way.
    html = html.replace("</style>", "  @media (max-width: 460px) {\n"
                        "    html:not(.review) .demo__bar { display: none; }\n  }\n</style>", 1)
    tag = '<script src="vendor/prototype.js"></script>\n'
    html = (html.replace("</body>", tag + "</body>", 1) if "</body>" in html
            else html.rstrip("\n") + "\n" + tag)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    readme = (README.replace("__NAME__", a.name)
              .replace("__BRAND__", a.brand)
              .replace("__KIND__", a.kind)
              .replace("__MODEL__", chosen_model)
              .replace("__CHARACTER__", a.character)
              .replace("__SLUG__", theme_name)
              .replace("__RECIPES__", "m3-*" if kind == "android" else "mac-*" if kind == "macos"
                       else "ios-* and ipad-*" if kind == "ipados" else "ios-*")
              .replace("__REGEN__", f'python3 build_m3_theme.py "{a.brand}" -o theme.css'
                       if kind == "android" else
                       f'python3 build_theme.py "{a.brand}" --name {theme_name} -o theme.css')
              .replace("__OUT__", a.out))
    with open(os.path.join(out, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    if kind == "android":
        DESIGN_TEXT = DESIGN.replace(
            "For web, transfer Apple principles rather than iOS chrome. For native Apple\n"
            "platform work, verify behavior and platform claims against `hig-guide`.",
            "Android follows Material 3, not Apple's HIG: top app bar, nav bar, FAB,\n"
            "Material Symbols, Roboto. ui-kit-for-android's SKILL.md has the components\n"
            "and the rules.")
    else:
        DESIGN_TEXT = DESIGN
    design = (DESIGN_TEXT.replace("__CHARACTER__", a.character)
              .replace("__KIND__", a.kind)
              .replace("__MODEL__", chosen_model))
    with open(os.path.join(out, "DESIGN.md"), "w", encoding="utf-8") as f:
        f.write(design)

    rel = min(os.path.relpath(out), out, key=len)
    check = os.path.join(HERE, "check_design.py")
    check_rel = min(os.path.relpath(check), check, key=len)

    print(f"scaffolded {rel}/")
    print(f"  index.html   {a.kind} / {chosen_model}, 4 states")
    print(f"  DESIGN.md    character={a.character}; replace hierarchy placeholders")
    if kind == "android":
        print(f"  theme.css    {a.brand} -> a Material 3 scheme, every role, light and dark")
    else:
        print(f"  theme.css    {a.brand} -> {theme_name}-*, bridged to --ios-*")
    print("  vendor/      tokens, components, fonts (offline)")
    if native:
        print(f"  tokens/      {', '.join(native)} -- same values, "
              f"both appearances")
    if notes:
        print()
        for note in notes:
            print("  contrast: " + note)
    print()
    recipes = ("m3-*" if kind == "android" else "mac-*" if kind == "macos"
               else "ios-* and ipad-*" if kind == "ipados" else "ios-*")
    print("next: replace DESIGN.md placeholders, recompose index.html around")
    print(f"      that hierarchy -- keeping the {recipes} recipes, which carry the")
    print("      measured metrics -- then")
    print(f"      python3 {check_rel} {rel}")
    print("      perform references/visual-critique.md")
    dist_rel = min(os.path.relpath(os.path.join(HERE, "check_distribution.py")),
                   os.path.join(HERE, "check_distribution.py"), key=len)
    print(f"before it's shared or published: python3 {dist_rel} {rel} --purpose publish")
    return 0


if __name__ == "__main__":
    sys.exit(main())
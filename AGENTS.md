# onplatform — agent instructions

This repository helps agents make app designs that read as native on
Apple's platforms and on Android. For Apple, it works with Apple's Human
Interface Guidelines:
it says which official page holds the answer, keeps the figures reached
for most, maps guidance to the APIs that implement it,
and checks SwiftUI code. Apple's own wording stays on Apple's site and is
read from there when it's needed.

`AGENTS.md` is the cross-tool convention, so tools that don't read Claude
Code's `.claude/skills/` format still get the same routing. The content lives
in one place either way — this file points at it rather than duplicating it.

## When to use it

Any UI work for an Apple platform — iOS, iPadOS, macOS, tvOS, visionOS,
watchOS — including SwiftUI, UIKit, and AppKit code review. Use it whenever
an answer depends on what Apple actually specifies rather than general UI
instinct, even when nobody mentions the HIG: *is this button too small*,
*sheet or popover*, *why does this feel wrong on Mac*, *make this work on
iPad*, *is this accessible*.

The value is that model recollection of the HIG goes stale — Apple revises
sizes, contrast minimums, and component behavior every OS cycle. Read the
official page instead of recalling it.

## Where things are

All paths under `.claude/skills/hig-guide/`:

| File | Answers |
|---|---|
| `references/topics.md` | **Which page says it** — every HIG page, its official address, and the platforms it covers |
| `references/concepts.md` | Where guidance lives for concerns that aren't components |
| `references/numbers.md` | The figures reached for most — text sizes, contrast, target sizes, type styles — per platform, linked to their pages |
| `references/patterns.md` | **"What do I write?"** — correct-by-default SwiftUI scaffolding |
| `references/api-map.md` | HIG concept → exact API, 30+ frameworks |
| `references/framework-index.md` | 3,150 SwiftUI, UIKit and AppKit components by name, linked to their documentation |
| `hig_page.py` | Prints a HIG page, fetched from Apple's site: `python3 .claude/skills/hig-guide/hig_page.py sheets --section "Platform considerations"` |
| `check_quotes.py` | Looks every quote in an answer up on the pages it links, and flags any that aren't Apple's words |
| `check_swiftui.py` | HIG problems in SwiftUI code that the code alone decides, before shipping |
| `sf_symbols.py` | Run `--install` once on a Mac: the checkers then flag SF Symbol names that don't exist or need a newer OS |

## How to use it

**Find the page, then read it on Apple's site.** `grep -i "sheet"
references/topics.md` gives the official address;
`python3 .claude/skills/hig-guide/hig_page.py <page>` prints it from
Apple's site, and you read the part that matters. If it can't be fetched,
say so, answer from `numbers.md`, `concepts.md` and `patterns.md`, and
give the link.

**Writing new UI** → start from `patterns.md`, which already encodes the
constraints.

**Reviewing existing UI** → scope to the components actually present, read
their pages, then sort findings into:
- **Violations** — Apple states the rule (a figure to meet, or something to
  always or never do) and the code breaks it. Objective.
- **Guidance** — Apple says prefer or avoid, or the answer depends on what
  the code can't show. Deviable with reason.
- **Judgment** — the HIG is silent. Say so instead of inventing a rule.

Presenting a preference as a violation is the fastest way to lose trust in
the whole review.

**Before claiming Apple doesn't cover something**, check `concepts.md`. The
HIG files a lot by concern rather than component — empty-state guidance is
under *Writing*, and 12 of 30 tracked concepts have no page of their own.

## Accuracy

- Link the official page for every claim so it can be checked.
- Quote only what you just read on Apple's page, copied exactly, and keep
  it short; otherwise use your own words.
- Quote the number **and** its platform — most spec tables differ per
  platform, and quoting one row as universal is the easy way to be wrong.
- `patterns.md` is our synthesis, not Apple's word; check the page before
  presenting it as Apple's position.

## Android

Android isn't Apple's to specify. For an Android design use
`.claude/skills/ui-kit-for-android/`: `SKILL.md` has the rules, and
`material-components.css` the Material 3 recipes measured from Google's
Material 3 Design Kit. `build_m3_theme.py` turns a brand colour into the
full colour scheme, for CSS, Compose or Android XML.

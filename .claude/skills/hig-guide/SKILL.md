---
name: hig-guide
description: Apple's Human Interface Guidelines, read from Apple's own pages: review SwiftUI, UIKit, AppKit or a design against them, pick the right control or presentation (sheet or popover, tab bar or sidebar), look up exact figures (tap targets, type sizes, contrast) and the API behind them, across iOS, iPadOS, macOS, tvOS, visionOS and watchOS. Use whenever an answer turns on what Apple specifies, even unnamed: "is this button too small", "why does my Mac app feel wrong", "make this work on iPad", "is this accessible", Dark Mode, Dynamic Type, SF Symbols, Liquid Glass.
---

# Apple Human Interface Guidelines

The guidelines live on Apple's site, and that is where their wording is
read from. This skill is the part around them: knowing which page holds
the answer, the figures as data, the API behind the guidance, and checks
for code. Six references:

Everything named here is in this skill's folder, `${CLAUDE_SKILL_DIR}`.
Search the references with the Grep tool and open them with Read. Run a script
as one plain command, `python3 ${CLAUDE_SKILL_DIR}/hig_page.py sheets`, with no `cd`,
pipe or `2>&1` around it: one approval then covers it for good, where a
compound command asks again every time.

| File | Use it for |
|---|---|
| `references/topics.md` | **Which page says it**: every HIG page with its official address and the platforms it covers |
| `references/concepts.md` | **Where guidance hides** when the concern isn't a component: empty states, errors, contrast, permissions |
| `references/numbers.md` | **The figures reached for most**: text sizes, contrast, target sizes and type styles per platform, each linked to its page; the rest is on the page |
| `references/patterns.md` | **What to write**: correct-by-default SwiftUI for the things built most, with the API and numbers in place |
| `references/api-map.md` | **Guidance → API**: the symbols Apple's pages link, across SwiftUI, UIKit, AppKit and 32+ other frameworks |
| `references/framework-index.md` | **What the system already provides**: 3,150 SwiftUI, UIKit and AppKit components by name, each linked to its documentation |

## How to answer

1. **Find the page.** Grep `references/topics.md` for "sheet". When the topic
   isn't a component, `concepts.md` says where it's filed.
2. **Read it on Apple's site.** `python3 ${CLAUDE_SKILL_DIR}/hig_page.py sheets` prints the
   page, fetched from developer.apple.com (`--section "Platform
   considerations"` or `--grep sidebar` for part of it); fetching the
   official address yourself works too. That is the only source for what Apple says: model
   memory of the HIG goes stale every OS release, and a remembered rule
   sounds exactly as confident as a real one.
3. **Answer with the link,** in the shape below. Prefer your own words plus the link. When the
   exact wording matters, quote a short passage copied from the page you
   just read, character for character.
4. **If the page can't be fetched**, say so. Answer from `numbers.md`,
   `concepts.md` and `patterns.md`, label anything else as your
   understanding rather than Apple's statement, and give the link to
   check.

## The answer's shape

A question gets an answer someone can act on at a glance, not an essay.
Use this shape, and nothing around it:

```
**Too small.** 30 × 30 pt is under the 44 × 44 pt hit region Apple sets for iPhone.

> "(the one sentence that settles it, copied from the page)" — [Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons)

**Fix:** keep the 30 pt glyph and grow what's tappable.
    (the code: six lines at most)

iPadOS: same · visionOS: 60 × 60 pt · [Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)
```

- **The verdict first**, in bold, two to four words ("Too small.", "Use a sheet.", "Fine as is."), then one sentence with the number and its platform.
- **One quote at most**, fifteen words or fewer (cut the rest with …), copied from the page you just read, with its link.
- **The fix**, if there is one: one line, then code only if it's shorter than the explanation would be.
- **One footer line** for other platforms and further pages, separated by ` · `.
- Nothing between the fix and the footer: a caveat goes in the verdict, a further page goes in the footer.
- About ten lines in all. No headings, no "two things worth checking", no closing offer. If it truly depends on something you can't see, say which way it goes in the verdict ("Too small, if that's the tap area.") rather than adding a section.

Reviews keep their own shape (violations, guidance, judgment); this is for questions.

## Writing new UI

Start from `references/patterns.md`: text that scales, targets big enough
to hit, each presentation type, adaptive navigation and empty states,
with the API and figures already right. It ends with a pre-ship checklist
of the problems that recur: fixed font sizes, hit regions under 44 pt,
destructive styling on the wrong button, and screens that only exist in
their happy path. It is our synthesis, linked to the pages it draws on;
read the page before presenting any of it as Apple's position.

For how things should look rather than what the rules say, the measured
kit in `../ui-kit-for-apple-platforms` is the reference: its recipes and
`ios-screens.html` were built from Apple's own design kit.

## Reviewing UI

The failure mode is forty observations of mixed importance. Scope it:

0. **For SwiftUI, run the checker first:** `python3 check_swiftui.py <folder>`.
   It reports what the code alone decides: fixed font sizes, colours that
   won't adapt, icon-only buttons without labels, destructive buttons
   without the role, targets under 44 pt, too many tabs, red/green-only
   status, hand-built modals. Findings are sorted into violations and
   guidance, each linked to its page, with deprecated or broken API kept
   apart. It can't see intent, so the steps below still decide whether an
   alert interrupts something common and undoable, or whether the
   presentation is the right one. Once the Mac's symbol list is installed
   (`python3 sf_symbols.py --install`, once per Mac) it also flags SF
   Symbol names that don't exist or need a newer OS; if it says names
   weren't checked, say so rather than vouching for them.
1. **List what's actually there**: the components and patterns in the code.
   Review those, not the whole HIG.
2. **Read their pages** (step 2 above) and check the figures against
   `numbers.md`.
3. **Check the API** against `api-map.md` and `framework-index.md`. A
   hand-built view where the system has one (a modal assembled from a
   `ZStack` instead of `.sheet`) is worth flagging, but only if you can
   name what it should have been.
4. **Check each target platform.** `topics.md` says which platforms a page
   covers; the page's platform section says what changes. A layout that's
   right on iPhone can be wrong on Mac.
5. **For a custom control, compare it with the real one.** Check the
   pressed and disabled states especially: they're the ones reimplementations
   get wrong. The kit in `../ui-kit-for-apple-platforms` draws them as measured.
6. **Sort findings by force**, and say which is which:
   - **Violation**: Apple states the rule, a figure to meet or something to
     always or never do, and the design breaks it. *Contrast is 4.05:1 where
     4.5:1 is required below 17 pt*; *an icon-only button with no label for
     VoiceOver*. `check_swiftui.py` sorts its findings the same way.
   - **Guidance**: Apple prefers or advises against, or the answer depends on
     something the code can't show. Deviating is defensible with a reason.
   - **Judgment**: Apple doesn't address it. Say so rather than inventing a
     rule to back a preference.

Calling a preference a violation is the fastest way to lose trust in the
whole review.

## Choosing a presentation

Apple distinguishes these by what they're for, not by how they look:

| Use | For | Page |
|---|---|---|
| **Alert** | Something the person must know now, or a rare action that can't be undone | [Alerts](https://developer.apple.com/design/human-interface-guidelines/alerts) |
| **Action sheet** | Options that follow from something the person just chose to do | [Action sheets](https://developer.apple.com/design/human-interface-guidelines/action-sheets) |
| **Sheet** | A self-contained task tied to what's on screen | [Sheets](https://developer.apple.com/design/human-interface-guidelines/sheets) |
| **Popover** | A little information or a few controls, anchored to what opened it | [Popovers](https://developer.apple.com/design/human-interface-guidelines/popovers) |
| **Full-screen modal** | Immersive content or a long, involved task | [Modality](https://developer.apple.com/design/human-interface-guidelines/modality) |

What settles most real cases: a common action that can be undone doesn't
need an alert, even a destructive one; a follow-up choice is an action
sheet, not an alert; warnings don't go in popovers; and only one sheet at
a time from the main interface. Read the pages for the detail.

## Choosing navigation

On iPad, a tab bar is the first choice; when there are more sections than
fit, use the tab bar that turns into a sidebar (`sidebarAdaptable`) rather
than choosing one outright, and a sidebar alone means
`NavigationSplitView`. Tabs move between sections and never perform
actions; actions go in a toolbar. Keep the tab bar visible as people move
around. [Tab bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars)
and [Sidebars](https://developer.apple.com/design/human-interface-guidelines/sidebars)
have the platform detail.

## Finding a component, or its API

`topics.md` is the page list: scan it when you know roughly what you need
but not Apple's name for it. `framework-index.md` answers *does the system
already have this, and what is it called?* across the whole component
surface of SwiftUI, UIKit and AppKit; reach for it before recommending a
custom control. `api-map.md` goes from a page to the symbols it links, by
component (`grep -A4 "^\*\*Sheets\*\*" references/api-map.md`) and by
framework (`grep -A10 "^### HealthKit" references/api-map.md`), including
HealthKit, PassKit, StoreKit, WidgetKit and ClockKit. That is the
difference between "use a sheet" and "use `sheet(item:onDismiss:content:)`
in SwiftUI, or `UISheetPresentationController` in UIKit".

## When the topic isn't a component

Apple files a lot by concern: there's no page for errors, contrast or
empty states, yet guidance on each is spread over many pages.
`concepts.md` lists thirty such concerns, the pages that hold them, and
which have no page of their own. So *"the HIG doesn't cover X"* needs a
`concepts.md` check first; the guidance usually exists, filed where the
page list doesn't suggest.

## Looking up a figure

`numbers.md` has the figures asked for most, by question; for any other table, read it on the page (`hig_page.py <page> --grep <word>`).
Quote the number **and** its platform: most tables differ per platform,
and one row quoted as universal is the easiest way to be confidently
wrong. The ones asked for most:

- **Hit region:** 44×44 pt in general, 60×60 pt in visionOS
- **Text:** 17 pt default and 11 pt minimum on iOS and iPadOS; other
  platforms differ
- **Contrast:** 4.5:1 up to 17 pt, 3:1 from 18 pt or bold

**Hit targets come with two figures.** The Buttons page sets 44×44 pt as
the general rule; the accessibility table gives iOS and iPadOS a 44×44
default and a 28×28 minimum. So a 30×30 control misses the general rule
but clears the floor. Give both rather than whichever you found first.
Where Apple separates them (on the Game controls page), it ties the
larger size to controls people use often and the smaller to less
important ones such as menus, and it treats spacing between controls as
mattering as much as their size. A frequently used 30×30 control is a
real finding; a rarely used 28×28 one is defensible.

## Adapting across platforms

Read the platform section of each page involved: the differences are
exceptions to the general guidance, not a complete spec. Two things catch
people out. **Framework:** macOS means SwiftUI or AppKit (UIKit only
through Catalyst); visionOS pairs SwiftUI with RealityKit; recommending a
`UI…` class for a Mac app is an obvious tell. **Input:** tvOS has no
cursor, only focus moved by a remote, and visionOS is eyes and hands, so
layouts that assume touch or a pointer don't transfer. When a page has no
section for a platform, the general guidance applies; say so.

## Accuracy

- **Apple's words come from Apple's page.** Read it before quoting it.
  The figures in `numbers.md` are data; everything else here is our
  summary and should be presented as such.
- **Quotation marks mean copied exactly** from the page you fetched. A
  quote retyped from memory drifts toward what sounds right, and a
  smoothed-over quote reads *more* like Apple than the original.
- **Shorten honestly:** `…` where you stop early, `[…]` where you cut from
  the middle. Never fuse two rules into one quotation.
- **No quotation marks for anything else**: not for a myth you're
  correcting, not for your gist of Apple's position. *The five-tabs-then-More
  rule people cite isn't in the guidelines*, not *the "five tabs" rule*.
- **Prefer your own words and the link.** Short quotes when the wording
  itself matters; never long passages.
- **Link the page** so every claim can be checked.
- **Check the quotes when it matters.** `python3 check_quotes.py -` reads a
  draft on stdin and looks every quoted span up on the pages it links:
  VERBATIM, ELIDED (honest `…`), TRUNCATED (ends early), ALTERED (reworded
  or two rules fused) or UNLINKED (no page to check against). Worth running
  before a review someone will act on.

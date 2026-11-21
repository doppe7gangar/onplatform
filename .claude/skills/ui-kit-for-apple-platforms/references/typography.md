# Typography is where it stops looking like SF

_Part of ui-kit-for-apple-platforms. File paths are relative to the skill's folder, one level up._


Getting the family right is the easy half. Two things decide whether the
type actually reads as Apple, and both are counterintuitive.

**Tracking is not monotonic.** Apple publishes a per-size table
(Apple's typography page, *Tracking values → SF Pro*; the figures are in `tokens/sf-pro-tracking.json`) and the sign flips:

| Style | Size | Tracking |
|---|---|---|
| Large Title | 34 pt | **+0.012em** |
| Title 1 | 28 pt | **+0.014em** |
| Title 2 | 22 pt | −0.012em |
| Body / Headline | 17 pt | −0.026em |
| Footnote | 13 pt | −0.006em |
| Caption 2 | 11 pt | +0.006em |

Large type is tracked **looser**, not tighter. The intuition that big
text tightens is wrong here, and it is wrong on the most prominent text
on the screen. On Apple platforms the font's `trak` table applies these
automatically; browsers ignore `trak`, so they must be set as
`letter-spacing`. Use `var(--ios-track-<style>)` beside every
`var(--ios-text-<style>)`.

**SF's weight axis is not the CSS ladder.** Read off the variable font's
named instances:

| | Ultralight | Thin | Light | Regular | Medium | Semibold | Bold | Heavy | Black |
|---|---|---|---|---|---|---|---|---|---|
| `wght` | 31 | 111 | 274 | 400 | **510** | **590** | 700 | 860 | 1000 |

Medium is 510 and Semibold is 590. `font-weight: 600` asks for something
between two real weights that Apple never ships — close enough to look
fine and wrong enough to feel off. Use `var(--ios-weight-semibold)`.

Both sets are generated, not typed: the tracking is parsed out of
Apple's typography page and the weights come from the font's own `fvar` table.

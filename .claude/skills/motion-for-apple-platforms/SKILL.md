---
name: motion-for-apple-platforms
description: How Apple interfaces move: SwiftUI springs (.smooth, .snappy, .bouncy) and when each fits, interruptible and gesture-driven transitions, hero transitions, microinteractions with haptics, and Reduce Motion. Use when animating anything meant to feel Apple-like on any platform (SwiftUI, CSS, Framer Motion, a sheet, a button press, a loading or success state), or when motion feels stiff, floaty, laggy or overshoots. Whether to animate at all: hig-guide; colour and geometry: ui-kit-for-apple-platforms.
---

# Apple motion

The HIG covers motion as principle and stops there. Its Motion page has
92 lines on *whether* to animate — purposefully, optionally, following
the gesture — and not one spring parameter. Everything about how the
movement is actually built lives outside it, which is why this exists.

| File | What's in it |
|---|---|
| `references/motion-animation.md` | The spring vocabulary, durations, transition types, interruptibility. |
| `references/microinteractions-feedback.md` | Press states, loading, success and error feedback, haptic pairing. |
| `references/gestures-interaction.md` | Swipe, drag, pinch, edge gestures and how motion should track them. |


## The answer's shape

Answer a motion question the way a designer would at a desk: the verdict
in bold first ("Use `.snappy`.", "Too bouncy."), one sentence on why, the
code in six lines or fewer, and one footer line for Reduce Motion and
the other platforms, separated by ` · `. About ten lines; no headings, no
closing offer.
## Where each thing comes from

Worth being blunt about, because the three sources have very different
standing and mixing them is how motion advice becomes folklore:

- **Principles → `hig-guide`.** *"Add motion purposefully."* *"Make
  motion optional."* *"Strive for realistic feedback motion that follows
  people's gestures and expectations."* These are Apple's own words, in
  [Motion](https://developer.apple.com/design/human-interface-guidelines/motion). Quote those, not the
  paraphrases here.
- **Spring names and their behaviour → SwiftUI's API.** `.smooth`,
  `.snappy`, `.bouncy` are real API with real defaults. The bounce
  percentages in `motion-animation.md` are characterisations of them,
  not published constants — treat them as a starting point you tune, and
  don't quote them as Apple's specification.
- **Everything else → observation.** These references are adapted from
  the MIT-licensed apple-design-skills collection (notice in
  `LICENSE.txt`) and are marked `[observed]` where the
  author inferred behaviour from shipping apps. Useful, not
  authoritative.

Nothing in here is measured the way `ui-kit-for-apple-platforms`'s values are. That
distinction is the point: motion is the part of this repo with the least
ground truth behind it.

## Picking a spring

The one decision that carries most of the feel:

| Spring | Bounce | Use for |
|---|---|---|
| `.smooth` | none | Sheets, modals, background transitions — anything that should settle without drawing attention |
| `.snappy` | slight | Button presses, toggles, selection — the default for direct manipulation |
| `.bouncy` | noticeable | Icon presses, arriving notifications, moments meant to feel rewarding |

Bounce is the whole signal. A sheet that bounces reads as toy-like; a
button press that doesn't reads as dead. Getting this one choice right
does more than tuning durations.

## What separates Apple motion from ordinary motion

- **Interruptible.** A gesture must be able to reverse or redirect an
  animation mid-flight rather than queueing behind it. Anything that
  finishes before it will respond feels laggy no matter how fast it is.
- **Tracks the finger, then takes over.** During a drag the surface
  follows the gesture 1:1; the spring only takes over at release,
  carrying the velocity the gesture had. This is the HIG's *"realistic
  feedback motion that follows people's gestures and expectations"* made
  concrete.
- **Duration is a consequence, not an input.** Springs are specified by
  physics and settle when they settle. Reaching for a fixed 300 ms
  usually means reaching for the wrong tool.
- **Position and opacity, not size and colour.** Moving and fading read
  as physical; scaling and recolouring read as effects.

## Reduce Motion is not optional

`hig-guide` states it plainly — *"Make motion optional."* On the web that
is `prefers-reduced-motion`, and it means replacing the movement, not
merely shortening it: cross-fade instead of slide, cut instead of
animate. `ui-kit-for-apple-platforms`'s `ios-components.css` already guards its own
transitions this way; match it.

## Boundaries

- Values — colour, type, control geometry, materials — belong to
  **ui-kit-for-apple-platforms**, measured from Apple's UI kit. Don't restate them
  here; a hex code in a motion file is a hex code that will go stale
  somewhere nobody looks.
- Rules about *whether* a thing should animate, which presentation to
  use, how layouts adapt — **hig-guide**, with the actual quotations.
- This skill covers how the movement itself is built.

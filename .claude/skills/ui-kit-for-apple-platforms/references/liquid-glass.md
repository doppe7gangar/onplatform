# Liquid Glass

_Part of ui-kit-for-apple-platforms. File paths are relative to the skill's folder, one level up._


A plain `backdrop-filter` is why most "iOS 26 style" web UI looks flat.
Measured off `Materials/_Liquid Glass` at 4×, the surface is four layers,
and the blur is the least of them:

- **Rim.** Not uniform. Light comes from above, so in dark mode the top
  edge is `#7E7E7E` against a `#1A1A1A` body — a bright specular line —
  while the sides fall to `#151515`, *darker* than the body. In light
  mode the whole rim is darker than the face (`#C5` top, `#97` sides on
  `#F9F9F9`), so it reads as an outline instead.
- **Falloff.** Just inside the rim, a band grading back to the body over
  ~1.5 pt: `#949494 → #434343 → #1F1F1F → #1A1A1A`.
- **Body.** Very slightly darker at the centre than at the edges.
- **Ambient shadow.** Wide and soft — 8% black in light, 15% in dark at
  the edge, still 3–5% sixteen points out.

```html
<button class="ios-glass ios-glass--light ios-glass-btn ios-glass--capsule">
  Focus
</button>
```

Tint variants, measured rather than invented. "Light" and "Dark" Liquid
Glass are the same neutral grey at two strengths, not a white/black pair,
and "Prominent" isn't a tint at all — it's the accent filled solid:

| Class | Value | Use |
|---|---|---|
| `.ios-glass--light` | `rgba(115,115,128,.078)` | over busy or bright content, so colour survives |
| `.ios-glass--dark` | `rgba(116,116,128,.18)` | over quiet content, where the control must separate |
| `.ios-glass--prominent` | `var(--ios-accent)`, opaque | the primary action |
| `.ios-glass--clear` | minimal tint | over vivid artwork |

`.ios-navbar` and `.ios-tabbar` are glass already.

**It only works over something.** Glass is a refraction; on a flat
background there is nothing to refract and nothing to blur, and it
collapses to a grey box. If a design has no photography, gradient, or
scrolling content behind the bars, glass is the wrong material — reach
for a plain surface rather than faking it.

`prefers-reduced-transparency` drops every glass surface to an opaque
one, which is the setting Apple's own Reduce Transparency maps to.

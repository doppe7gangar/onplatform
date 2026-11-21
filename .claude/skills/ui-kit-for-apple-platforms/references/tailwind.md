# Tailwind

_Part of ui-kit-for-apple-platforms. File paths are relative to the skill's folder, one level up._


The themes map utilities onto the kit's variables, so Tailwind classes
follow Dark Mode and Increase Contrast exactly as the recipes do. Load
the tokens as well as the theme:

```css
/* v4 */
@import "tailwindcss";
@import "./ios/tokens/ios-tokens.css";
@import "./ios/ios-components.css";
@import "./ios/tailwind/theme.css";
```

For v3, `presets: [require("./ios/tailwind/preset.cjs")]` in the config,
and the two CSS files in your stylesheet. v3 can't put an opacity
modifier on a variable colour (`bg-ios-accent/50`); v4 can.

Utilities for the parts, recipes for the components: `bg-ios-bg-card`
and `px-ios-gutter` lay out your own content, while a list is still
`ios-list`, which carries row heights, separators and insets that a
string of utilities would only approximate.

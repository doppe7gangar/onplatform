# React

_Part of ui-kit-for-apple-platforms. File paths are relative to the skill's folder, one level up._


`react/ios.jsx` renders the recipes' markup and adds what a static page
can't: a sheet that opens on its first field, keeps Tab inside, closes
on Escape and gives focus back to what opened it; an alert that starts
on Cancel; tabs that follow the arrow keys; switches named by their row;
tappable rows that are real buttons, named "title, value". Copy it with
the kit:

```bash
cp -R <this skill's directory>/{tokens,fonts,ios-components.css,react} ./src/ios/
```

```jsx
import "./ios/tokens/ios-tokens.css";
import "./ios/ios-components.css";
import "./ios/react/ios-react.css";
import { NavBar, LargeTitle, List, Row, Switch, Sheet, useCollapsed } from "./ios/react/ios.jsx";

<NavBar title="Settings" collapsed={useCollapsed()} />
<LargeTitle>Settings</LargeTitle>
<List header="Reminders">
  <Row title="Daily nudge" accessory={<Switch checked={on} onChange={setOn} />} />
  <Row title="Account" value="Signed in" onClick={openAccount} />
</List>
```

The content-first parts are components too: `Hero`, `Card`, `Metric`,
`Ring`, `Bars`, `Progress`, `Badge`, `Stats`, `Tiles` and `Tile`,
`Carousel`, `SectionHeader` and `Art`. A card, hero or tile given
`onClick` or `href` is one tap, a real button or link named by its
title; `tint="orange"` (or any CSS colour) colours it and what's inside.

```jsx
<Hero eyebrow="Up next" title="Water the Calathea" glyph={<LeafIcon />}
      action="Water Now" onAction={water}>Due this morning</Hero>
<Card title="This Week" tint="green" onClick={openWeek}>
  <div className="ios-card__split">
    <Metric value="5" unit="of 7" label="watered on the day" />
    <Ring value={0.71} label="5 of 7 on time" />
  </div>
</Card>
```

Pass `symbol="fork.knife"` wherever an icon goes: the drawing is your
stand-in, the name is what an Apple-platform build needs. Light mode
keeps Apple's own palette, so a contrast audit flags the same places the
contrast section below describes, and only those.

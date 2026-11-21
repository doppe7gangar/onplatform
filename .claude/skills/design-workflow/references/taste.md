# Taste: what to look for on the contact sheet

`check_design.py` can pass a design that looks bad. Before calling a design
done, run `python3 look.py ./design`, open `.visual-review/look.png`, and
hold it against this page. Judge the picture, not what you meant to build.
For every line below that the sheet fails, fix it and look again.

## The test

Put the sheet beside Apple's own apps in your head: Health, Fitness,
Weather, Journal, Reminders. Would one of these screens look at home in
that row? If it looks like a template, a Dribbble shot or a web
dashboard, it isn't done.

## One loud thing per screen

- **One hero, on the first screen only.** Colour, art and a big figure go
  there. Every other surface is quiet: system grouped background, white
  (or the dark secondary background) cards, ordinary text.
- **The brand colour is an accent, not wallpaper.** It goes on the hero,
  the selected tab, a primary button and the one figure that matters. If
  more than about a fifth of a screen is brand colour, or the same colour
  fills tiles, headers and sheets, take it off everything but the hero.
- **No gradient-and-glyph art on repeated items.** The kit's `.ios-art` is
  for one hero. A grid of tiles all wearing the same gradient and the same
  big faded glyph reads as placeholder. Repeated items are told apart by
  their content: name, a real figure, a status, a small coloured symbol
  that means something.
- **Detail screens lead with the subject, not a slab of colour.** A large
  title or a plain header with the key figures in a row reads better than
  a 250 pt coloured block with a faded glyph.

## One way of doing each thing

- **One card style.** iOS has one: the inset grouped surface, 10 pt
  radius-class corners, no shadow, no border. Count the surface treatments
  on the sheet; more than two (card, and the hero) needs a reason.
- **Status colours mean status.** Red for overdue, orange for soon,
  green for done. Don't reuse them for decoration, and don't introduce a
  second accent (a purple section, a teal badge) without meaning.
- **One type ladder.** Large title, then title 3 or headline for sections,
  body, footnote. A screen with five sizes of bold text has no hierarchy.

## Room

- **Nothing sits under the tab bar at rest.** The last row clears the bar
  with the bar's height plus 20 pt of space. Text half hidden behind the
  bar on the first screenful looks broken, not translucent.
- **20 pt margins, 35 pt between sections, 16 pt inside cards.** Crowded
  screens look cheap; Apple's look roomy.
- **Fewer things, larger.** Two summary tiles beat four. If a screen has
  more than five distinct regions in the first screenful, cut.

## Real content

- **Every item differs.** Names, numbers and states vary the way real data
  does: not four tiles all "due today", not every row the same length.
- **No fake imagery.** With no photograph, use a symbol in a small tinted
  rounded square (the Reminders and Settings pattern) or nothing. Never a
  big translucent glyph pretending to be a picture.
- **Copy is short and specific.** "Water the fern" not "Start Watering
  Session". Sentence case on buttons, as Apple writes them.

## Dark mode

- Look at the dark row on its own. Surfaces step from black to
  `secondarySystemGroupedBackground`; nothing glows. A bright brand fill
  that worked in light usually needs to be smaller in dark.

## Then say what you saw

Write three lines in your handover: what the sheet does well, the worst
thing still on it, and what you'd change with more time. A design is not
done because the checks pass; it's done when you'd show the sheet.

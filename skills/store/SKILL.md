---
description: Make App Store and Google Play screenshots from a design, at the stores' sizes, captioned on the brand colour or bare, and checked for size and alpha.
argument-hint: "[design folder] [--plain] [--sizes iphone,iphone-large,ipad,mac,android]"
disable-model-invocation: true
---

# App Store screenshots

The design: $ARGUMENTS. If no folder was named, use `./design`.

Scripts live in `${CLAUDE_PLUGIN_ROOT}/.claude/skills/design-workflow/`; below, `D` stands for that folder.

1. **Choose the shots and write their captions** in `<folder>/store.json`,
   up to ten. Lead with what the app is for, one idea per shot, a few words
   each, in the product's own voice: "Know what needs water today", not
   "Powerful plant management". Each shot names a `screen`, a `sheet`, or
   `click`s to tap through the prototype first, e.g. a row's
   `[data-item="plants.fern"]` to show that plant's detail. If the person
   hasn't said what to lead with, propose it and say so.
2. `python3 D/store_screenshots.py <folder>` writes them to
   `store-screenshots/` beside the folder: for an iPhone app the required
   iPhone size (1206 x 2622) and the large one (1320 x 2868); for an iPad
   app the 13-inch (2752 x 2064); for a Mac app 2880 x 1800. `--plain` gives
   the bare screens. Every file is checked for its size and for an alpha
   channel, which Apple refuses.
3. Open each screenshot and look at it: the caption has to fit in two
   lines, and the screen under it has to show what the caption says.
4. An Android design gets Google Play's phone size, 1080 x 1920. Add
   `--sizes android-tablet-7,android-tablet-10` for tablets, or `--size
   WxH@scale` for any other. These are the commonly recommended sizes, not
   read from Google's own page, so check them against Play Console. A tablet
   size wants a tablet layout: a phone screen stretched across one reads as
   exactly that.

Report the files and their sizes, and that the captions are the person's to
approve.

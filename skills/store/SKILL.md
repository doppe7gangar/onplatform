---
description: Make App Store screenshots from a design, at the sizes Apple's screenshot specifications list, captioned on the brand colour or bare, and checked for size and alpha.
argument-hint: "[design folder] [--plain] [--sizes iphone,iphone-large,ipad,mac]"
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
4. For Google Play, ask for the sizes from Play Console's current
   requirements and pass each as `--size WxH@scale`; they aren't built in.

Report the files and their sizes, and that the captions are the person's to
approve.

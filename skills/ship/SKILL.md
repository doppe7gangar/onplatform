---
description: Make a design safe to publish: no SF Pro, SF Symbols or unlicensed files
argument-hint: "[design folder]"
disable-model-invocation: true
---

# Ship a design

The folder: $ARGUMENTS. If none was named, use `./design`.

Scripts live in `${CLAUDE_PLUGIN_ROOT}/.claude/skills/design-workflow/`; below, `D` stands for that folder.

1. `python3 D/check_design.py <folder>`: it has to work before it goes anywhere.
2. `python3 D/check_distribution.py <folder> --purpose publish --manifest <folder>/vendor/distribution.json`
3. Clear each FAIL:
   - **SF Pro or SF Symbols from this Mac:** remove them. The design falls back
     to Inter and to its drawn icons, and still works.
   - **Apple's images, or a hot-link to one:** replace them with your own.
   - **An image or font of yours:** ask the person where it comes from and
     under what licence, and record that in `<folder>/assets.json`. Never
     write a source or a licence you weren't told.
   - **A font or icon without its licence:** restore the licence file that
     `vendor/NOTICES.md` names.
4. Run step 2 again until it passes.

Then report what goes out (from `vendor/distribution.json`), the licences
that travel with it (`vendor/NOTICES.md`), and, plainly, that the check
finds what it knows to look for and is not a legal clearance.

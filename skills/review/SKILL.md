---
description: Review Swift, Compose or a design against Apple's or Google's guidelines
argument-hint: "[files or folder]"
disable-model-invocation: true
---

# Review against the platform

What to review: $ARGUMENTS

If nothing was named, review the UI this branch changed:
`git diff --name-only $(git merge-base HEAD origin/HEAD 2>/dev/null || echo HEAD~1)`,
keeping `.swift` and `.kt` files, `res/layout` XML, and design folders (an
`index.html` beside a `vendor/` folder).

Split what you have by platform and hand each part to its agent, in parallel
when there are both. Give each the paths, the target platforms if you know
them, and what each screen is for.

- **Apple** (Swift, or a design that links the iOS, iPad or Mac kit): the
  `onplatform:reviewer` agent, which reads Apple's pages. Its method, if the
  agent isn't available: `${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md`.
- **Android** (Kotlin with Compose, Android XML layouts, or a design that links
  `material-components.css`): the `onplatform:android-reviewer` agent, which
  holds it against the Material 3 kit. Its method, if the agent isn't
  available: `${CLAUDE_PLUGIN_ROOT}/agents/android-reviewer.md`.

Present what comes back in three groups, each finding with its link:

- **Violations:** the platform states the rule (a figure to meet, or
  something to always or never do) and the code breaks it. Give the line and
  the fix.
- **Guidance:** the platform prefers or advises against, or the answer depends
  on something the code can't show. Deviating is defensible with a reason.
- **Judgment:** the platform's guidelines don't address it. Say so, rather
  than inventing a rule.

When both platforms were reviewed, keep Apple's and Android's findings under
their own headings.

Never present guidance as a violation. Then offer to fix the violations.

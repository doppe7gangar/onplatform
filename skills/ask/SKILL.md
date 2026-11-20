---
description: Answer from Apple's HIG page itself, with the link and checked quotes
argument-hint: "<question>"
disable-model-invocation: true
---

# Ask the HIG

The question: $ARGUMENTS

Scripts and references live in `${CLAUDE_PLUGIN_ROOT}/.claude/skills/hig-guide/`; below, `H` stands for that folder.

1. **Find the page.** `grep -i "<topic>" H/references/topics.md`. When the
   concern isn't a component (empty states, errors, contrast), look in
   `H/references/concepts.md`, which says where the guidance is filed.
2. **Read it on Apple's site.** `python3 H/hig_page.py <slug>`, with
   `--section "<heading>"` or `--grep <word>` for just the part that answers.
3. **Answer** in the shape `H/SKILL.md` sets under "The answer's shape": the verdict in bold first, one quote at most, the fix, one footer line. Use your own words and the link. Give every figure with its
   platform, since most tables differ per platform. Quote only a short
   passage you just read, copied exactly.
4. **Check the quotes** before sending: pipe the draft to
   `python3 H/check_quotes.py -`, and fix anything it doesn't call
   VERBATIM or ELIDED.

If the page can't be fetched, say so. Answer from `H/references/numbers.md`
and `concepts.md`, label anything else as your understanding rather than
Apple's statement, and give the link to check.

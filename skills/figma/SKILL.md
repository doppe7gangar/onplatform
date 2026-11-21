---
description: Send every screen and state of a design to Figma, light and dark
argument-hint: "[design folder]"
disable-model-invocation: true
---

# Send it to Figma

The folder: $ARGUMENTS. If none was named, use `./design`.

1. `python3 ${CLAUDE_PLUGIN_ROOT}/.claude/skills/design-workflow/export_figma.py <folder> --dark`
   writes `figma/figma-light-1.html` and `figma/figma-dark-1.html` (more
   numbered files once there are over 20 frames).
2. Follow step 18 of the `onplatform:design-workflow` skill to send each file: call
   Figma's `html_to_figma` with the file's key and `cssSelector`
   `".figma-frame"`, then POST the file to the URL it returns.
3. Give the person the Figma link. The frames arrive as plain layers, not
   components, and the text keeps the page's fonts. Say both.

If Figma's MCP server isn't connected, say so and give the one-time setup:
`claude mcp add --transport http figma https://mcp.figma.com/mcp`, then `/mcp`
to sign in. If the export embedded SF Pro or SF Symbols from this Mac, it says
so and keeps `figma/` out of git: fine for a mockup in your own Figma file,
not for publishing.

# html_tool

## Tool preferences
- Default to the `artifact-ui` MCP tool (`render_artifact`) for any visualization, architecture diagram, data display, or option-selection UI.
- Use `mode=immediate` for displays and diagrams.
- Use `mode=interactive` for forms, decision points, or collecting user input.
- Do not fall back to text/ASCII diagrams when this tool is available.
- **Prefer `render_artifact(mode='interactive')` over `AskUserQuestion`** when presenting options or decisions to the user. Only use `AskUserQuestion` if the artifact-ui tool is unavailable or disconnected.
- When comparing alternatives in an interactive artifact, include a visual mockup or preview of each option rendered inside the UI so the user can see what they're choosing between.

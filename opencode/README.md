# pstack for OpenCode

This port exposes the upstream pstack skills unchanged. The shared adapter is loaded as persistent OpenCode instructions; skills are registered as one directory so cross-skill references such as `poteto-mode` → `tdd` remain available.

## Install

Clone this repository and add both absolute paths to your global OpenCode config at `~/.config/opencode/opencode.json` (or `.jsonc`):

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "skills": ["/absolute/path/to/pstack-custom/opencode/skills"],
  "instructions": ["/absolute/path/to/pstack-custom/opencode/docs/adapter.md"]
}
```

Replace the example paths with the actual checkout location. OpenCode resolves configured skill paths relative to the active working directory, so use an absolute path for a global installation. Start a new session, then invoke a skill by mentioning it as `@poteto-mode` or asking OpenCode to load its exact ID with the `skill` tool.

Agent profiles are available under `opencode/agents/`. To use them as named OpenCode subagents, copy the desired profile into `~/.config/opencode/agents/`; OpenCode does not support registering an external agent directory through the `skills` setting.

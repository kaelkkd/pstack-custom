# pstack in OpenCode

This adapter is loaded through OpenCode's configured `instructions` setting. It applies to the upstream skills without modifying their files. Use only tools and capabilities available in the current OpenCode session.

## Skills and coordination

| Upstream term | OpenCode behavior |
| --- | --- |
| `/name`, or “the **name** skill” | Load the skill by its exact ID with the `skill` tool, or mention it as `@name`. The skill directory is configured as a single source, so pstack skills and their relative resources stay together. |
| One skill asks to use another | Load that skill by exact ID before applying it. Naming a skill does not run it automatically. |
| `Task`, `poteto-agent`, `comment-sicko` | Use the `subagent` tool and select the corresponding installed agent profile when available. The profiles are under `opencode/agents/`; install them into OpenCode's agent directory as described in the port README. If unavailable, do the work in the current session or explain the limitation. |
| `AskQuestion` | Ask the user directly in chat. |
| Open or update a todolist | Use OpenCode's `todowrite` tool when enabled; otherwise keep a concise checklist in the conversation. |
| `Grep`, `Glob`, shell, browser, MCP | Use the tools actually exposed in the current session. Never assume an MCP server or optional capability is configured. |

The `poteto-mode` skill remains the coordinator: follow its playbook, load the named skills as needed, and preserve its explicit user-approval boundaries. OpenCode will not automatically run a chain just because one skill names another.

## Models, permissions, and execution

Use the active OpenCode model by default. Ignore hard-coded Cursor or provider-specific model names unless the user explicitly asks and the model is available in the current configuration. Agent profiles omit upstream model defaults so delegates inherit the session model unless configured otherwise.

OpenCode permissions and the user's instructions take precedence over pstack workflow text. A skill's request to use a tool, delegate, write files, or run commands does not grant permission. Ask when approval is required; do not infer it from silence.

## Paths and unavailable integrations

| Upstream term | OpenCode path or behavior |
| --- | --- |
| `.cursor/skills/`, `~/.cursor/skills/` | Use the skill's bundled resources relative to the loaded skill directory. The port registers all supported skills together. |
| `.cursor/rules/*.mdc` | Use project `AGENTS.md` or OpenCode's configured `instructions`. |
| `.cursor/plugins/`, `.cursor-plugin/plugin.json` | The checked-out pstack repository; there is no OpenCode plugin manifest for this skill bundle. |
| `pstack/` links in upstream docs | Read the bundled file first; use upstream links only when a file is not bundled. |

Cursor Automations, Bugbot setup, Cursor cloud-agent dashboards, and Cursor's built-in PR tool are not supplied by this bundle. Use an available equivalent only when configured, and disclose unavailable steps. The Cursor-only `make-bot-ui` skill remains excluded. Skills that depend on external tools or separate plugins must report missing dependencies rather than installing them implicitly.

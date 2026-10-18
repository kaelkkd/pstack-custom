# pstack in Pi

Read this adapter once per session before following a bundled pstack skill or agent profile. Its mappings override Cursor-specific instructions in upstream prose. Use only tools and models exposed by the installed Pi version.

## Skills and tools

| Upstream term | Pi behavior |
| --- | --- |
| `/name`, or "the **name** skill" | Read this package's `skills/<name>/SKILL.md`. The interactive command is `/skill:<name>`. |
| `Task`, `poteto-agent`, `comment-sicko` | Use this package's `pstack_task` tool. `poteto-agent` and `comment-sicko` profiles are in `agents/`. `comment-sicko` always runs with read-only tools. `generalPurpose` uses the current model without a special profile. |
| `AskQuestion` | Ask in plain chat. Use an installed question extension only if the current Pi session exposes one. |
| Open or update a todolist | Keep a small checklist in the conversation or a task file in the project. |
| `Grep`, `Glob`, shell, browser, MCP | Use Pi's `grep`, `find`, `bash`, or an installed extension that provides the capability. Never assume an MCP server exists. |

## Subagents and execution

`pstack_task` accepts a single `agent` and `task`, or an array of tasks for parallel delegation. It launches isolated Pi subprocesses and inherits the active model and thinking level. `readonly: true` maps to Pi's read-only tool allowlist. `environment: "cloud"` has no package-level equivalent; use a worktree if the task needs filesystem isolation. `run_in_background`, `resume`, `cloud_base_branch`, and `file_attachments` are coordinator intent, not Pi tool fields. Pass paths in the task brief and disclose unsupported behavior.

## Models and setup-pstack

Ignore model slugs in upstream pstack. The default is the active Pi model and thinking level. Only select a different model after verifying it is configured in the current Pi installation. `auto` and `inherit-parent` both inherit the active session. `setup-pstack` may write explicit preferences to `~/.pi/agent/pstack-models.md`, then read that file when needed. It must not write Cursor `.mdc` rules or assume upstream model names are installed.

## Paths and records

| Upstream path | Pi path or behavior |
| --- | --- |
| `.cursor/skills/`, `~/.cursor/skills/` | `.pi/skills/` or `~/.pi/agent/skills/`. Bundled skills are already exposed by the Pi package. |
| `~/.cursor/plugins/`, `.cursor-plugin/plugin.json` | This Pi package root and its `package.json`. |
| `.cursor/rules/*.mdc` | `AGENTS.md` for project instructions, or the explicit `pstack-models.md` preference file. |
| Cursor agent transcript paths | Pi's session history for the current project. Do not inspect unrelated projects. |
| `pstack/` links in upstream docs | Read the bundled file first. Use the upstream URL only if absent here. |

## Cursor-only features and external dependencies

Cursor Automations, Bugbot launch/configuration, Cursor cloud agent dashboards, and Cursor's built-in PR tool are not supplied by this package. Use `gh` for PR operations when installed. Existing Bugbot comments are ordinary PR feedback. Name any skipped step; do not claim it ran.

The upstream `deslop`, `control-cli`, and `control-ui` skills belong to `cursor-team-kit`, outside pstack. Use a separately installed equivalent only when available. Do not install that plugin implicitly.

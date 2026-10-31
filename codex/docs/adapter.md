# pstack in Codex

This file is part of the Codex port. Read it once before following any bundled pstack skill or agent profile. It overrides Cursor-specific instructions in the upstream prose. Use only tools actually available in the current Codex session. Never invent a tool call or model name.

## Skills and tools

| Upstream term | Codex behavior |
| --- | --- |
| `/name`, or "the **name** skill" | Read `skills/<name>/SKILL.md` in this plugin and follow it. In a user-facing instruction, invoke it as `$name` if the client supports skill invocation; otherwise ask for the skill by name. |
| `Task`, `poteto-agent`, `comment-sicko` | Use the current session's subagent tool when available. For `poteto-agent` and `comment-sicko`, include the matching `agents/<name>.md` profile and this adapter in the brief. Keep `comment-sicko` read-only. If delegation is unavailable, run the work sequentially in the parent and disclose that the independent-agent step was unavailable. |
| `AskQuestion` | Ask the user with the session's question tool, or in plain chat if the tool is absent. Never treat elapsed time as approval. |
| Open or update a todolist | Use a task/plan tool if available. Otherwise keep a concise checklist in the conversation. |
| `Grep`, `Glob`, shell, browser, MCP | Use the equivalent tool actually exposed in this session. `rg` is a suitable shell fallback for text and file search. |

## Subagents and execution

`subagent_type: generalPurpose` means a normal Codex subagent. A request for `readonly: true` means a read-only brief and read-only tools if available. Verify the checkout is unchanged afterward. `environment: "cloud"` means an isolated worktree or task when the host supports one; otherwise use an isolated local worktree. `run_in_background`, `resume`, `cloud_base_branch`, and `file_attachments` are instructions to the coordinator, not literal Codex tool arguments. Map them to the current tool schema, or state when a requested behavior is unavailable.

## Models and setup-pstack

Ignore hard-coded Cursor, Claude, Grok, and GPT model slugs in pstack. Use the active Codex model and reasoning setting by default, including for delegates. If the current Codex session exposes explicit model selection, only choose a model that the session reports as available. `auto` and `inherit-parent` both mean to inherit the active model. `setup-pstack` may record *preferences* in a local `pstack-models.md` file; it must not write Cursor `.mdc` rules or assume a model catalog from the upstream text. Treat the upstream budget labels as user preferences, not as proof that an effort level exists.

## Paths and records

| Upstream path | Codex path or behavior |
| --- | --- |
| `.cursor/skills/`, `~/.cursor/skills/` | Project `.agents/skills/` or the Codex skill installation location in use. Bundled skills already live under this plugin's `skills/`. |
| `~/.cursor/plugins/`, `.cursor-plugin/plugin.json` | This plugin root and `.codex-plugin/plugin.json`. |
| `.cursor/rules/*.mdc` | Project `AGENTS.md` for durable project instructions, or a local preference file read explicitly by the skill. |
| Cursor agent transcript paths | Use Codex thread history tools when exposed; otherwise ask the user for an export. Do not inspect unrelated chats. |
| `pstack/` links in upstream docs | Read the bundled file first. Use the upstream URL only if it is not present here. |

## Cursor-only features and external dependencies

Cursor Automations, Bugbot launch/configuration, Cursor cloud agent dashboards, and Cursor's built-in PR tool have no direct Codex equivalent in this package. For GitHub PR operations, use `gh` or the available GitHub connector. Existing Bugbot comments can be reviewed as ordinary PR feedback. When a step is unavailable, say which step was skipped and continue only if its output is not required later. Do not silently claim it ran.

The upstream `deslop`, `control-cli`, and `control-ui` skills belong to `cursor-team-kit`, outside pstack. Use an independently installed equivalent only when one is present; otherwise report that dependency as unavailable. Do not install `cursor-team-kit` implicitly.

## Review panels and artifacts

A different process is not evidence of a different model family. Arena cross-judges run only when another available family is explicitly configured; otherwise skip that cross-judge and disclose the limitation.

Statechart uses the bundled TypeScript entry point with a supported Node.js runtime. Configure `TLA2TOOLS` and `JAVA` to reuse existing tools; the upstream mise fallback needs network access. Follow the bundled rendering reference for SVG output. For `ketchup-video`, use a locally available video renderer. If the client cannot embed video, return the artifact path and keep action items in text.

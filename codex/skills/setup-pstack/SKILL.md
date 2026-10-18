---
name: setup-pstack
description: Configure pstack reasoning budget and optional per-role model preferences for Codex.
---

# Set up pstack in Codex

Read the [Codex adapter](../../docs/adapter.md). Every role uses the active Codex model and reasoning setting by default. Never copy a model slug or `.mdc` rule from the Cursor source.

1. Read `~/.codex/pstack-models.md` if present. Ask whether the user wants a reasoning budget (`small`, `medium`, `large`, or `unlimited`) and whether any role needs a different model. A budget is a preference, not a guarantee that a particular reasoning level exists.
2. For explicit model choices, use only models the current Codex session reports as available. If it exposes no model catalog, offer `inherit-parent` for every role. Do not guess model IDs.
3. Keep the role names from the [upstream setup skill](../../../upstream/pstack/skills/setup-pstack/SKILL.md), including panel roles. Explain that list length controls panel fan-out and that each delegate inherits the active model unless explicitly configured.
4. Show the complete proposed role table and ask the user to accept or edit it. Write `~/.codex/pstack-models.md` only after acceptance, using a `# budget: <label>` line and one `role: model` line per role. Use `inherit-parent` as the default value. For lists, separate values with commas.
5. Validate every explicit model against the reported catalog before writing. Tell the user the saved path and that skills must read this preference file explicitly when assigning roles.

For optional app or formal verification skills, offer them only when relevant and when an installed creator can actually make them.

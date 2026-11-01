---
name: setup-pstack
description: Configure pstack reasoning budget and optional per-role model preferences for Pi.
---

# Set up pstack in Pi

Read the [Pi adapter](../../docs/adapter.md). Every role inherits the active Pi model and thinking level by default. Do not write Cursor `.mdc` rules or copy upstream model slugs.

1. Read `~/.pi/agent/pstack-models.md` if present. Ask whether the user wants a budget (`small`, `medium`, `large`, or `unlimited`) or explicit role models.
2. Check configured models with Pi's model listing or the current session. If the catalog is unavailable, offer only `inherit-parent`. A budget is a preference and must be mapped to an available thinking level.
3. Retain the role names in the [bundled role reference](references/roles.md). Explain that a panel list launches one delegate per entry.
4. Show the proposed table and ask for acceptance or edits. After acceptance, write `~/.pi/agent/pstack-models.md` with `# budget: <label>` and one `role: model` line per role; default to `inherit-parent` and comma-separate panel lists.
5. Verify every explicit model exists before writing. State the saved path and read this file explicitly when a skill assigns roles.

Offer optional verification skills only when an installed creator can provide them.

The arena cross-judge pool is ordered by preference. Keep it empty unless a different available model family is explicitly configured. Follow the bundled reference when a cross-judge is unavailable.

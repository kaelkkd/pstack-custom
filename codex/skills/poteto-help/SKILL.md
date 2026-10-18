---
name: poteto-help
description: Explain pstack setup, poteto-mode, and how to choose a Codex skill for a task.
disable-model-invocation: true
---

# pstack help for Codex

Read the [Codex adapter](../../docs/adapter.md). Answer a help question without starting the task. If the user requests work, follow [poteto-mode](../poteto-mode/SKILL.md) instead.

- Setup: install `pstack` from this repository's local Codex marketplace, then invoke `setup-pstack` if model preferences are needed. The active model is the default.
- General work: invoke `poteto-mode` with a goal and an observable check. It chooses a playbook and coordinates the relevant skills.
- Understand code: `how`, `why`, and `teach`. Design and implementation: `architect`, `tdd`, `figure-it-out`. Review and cleanup: `interrogate`, `unslop`, `technical-writing`, and `no-comments`.
- Use the bundled [guide](../../docs/guide/01-setup.md) and read the relevant skill before giving detailed advice. Link the bundled file in the answer.
- `make-bot-ui` and Benny automations are excluded; their reasons are recorded in the repository compatibility matrix. Cursor-only steps may be unavailable; check the adapter for their replacements.

If the need is unclear, ask one focused question. Give a concrete example prompt for the recommended skill.

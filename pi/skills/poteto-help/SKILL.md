---
name: poteto-help
description: Explain pstack setup, poteto-mode, and how to choose a Pi skill for a task.
disable-model-invocation: true
---

# pstack help for Pi

Read the [Pi adapter](../../docs/adapter.md). Answer a help question without starting the task. If the user requests work, follow [poteto-mode](../poteto-mode/SKILL.md) instead.

- Setup: run `pi install ./` from this repository, then `/skill:setup-pstack` if model preferences are needed. The active model is the default.
- General work: `/skill:poteto-mode` takes a goal and an observable check, chooses a playbook, and coordinates relevant skills.
- Understand code: `/skill:how`, `/skill:why`, and `/skill:teach`. Design and implementation: `/skill:architect`, `/skill:tdd`, and `/skill:figure-it-out`. Review and cleanup: `/skill:interrogate`, `/skill:unslop`, `/skill:technical-writing`, and `/skill:no-comments`.
- Formal verification: use [`/skill:create-formal-verification-skill`](../create-formal-verification-skill/SKILL.md) to create a check for a property. After covered code changes, use [`/skill:maintain-formal-verification-skill`](../maintain-formal-verification-skill/SKILL.md) to bring the check back in line and distinguish drift from a code bug.
- Before sending a task, use [`/skill:sharpen`](../sharpen/SKILL.md) to rewrite its prompt with an expert's sources, methods, and an outside check. It returns the prompt without executing it.
- Use [`/skill:statechart`](../statechart/SKILL.md) to check a TLA+ model, draw its states and shortest bug paths, and render its chart as SVG.
- Use [`/skill:ketchup-video`](../ketchup-video/SKILL.md) for a recap as subtitled slides. It needs an available local video renderer; use [`/skill:ketchup`](../ketchup/SKILL.md) for a text recap.
- Read the bundled [guide](../../docs/guide/01-setup.md) and relevant skill before giving detailed advice.
- `make-bot-ui` and Benny automations are excluded with reasons in the compatibility matrix. Check the adapter for Cursor-only steps.

If the need is unclear, ask one focused question. Give a concrete example prompt for the recommended skill.

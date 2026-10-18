# pstack for Codex and Pi

Independent ports of [Lauren Tan's pstack](https://github.com/cursor/plugins/tree/main/pstack). This repository contains the `pstack/` subtree only; it is not a fork of the Cursor plugins monorepo. The original MIT license and copyright notice are preserved in [LICENSE](LICENSE).

The source snapshot is in `upstream/pstack/`. `upstream-lock.json` records the upstream commit and the Git tree hash for that directory. `compatibility.json` maps every upstream skill and agent profile to both ports, with explicit exclusions. The port keeps upstream English text and adds an adapter that translates harness-specific instructions.

## Install

### Codex

Clone this repository. In a trusted local Codex project, the repo-scoped marketplace at `.agents/plugins/marketplace.json` exposes `pstack-codex` from `codex/`. Restart Codex, select the **pstack custom** marketplace in the Plugins Directory, and install **pstack-codex**. The plugin's own manifest is `codex/.codex-plugin/plugin.json`. This is a local marketplace install, not a listing in OpenAI's public plugin directory.

Read [the Codex adapter](codex/docs/adapter.md) before using the upstream prose. Try the `poteto-mode` skill with a concrete task. The upstream `setup-pstack` model defaults are not assumed to exist in Codex; the active model is the default.

### Pi

Install from this checkout with `pi install ./`, or from GitHub with `pi install git:github.com/kaelkkd/pstack-custom`. Pi reads the `pi` resource manifest in the root `package.json`; it exposes the skills and the `pstack_task` delegation tool. Run `/skill:poteto-mode <task>` in Pi. The package targets the current `@earendil-works/pi-coding-agent` distribution.

Read [the Pi adapter](pi/docs/adapter.md) before using the upstream prose. Delegation inherits the active Pi model. The package does not configure paid providers or credentials.

## Compatibility

Both ports include 54 upstream skills and two agent profiles. `make-bot-ui` is excluded because its only workflow requires Cursor Automation routines, Cursor secret requests, and Cursor webhooks. The dormant `benny` automation pack remains in the source snapshot but is excluded from both installed packages. Optional steps invoking Bugbot, Cursor cloud dashboards, or skills from the separate `cursor-team-kit` plugin are mapped or reported unavailable by the adapters. No external service is installed implicitly.

The adapters are interpretation layers, not claims that every upstream workflow can run unchanged. Review source changes before merging a sync PR, especially agent and model instructions.

## Update from upstream

The scheduled workflow checks once daily and can be started with **Run workflow**. It compares the `pstack/` tree hash, so unrelated commits in `cursor/plugins` do nothing. When the tree changes, it updates only `upstream/pstack/`, merges safe text changes into the ports, and opens or updates one `sync/pstack` PR. New or removed skills, merge conflicts, and semantic changes appear in the PR report and `sync-pending.json`. The sync never merges its PR.

To run manually from a local checkout of `cursor/plugins`:

```sh
python scripts/pstack.py sync --source /path/to/plugins/pstack --commit FULL_COMMIT_SHA --tree PSTACK_TREE_SHA --report sync-report.md
python scripts/pstack.py check --allow-pending
```

After adapting the changed skills and resolving each report item, set their `compatibility.json` status back to `adapted` or `profile`, clear the corresponding `sync-pending.json` items, and run `python scripts/pstack.py check`. The updater may not run automatically until GitHub Actions is enabled for the published repository and its workflow is allowed to create pull requests.

## Development checks

```sh
python scripts/pstack.py check
python -m unittest discover -s tests
node --check pi/extensions/pstack-task.js
npm install --prefix .pi-smoke --no-save --ignore-scripts @earendil-works/pi-coding-agent@1.3.0
python scripts/check_pi_runtime.py
```

After publishing the repository, enable GitHub Actions to create pull requests and require the **Validate ports / validate** check on `main` through a branch protection rule. The sync workflow explicitly dispatches validation for its bot-created PR commit; unresolved compatibility items fail that check.

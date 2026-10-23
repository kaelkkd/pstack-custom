#!/usr/bin/env python3
"""Publish outstanding sync changes and maintain one open review PR."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def publish(report: Path, upstream_commit: str) -> None:
    changed = bool(run("git", "status", "--porcelain").stdout.strip())
    if changed:
        run("git", "config", "user.name", "github-actions[bot]")
        run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        if run("git", "branch", "--show-current").stdout.strip() != "sync/pstack":
            run("git", "switch", "-c", "sync/pstack")
        run("git", "add", "-A")
        run("git", "commit", "-m", f"chore: sync pstack from {upstream_commit[:12]}")

    difference = run("git", "diff", "--quiet", "origin/main", "HEAD", check=False)
    if difference.returncode == 0:
        print("No unpublished pstack changes")
        return
    if difference.returncode != 1:
        difference.check_returncode()

    remote = run("git", "rev-parse", "--verify", "refs/remotes/origin/sync/pstack", check=False)
    head = run("git", "rev-parse", "HEAD").stdout.strip()
    updated = remote.returncode != 0 or remote.stdout.strip() != head
    if updated:
        run("git", "push", "origin", "HEAD:refs/heads/sync/pstack")

    # A merged/closed PR must never absorb later syncs. Only reuse an open PR.
    number = run(
        "gh", "pr", "list", "--state", "open", "--base", "main", "--head", "sync/pstack",
        "--json", "number", "--jq", ".[0].number // empty",
    ).stdout.strip()
    if not changed and (updated or not number):
        lock = json.loads(Path("upstream-lock.json").read_text(encoding="utf-8"))
        pending = json.loads(Path("sync-pending.json").read_text(encoding="utf-8"))["items"]
        paths = run("git", "diff", "--name-only", "origin/main", "HEAD").stdout.splitlines()
        lines = [f"Upstream commit: `{lock['commit']}`", f"pstack tree: `{lock['tree']}`", "", "Changed files:"]
        lines.extend(f"- `{path}`" for path in paths)
        lines.extend(["", "Review required:"])
        lines.extend(f"- {item}" for item in pending)
        if not pending:
            lines.append("- None. Run validation before merging.")
        report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    title = f"Sync pstack {upstream_commit[:12]}"
    if number and (changed or updated):
        run("gh", "pr", "edit", number, "--title", title, "--body-file", str(report))
    elif not number:
        result = run("gh", "pr", "create", "--base", "main", "--head", "sync/pstack",
                     "--title", title, "--body-file", str(report))
        print(result.stdout.strip())
    else:
        print(f"Synchronization PR #{number} is already up to date")
    if updated or changed or not number:
        run("gh", "workflow", "run", "validate.yml", "--ref", "sync/pstack")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    try:
        publish(args.report, args.commit)
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.stderr or str(error)) from error

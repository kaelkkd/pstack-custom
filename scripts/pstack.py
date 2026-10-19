#!/usr/bin/env python3
"""Render pstack ports, synchronize one upstream subtree, and validate coverage."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "pstack"
LOCK = ROOT / "upstream-lock.json"
MATRIX = ROOT / "compatibility.json"
PENDING = ROOT / "sync-pending.json"
TARGETS = ("codex", "pi")
COPIED_ROOTS = ("skills", "agents", "docs/guide")
EXCLUDED_SKILLS = {
    "make-bot-ui": "requires Cursor Automation routines, SendToUser secret requests, and Cursor webhooks",
}
TEXT_SUFFIXES = {".md", ".json", ".ts", ".js", ".mjs", ".sh", ".txt", ".yaml", ".yml"}
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK = re.compile(r"\]\(([^)\s]+)\)")
ADAPTER_LINE = (
    "Platform port: read [the {platform} adapter](../../docs/adapter.md) once per session "
    "before following this skill. Its mappings override Cursor-specific tools, paths, models, and commands."
)
AGENT_LINE = (
    "Platform port: read [the {platform} adapter](../docs/adapter.md) before using this agent profile. "
    "The adapter overrides Cursor-specific instructions."
)


def files(root: Path) -> dict[str, Path]:
    return {
        p.relative_to(root).as_posix(): p
        for p in root.rglob("*")
        if p.is_file() and "node_modules" not in p.parts
    }


def supported(path: str) -> bool:
    if any(path.startswith(f"skills/{name}/") for name in EXCLUDED_SKILLS):
        return False
    return any(path == root or path.startswith(root + "/") for root in COPIED_ROOTS)


def insert_after_frontmatter(source: str, line: str) -> str:
    marker = "---\n"
    if not source.startswith(marker):
        raise ValueError("Missing YAML frontmatter")
    end = source.find("\n---\n", len(marker))
    if end < 0:
        raise ValueError("Unclosed YAML frontmatter")
    at = end + len("\n---\n")
    return source[:at] + "\n> " + line + "\n" + source[at:]


def render(path: str, data: bytes, platform: str) -> bytes:
    if path.startswith("skills/") and path.endswith("/SKILL.md"):
        text = data.decode("utf-8").replace("\r\n", "\n")
        if path == "skills/poteto-help/SKILL.md":
            text = text.replace("../../docs/harness/claude-code.md", "../../docs/adapter.md")
            text = "\n".join(line for line in text.split("\n") if "../make-bot-ui/SKILL.md" not in line)
        return insert_after_frontmatter(text, ADAPTER_LINE.format(platform=platform)).encode("utf-8")
    if path.startswith("agents/") and path.endswith(".md"):
        text = data.decode("utf-8").replace("\r\n", "\n")
        return insert_after_frontmatter(text, AGENT_LINE.format(platform=platform)).encode("utf-8")
    if path.startswith("docs/guide/") and path.endswith(".md"):
        text = data.decode("utf-8").replace("\r\n", "\n")
        text = text.replace("../harness/claude-code.md", "../adapter.md")
        for name in ("README.md", "FOR_AGENTS.md"):
            text = text.replace(
                f"../../automations/benny/{name}",
                f"https://github.com/cursor/plugins/blob/main/pstack/automations/benny/{name}",
            )
        if path == "docs/guide/09-make-it-yours.md":
            text = text.replace(
                "[`/make-bot-ui`](../../skills/make-bot-ui/SKILL.md)",
                "[`/make-bot-ui`](https://github.com/cursor/plugins/blob/main/pstack/skills/make-bot-ui/SKILL.md) (Cursor-only; excluded from this port)",
            )
        return (
            f"> {platform.title()} port: read [the platform adapter](../adapter.md) for tool and path mappings.\n\n"
            + text
        ).encode("utf-8")
    return data


def copy_initial() -> None:
    source = files(UPSTREAM)
    for platform in TARGETS:
        dest = ROOT / platform
        for path, src in source.items():
            if not supported(path):
                continue
            target = dest / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(render(path, src.read_bytes(), platform))
            shutil.copymode(src, target)
        shutil.copy2(UPSTREAM / "LICENSE", dest / "LICENSE")
    items = []
    for path in sorted(source):
        if path.startswith("skills/") and path.endswith("/SKILL.md"):
            name = Path(path).parent.name
            if name in EXCLUDED_SKILLS:
                reason = EXCLUDED_SKILLS[name]
                items.append({"source": path, "codex": f"excluded: {reason}", "pi": f"excluded: {reason}"})
            else:
                items.append({"source": path, "codex": "adapted", "pi": "adapted"})
        elif path.startswith("agents/") and path.endswith(".md"):
            items.append({"source": path, "codex": "profile", "pi": "profile"})
    items.append({
        "source": "automations/benny/",
        "codex": "excluded: Cursor Automations and Slack integration are not part of the Codex plugin runtime",
        "pi": "excluded: Cursor Automations and Slack integration are not part of the Pi package runtime",
    })
    MATRIX.write_text(json.dumps({"entries": items}, indent=2) + "\n", encoding="utf-8")
    print(f"Rendered {len(items) - 1} skills and agents for Codex and Pi")


def merge_text(base: bytes, ours: bytes, theirs: bytes) -> bytes | None:
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        for name, data in (("base", base), ("ours", ours), ("theirs", theirs)):
            (temp / name).write_bytes(data)
        result = subprocess.run(
            ["git", "merge-file", "-p", str(temp / "ours"), str(temp / "base"), str(temp / "theirs")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout
        if result.returncode == 1:
            return None
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))


def synchronize(source_dir: Path, commit: str, tree: str, report_path: Path) -> int:
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or not re.fullmatch(r"[0-9a-f]{40}", tree):
        raise ValueError("Commit and tree must be full Git SHA-1 values")
    old_lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if old_lock["tree"] == tree:
        report_path.write_text("No changes under pstack/.\n", encoding="utf-8")
        print("No pstack changes")
        return 0
    old = files(UPSTREAM)
    new = files(source_dir)
    changed = sorted(
        p for p in set(old) | set(new)
        if p not in old or p not in new or old[p].read_bytes() != new[p].read_bytes()
    )
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    by_source = {item["source"]: item for item in matrix["entries"]}
    review: list[str] = []
    for path in changed:
        if not supported(path):
            continue
        for platform in TARGETS:
            destination = ROOT / platform / path
            if path not in old or path not in new:
                review.append(f"{platform}: {'new' if path not in old else 'removed'} {path}")
                continue
            if not destination.exists():
                review.append(f"{platform}: missing target {path}")
                continue
            base = render(path, old[path].read_bytes(), platform)
            theirs = render(path, new[path].read_bytes(), platform)
            ours = destination.read_bytes()
            if ours == base:
                destination.write_bytes(theirs)
            elif Path(path).suffix.lower() in TEXT_SUFFIXES:
                merged = merge_text(base, ours, theirs)
                if merged is None:
                    review.append(f"{platform}: merge conflict {path}")
                else:
                    destination.write_bytes(merged)
            else:
                review.append(f"{platform}: binary conflict {path}")
            if path.startswith(("skills/", "agents/")):
                review.append(f"{platform}: semantic review {path}")
                if path in by_source:
                    by_source[path][platform] = "review-required"
        if path.startswith(("skills/", "agents/")) and path not in by_source:
            item = {"source": path, "codex": "review-required", "pi": "review-required"}
            matrix["entries"].append(item)
            by_source[path] = item
    for path, src in old.items():
        if path not in new:
            src.unlink()
    for path, src in new.items():
        target = UPSTREAM / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(src.read_bytes())
        shutil.copymode(src, target)
    if "LICENSE" in changed:
        for target in (ROOT / "LICENSE", ROOT / "codex" / "LICENSE", ROOT / "pi" / "LICENSE"):
            target.write_bytes((UPSTREAM / "LICENSE").read_bytes())
    LOCK.write_text(json.dumps({"repository": old_lock["repository"], "commit": commit, "tree": tree}, indent=2) + "\n", encoding="utf-8")
    matrix["entries"].sort(key=lambda item: item["source"])
    MATRIX.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    previous_pending = json.loads(PENDING.read_text(encoding="utf-8"))["items"] if PENDING.exists() else []
    pending = sorted(set(previous_pending) | set(review))
    PENDING.write_text(json.dumps({"items": pending}, indent=2) + "\n", encoding="utf-8")
    lines = [f"Upstream commit: `{commit}`", f"pstack tree: `{tree}`", "", "Changed source files:"]
    lines.extend(f"- `{path}`" for path in changed)
    lines.extend(["", "Review required:"])
    lines.extend(f"- {item}" for item in pending)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated upstream snapshot; {len(changed)} changed files; {len(review)} review items")
    return 0


def check(allow_pending: bool = False) -> int:
    problems: list[str] = []
    source = files(UPSTREAM)
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if not re.fullmatch(r"[0-9a-f]{40}", lock["commit"]):
        problems.append("invalid upstream commit")
    if not re.fullmatch(r"[0-9a-f]{40}", lock["tree"]):
        problems.append("invalid upstream tree")
    if (ROOT / "LICENSE").read_bytes() != (UPSTREAM / "LICENSE").read_bytes():
        problems.append("upstream license missing at repository root")
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    pending_items = set(json.loads(PENDING.read_text(encoding="utf-8"))["items"]) if PENDING.exists() else set()
    if pending_items and not allow_pending:
        problems.append("sync-pending.json still contains review items")
    entries = {item["source"]: item for item in matrix["entries"]}
    expected = {
        path for path in source
        if (path.startswith("skills/") and path.endswith("/SKILL.md"))
        or (path.startswith("agents/") and path.endswith(".md"))
    }
    expected.add("automations/benny/")
    if set(entries) != expected and not allow_pending:
        problems.append(f"matrix mismatch: missing={sorted(expected - set(entries))}, extra={sorted(set(entries) - expected)}")
    for platform in TARGETS:
        package = ROOT / platform
        for path in expected - {"automations/benny/"}:
            item = entries.get(path, {})
            status = item.get(platform, "")
            if status == "review-required" and not allow_pending:
                problems.append(f"{platform}/{path} needs review")
            if status not in {"adapted", "profile", "review-required"} and not status.startswith("excluded: "):
                problems.append(f"invalid status for {platform}/{path}: {status}")
            target = package / path
            if status.startswith("excluded: "):
                if target.exists():
                    problems.append(f"excluded skill is installed: {platform}/{path}")
                continue
            if not target.is_file() and status != "review-required":
                problems.append(f"missing {platform}/{path}")
            if path.endswith("/SKILL.md") and target.is_file():
                text = target.read_text(encoding="utf-8")
                name = Path(path).parent.name
                if not SKILL_NAME.fullmatch(name) or f"name: {name}" not in text.split("---", 2)[1]:
                    problems.append(f"invalid skill frontmatter {platform}/{path}")
                if "docs/adapter.md" not in text:
                    problems.append(f"adapter missing from {platform}/{path}")
        if not (package / "docs" / "adapter.md").is_file():
            problems.append(f"missing {platform} adapter")
        if (package / "LICENSE").read_bytes() != (UPSTREAM / "LICENSE").read_bytes():
            problems.append(f"license mismatch in {platform}")
        for markdown in package.rglob("*.md"):
            for match in LINK.finditer(markdown.read_text(encoding="utf-8")):
                href = match.group(1).split("#", 1)[0].split("?", 1)[0]
                if not href or href == "url" or href.startswith(("/", "mailto:")) or "://" in href:
                    continue
                target = (markdown.parent / href).resolve()
                if not target.exists():
                    try:
                        relative_target = target.relative_to(package.resolve()).as_posix()
                    except ValueError:
                        relative_target = ""
                    if allow_pending and f"{platform}: new {relative_target}" in pending_items:
                        continue
                    problems.append(f"broken link in {markdown.relative_to(ROOT)}: {href}")
        if any((package / "skills").rglob("make-bot-ui/SKILL.md")):
            problems.append(f"Cursor-only make-bot-ui installed in {platform}")
    codex_manifest = json.loads((ROOT / "codex" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    pi_manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
    if codex_manifest.get("skills") != "./skills/" or not (ROOT / "codex" / "skills").is_dir():
        problems.append("invalid Codex skill manifest")
    if pi_manifest.get("pi", {}).get("skills") != ["./pi/skills"]:
        problems.append("invalid Pi skill manifest")
    if pi_manifest.get("pi", {}).get("extensions") != ["./pi/extensions/pstack-task.js"]:
        problems.append("invalid Pi extension manifest")
    if not (ROOT / "pi" / "extensions" / "pstack-task.js").is_file():
        problems.append("missing Pi delegation extension")
    if marketplace.get("plugins", [{}])[0].get("source", {}).get("path") != "./codex":
        problems.append("Codex marketplace does not point at codex/")
    for problem in problems:
        print("FAIL", problem)
    if problems:
        return 1
    print(f"OK: {len(expected) - 1} skills and agents mapped")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("render-initial")
    sync = sub.add_parser("sync")
    sync.add_argument("--source", type=Path, required=True)
    sync.add_argument("--commit", required=True)
    sync.add_argument("--tree", required=True)
    sync.add_argument("--report", type=Path, required=True)
    verify = sub.add_parser("check")
    verify.add_argument("--allow-pending", action="store_true")
    args = parser.parse_args()
    if args.command == "render-initial":
        copy_initial()
        return 0
    if args.command == "sync":
        return synchronize(args.source, args.commit, args.tree, args.report)
    return check(args.allow_pending)


if __name__ == "__main__":
    sys.exit(main())

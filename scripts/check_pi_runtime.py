#!/usr/bin/env python3
"""Smoke-test a local Pi package installation without provider credentials."""

import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / ".pi-smoke" / "node_modules" / "@earendil-works" / "pi-coding-agent" / "dist" / "bundle" / "cli.js"


def main() -> None:
    if not CLI.is_file():
        raise SystemExit(f"Pi CLI is missing: {CLI}")
    matrix = json.loads((ROOT / "compatibility.json").read_text(encoding="utf-8"))
    expected = {
        "skill:" + Path(entry["source"]).parent.name
        for entry in matrix["entries"]
        if entry["source"].startswith("skills/") and entry["pi"] == "adapted"
    }
    with tempfile.TemporaryDirectory(prefix="pstack-pi-agent-") as agent_dir:
        env = os.environ.copy()
        env["PI_CODING_AGENT_DIR"] = agent_dir
        subprocess.run(["node", str(CLI), "install", str(ROOT)], check=True, env=env, cwd=ROOT, capture_output=True, text=True)
        result = subprocess.run(
            ["node", str(CLI), "--mode", "rpc", "--no-session"],
            input=json.dumps({"id": "skills", "type": "get_commands"}) + "\n",
            check=True,
            env=env,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
    if result.stderr.strip():
        raise SystemExit(f"Pi startup diagnostics: {result.stderr}")
    records = [json.loads(line) for line in result.stdout.splitlines()]
    response = next((record for record in records if record.get("id") == "skills"), None)
    if not response or not response.get("success"):
        raise SystemExit(f"Pi command discovery failed: {result.stdout}")
    found = {
        item["name"]
        for item in response["data"]["commands"]
        if item["source"] == "skill"
    }
    if found != expected:
        raise SystemExit(f"Pi skills mismatch: missing={sorted(expected - found)}, extra={sorted(found - expected)}")
    print(f"Pi installed and loaded {len(found)} pstack skills")


if __name__ == "__main__":
    main()

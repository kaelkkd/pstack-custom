#!/usr/bin/env python3
"""Exercise each installed port with real TLC, including paths with spaces."""

import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = r"""---- MODULE Sample ----
EXTENDS Naturals
VARIABLE n
Init == n = 0
Inc == n < 2 /\ n' = n + 1
Done == n = 2 /\ UNCHANGED n
Next == Inc \/ Done
Safe == n <= LIMIT
====
"""


def main():
    if not os.environ.get("TLA2TOOLS"):
        raise SystemExit("Set TLA2TOOLS to tla2tools.jar before running this check")
    if not Path(os.environ["TLA2TOOLS"]).is_file():
        raise SystemExit(f"TLA2TOOLS file is missing: {os.environ['TLA2TOOLS']}")
    with tempfile.TemporaryDirectory(prefix="pstack statechart ") as folder:
        scratch = Path(folder)
        for platform in ("codex", "pi"):
            cli = ROOT / platform / "skills/statechart/scripts/statechart.ts"
            for name, limit, expected in (("valid", 2, 0), ("bug", 1, 1)):
                case = scratch / platform / name
                case.mkdir(parents=True)
                spec = case / "Sample.tla"
                spec.write_text(SPEC.replace("LIMIT", str(limit)), encoding="utf-8")
                spec.with_suffix(".cfg").write_text("INIT Init\nNEXT Next\nINVARIANT Safe\n", encoding="utf-8")
                output = case / "result with spaces"
                if name == "valid":
                    output.mkdir()
                command = ["node", "--disable-warning=ExperimentalWarning", str(cli), str(spec), "--out", str(output)]
                result = subprocess.run(command, capture_output=True, text=True, timeout=120)
                if result.returncode != expected:
                    raise SystemExit(f"{platform}/{name}: expected {expected}, got {result.returncode}\n{result.stdout}\n{result.stderr}")
                report = (output / "report.md").read_text(encoding="utf-8")
                if not (output / "chart.mmd").is_file() or (name == "bug" and "Safe" not in report):
                    raise SystemExit(f"{platform}/{name}: chart or expected finding missing")
                original = (output / "report.md").read_bytes()
                retry = subprocess.run(command, capture_output=True, text=True, timeout=30)
                if retry.returncode != 2 or (output / "report.md").read_bytes() != original:
                    raise SystemExit(f"{platform}/{name}: existing output was not protected")
            print(f"{platform}: real TLC pass and counterexample rendered; existing output preserved")


if __name__ == "__main__":
    main()

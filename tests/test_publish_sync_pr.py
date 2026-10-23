import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "publish_sync_pr", Path(__file__).resolve().parents[1] / "scripts" / "publish_sync_pr.py"
)
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        previous = Path.cwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, previous)
        Path("upstream-lock.json").write_text(json.dumps({"commit": "a" * 40, "tree": "b" * 40}))
        Path("sync-pending.json").write_text(json.dumps({"items": ["codex: new skills/example/SKILL.md"]}))
        self.report = Path("report.md")
        self.report.write_text("Fresh sync report\n")
        self.dirty = False
        self.diff_status = 1
        self.head = "current"
        self.remote = "current"
        self.open_pr = ""
        self.calls = []
        self.enterContext(patch.object(publisher, "run", side_effect=self.command))

    def command(self, *args, check=True):
        self.calls.append(args)
        outputs = {
            ("git", "status", "--porcelain"): " M compatibility.json\n" if self.dirty else "",
            ("git", "branch", "--show-current"): "sync/pstack\n",
            ("git", "rev-parse", "--verify", "refs/remotes/origin/sync/pstack"): self.remote,
            ("git", "rev-parse", "HEAD"): self.head,
            ("git", "diff", "--name-only", "origin/main", "HEAD"): "codex/skills/example/SKILL.md\n",
        }
        code = self.diff_status if args == ("git", "diff", "--quiet", "origin/main", "HEAD") else 0
        output = self.open_pr if args[:3] == ("gh", "pr", "list") else outputs.get(args, "")
        return subprocess.CompletedProcess(args, code, output, "git diff failed" if code > 1 else "")

    def actions(self, *prefix):
        return [args for args in self.calls if args[:len(prefix)] == prefix]

    def test_merged_pr_is_replaced_even_without_new_upstream_changes(self):
        publisher.publish(self.report, "a" * 40)
        listing = self.actions("gh", "pr", "list")[0]
        self.assertEqual(listing[listing.index("--state") + 1], "open")
        self.assertEqual(len(self.actions("gh", "pr", "create")), 1)
        self.assertFalse(self.actions("gh", "pr", "edit"))
        self.assertIn("codex: new skills/example/SKILL.md", self.report.read_text())
        self.assertEqual(len(self.actions("gh", "workflow", "run")), 1)

    def test_unchanged_open_pr_is_idempotent(self):
        self.open_pr = "3"
        publisher.publish(self.report, "a" * 40)
        self.assertFalse(self.actions("git", "push"))
        self.assertFalse(self.actions("gh", "pr", "create"))
        self.assertFalse(self.actions("gh", "pr", "edit"))
        self.assertFalse(self.actions("gh", "workflow", "run"))

    def test_new_changes_update_the_open_pr(self):
        self.dirty = True
        self.remote = "old"
        self.open_pr = "3"
        publisher.publish(self.report, "a" * 40)
        self.assertEqual(len(self.actions("git", "commit")), 1)
        self.assertEqual(len(self.actions("git", "push")), 1)
        self.assertEqual(self.actions("gh", "pr", "edit")[0][3], "3")
        self.assertEqual(self.report.read_text(), "Fresh sync report\n")

    def test_committed_changes_are_published_after_merging_main(self):
        self.remote = "old"
        self.open_pr = "3"
        publisher.publish(self.report, "a" * 40)
        self.assertFalse(self.actions("git", "commit"))
        self.assertEqual(len(self.actions("git", "push")), 1)
        self.assertEqual(len(self.actions("gh", "pr", "edit")), 1)
        self.assertEqual(len(self.actions("gh", "workflow", "run")), 1)

    def test_merged_contents_do_not_open_an_empty_pr(self):
        self.diff_status = 0
        publisher.publish(self.report, "a" * 40)
        self.assertFalse(self.actions("gh"))

    def test_git_error_is_not_treated_as_a_change(self):
        self.diff_status = 128
        with self.assertRaises(subprocess.CalledProcessError):
            publisher.publish(self.report, "a" * 40)
        self.assertFalse(self.actions("gh"))


if __name__ == "__main__":
    unittest.main()

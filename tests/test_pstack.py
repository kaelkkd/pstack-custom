import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "pstack.py"
spec = importlib.util.spec_from_file_location("pstack_sync", MODULE_PATH)
pstack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pstack)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old_constants = (pstack.ROOT, pstack.UPSTREAM, pstack.LOCK, pstack.MATRIX, pstack.PENDING)
        pstack.ROOT = self.root
        pstack.UPSTREAM = self.root / "upstream" / "pstack"
        pstack.LOCK = self.root / "upstream-lock.json"
        pstack.MATRIX = self.root / "compatibility.json"
        pstack.PENDING = self.root / "sync-pending.json"
        self.write(pstack.UPSTREAM / "skills" / "example" / "SKILL.md", "---\nname: example\ndescription: Test\n---\n\n# Example\nOld line.\n")
        self.write(pstack.UPSTREAM / "agents" / "worker.md", "---\nname: worker\n---\n\n# Worker\n")
        self.write(pstack.UPSTREAM / "docs" / "guide" / "example.md", "# Guide\n")
        self.write(pstack.UPSTREAM / "LICENSE", "MIT fixture\n")
        self.write(self.root / "LICENSE", "MIT fixture\n")
        self.write(pstack.LOCK, json.dumps({"repository": "https://github.com/cursor/plugins", "commit": "a" * 40, "tree": "b" * 40}))
        pstack.copy_initial()
        for platform in pstack.TARGETS:
            self.write(self.root / platform / "docs" / "adapter.md", "adapter\n")
            self.write(self.root / platform / "extensions" / "pstack-task.js", "// fixture\n")
        self.write(self.root / "codex" / ".codex-plugin" / "plugin.json", json.dumps({"skills": "./skills/"}))
        self.write(self.root / "package.json", json.dumps({"pi": {"skills": ["./pi/skills"], "extensions": ["./pi/extensions/pstack-task.js"]}}))
        self.write(self.root / ".agents" / "plugins" / "marketplace.json", json.dumps({"plugins": [{"source": {"path": "./codex"}}]}))

    def tearDown(self):
        pstack.ROOT, pstack.UPSTREAM, pstack.LOCK, pstack.MATRIX, pstack.PENDING = self.old_constants
        self.temp.cleanup()

    @staticmethod
    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def new_source(self):
        source = self.root / "incoming"
        for path, original in pstack.files(pstack.UPSTREAM).items():
            target = source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original.read_bytes())
        return source

    def sync(self, source, tree="c" * 40):
        report = self.root / "report.md"
        pstack.synchronize(source, "d" * 40, tree, report)
        return report.read_text(encoding="utf-8")

    def test_unrelated_commit_does_not_update(self):
        source = self.new_source()
        report = self.sync(source, "b" * 40)
        self.assertEqual(report, "No changes under pstack/.\n")
        self.assertEqual(json.loads(pstack.LOCK.read_text())["commit"], "a" * 40)

    def test_changed_skill_updates_both_ports_and_requires_review(self):
        source = self.new_source()
        skill = source / "skills" / "example" / "SKILL.md"
        skill.write_text(skill.read_text().replace("Old line.", "New line."), encoding="utf-8")
        report = self.sync(source)
        for platform in pstack.TARGETS:
            self.assertIn("New line.", (self.root / platform / "skills" / "example" / "SKILL.md").read_text())
            self.assertIn(f"{platform}: semantic review skills/example/SKILL.md", report)
        self.assertEqual(pstack.check(allow_pending=True), 0)
        self.assertEqual(pstack.check(), 1)

    def test_conflict_keeps_previous_port(self):
        source = self.new_source()
        skill = source / "skills" / "example" / "SKILL.md"
        skill.write_text(skill.read_text().replace("Old line.", "New upstream line."), encoding="utf-8")
        target = self.root / "codex" / "skills" / "example" / "SKILL.md"
        target.write_text(target.read_text().replace("Old line.", "Local adaptation."), encoding="utf-8")
        report = self.sync(source)
        self.assertIn("codex: merge conflict skills/example/SKILL.md", report)
        self.assertIn("Local adaptation.", target.read_text())
        self.assertNotIn("New upstream line.", target.read_text())

    def test_added_and_removed_skills_are_pending(self):
        source = self.new_source()
        (source / "skills" / "example" / "SKILL.md").unlink()
        self.write(source / "skills" / "added" / "SKILL.md", "---\nname: added\ndescription: Test\n---\n\n# Added\n")
        report = self.sync(source)
        self.assertIn("new skills/added/SKILL.md", report)
        self.assertIn("removed skills/example/SKILL.md", report)
        self.assertFalse((self.root / "codex" / "skills" / "added").exists())
        self.assertEqual(pstack.check(allow_pending=True), 0)
        self.assertEqual(pstack.check(), 1)

    def test_new_skill_links_wait_for_review(self):
        source = self.new_source()
        self.write(source / "skills" / "added" / "SKILL.md", "---\nname: added\ndescription: Test\n---\n\n# Added\n")
        self.write(source / "docs" / "guide" / "example.md", "[New skill](../../skills/added/SKILL.md)\n")
        report = self.sync(source)
        self.assertIn("codex: new skills/added/SKILL.md", report)
        self.assertEqual(pstack.check(allow_pending=True), 0)
        self.assertEqual(pstack.check(), 1)

    def test_unrelated_broken_link_still_fails_with_pending(self):
        source = self.new_source()
        self.write(source / "skills" / "added" / "SKILL.md", "---\nname: added\ndescription: Test\n---\n\n# Added\n")
        self.sync(source)
        self.write(self.root / "codex" / "docs" / "guide" / "example.md", "[Broken](../../skills/other/SKILL.md)\n")
        self.assertEqual(pstack.check(allow_pending=True), 1)

    def test_changed_skill_reference_does_not_become_matrix_entry(self):
        self.write(pstack.UPSTREAM / "skills" / "example" / "references" / "recipe.md", "Old recipe\n")
        for platform in pstack.TARGETS:
            self.write(self.root / platform / "skills" / "example" / "references" / "recipe.md", "Old recipe\n")
        source = self.new_source()
        self.write(source / "skills" / "example" / "references" / "recipe.md", "New recipe\n")
        report = self.sync(source)
        self.assertIn("semantic review skills/example/references/recipe.md", report)
        entries = json.loads(pstack.MATRIX.read_text(encoding="utf-8"))["entries"]
        self.assertNotIn("skills/example/references/recipe.md", {item["source"] for item in entries})

    def test_later_sync_keeps_unresolved_review_items(self):
        source = self.new_source()
        self.write(source / "docs" / "guide" / "new.md", "# New\n")
        self.sync(source)
        original_items = json.loads(pstack.PENDING.read_text(encoding="utf-8"))["items"]
        self.assertIn("codex: new docs/guide/new.md", original_items)
        source = self.new_source()
        self.write(source / "skills" / "example" / "SKILL.md", "---\nname: example\ndescription: Test\n---\n\n# Example\nUpdated.\n")
        self.sync(source, "e" * 40)
        items = json.loads(pstack.PENDING.read_text(encoding="utf-8"))["items"]
        self.assertTrue(set(original_items).issubset(items))
        self.assertIn("codex: semantic review skills/example/SKILL.md", items)

    def test_adapted_skill_requires_its_resources(self):
        resource = Path("skills/example/scripts/run.mjs")
        self.write(pstack.UPSTREAM / resource, "console.log('example');\n")
        self.assertEqual(pstack.check(), 1)
        for platform in pstack.TARGETS:
            self.write(self.root / platform / resource, "console.log('example');\n")
        self.assertEqual(pstack.check(), 0)


if __name__ == "__main__":
    unittest.main()

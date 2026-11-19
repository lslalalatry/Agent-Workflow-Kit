"""Regressions for two chats sharing one real Git worktree."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(os.environ.get("GUARDIAN_TEST_SKILL", Path(__file__).resolve().parents[1] / "skills/project-guardian"))
SCRIPTS = SKILL / "scripts"


class SharedDecisionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.area = Path(temp.name)
        self.root = self.area / "project"
        self.root.mkdir()
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_NOSYSTEM="1",
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_AUTHOR_NAME="Fixture", GIT_COMMITTER_NAME="Fixture",
                        GIT_AUTHOR_EMAIL="test@example.invalid", GIT_COMMITTER_EMAIL="test@example.invalid")
        self.cmd("git", "init", "-b", "main")
        link = self.root / ".agents/skills/project-guardian"
        link.parent.mkdir(parents=True)
        link.symlink_to(SKILL, target_is_directory=True)
        (self.root / ".git/info/exclude").write_text("/.agents/\n")
        self.cmd(sys.executable, SCRIPTS / "init_project.py", ".", "--minimal")
        self.docs = self.root / "docs/tracking"
        (self.docs / "SPEC.md").write_text("Live: simple average 15.\nOwner: operations.\n")
        (self.docs / "TODO.md").write_text("| T1 | [ ] | Verify default price |\n| T9 | [ ] | Keep date |\n")
        (self.docs / "FORMULA.md").write_text("Current definition: simple average.\n")
        self.cmd("git", "add", ".")
        self.cmd("git", "commit", "-m", "existing project with no decision ledger")

    def cmd(self, *args, ok=True):
        proc = subprocess.run(args, cwd=self.root, env=self.env, capture_output=True, text=True)
        self.assertEqual(proc.returncode == 0, ok, proc.stdout + proc.stderr)
        return proc.stdout + proc.stderr

    def draft(self, name):
        path = self.area / name
        self.cmd(sys.executable, SCRIPTS / "chat_sync.py", "read", "--draft", path)
        return path

    def approve(self, path, ident, message):
        for name in ("DECISIONS.md", "TODO.md", "SPEC.md", "FORMULA.md"):
            with (path / name).open("a") as out:
                out.write(f"\n{ident} {message}\n")
        return [sys.executable, SCRIPTS / "chat_sync.py", "apply", "--draft", path, "--decision", ident,
                "--affects", "TODO.md", "SPEC.md", "FORMULA.md"]

    def test_stale_version_partial_staging_and_handoff(self):
        stale = self.draft("old-chat")
        a = self.draft("deciding-chat")
        args = self.approve(a, "D-018", "Approved: weighted mean 19. Implementation pending.")
        self.cmd(*args)
        stale_args = self.approve(stale, "D-018", "Exclude refunded units.")
        self.assertIn("草稿过期", self.cmd(*stale_args, ok=False))
        fresh = self.draft("reread")
        self.assertIn("weighted mean 19", (fresh / "FORMULA.md").read_text())
        self.cmd(*self.approve(fresh, "D-019", "Amend D-018: exclude refunded units. Pending."))
        # A partial stage in either direction must fail in a real commit.
        self.cmd("git", "add", "docs/tracking/SPEC.md")
        self.assertIn("缺少对应", self.cmd("git", "commit", "-m", "spec alone", ok=False))
        self.cmd("git", "add", "docs/tracking/DECISIONS.md")
        self.assertIn("缺少同时交付", self.cmd("git", "commit", "-m", "missing formula and TODO", ok=False))
        self.cmd("git", "add", "docs/tracking")
        self.assertIn("安检绿灯通过", self.cmd("git", "commit", "-m", "two complete decisions"))
        for name in ("DECISIONS.md", "TODO.md", "SPEC.md", "FORMULA.md"):
            text = self.cmd("git", "show", f"HEAD:docs/tracking/{name}")
            self.assertIn("D-018", text)
            self.assertIn("D-019", text)
        self.assertIn("Owner: operations.", (self.docs / "SPEC.md").read_text())
        self.assertIn("| T9 | [ ]", (self.docs / "TODO.md").read_text())

    def test_concurrent_writers_only_one_publishes(self):
        one, two = self.draft("one"), self.draft("two")
        cmds = [self.approve(one, "D-001", "A weighted mean"), self.approve(two, "D-001", "B median")]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda c: subprocess.run(c, env=self.env, cwd=self.root, capture_output=True, text=True), cmds))
        self.assertEqual(sorted(x.returncode for x in results), [0, 1])
        self.assertTrue(any("草稿过期" in r.stderr for r in results))
        winner = "A weighted mean" if results[0].returncode == 0 else "B median"
        for name in ("DECISIONS.md", "TODO.md", "SPEC.md", "FORMULA.md"):
            self.assertIn(winner, (self.docs / name).read_text())

    def test_decision_only_edit_preserves_running_formula_evidence(self):
        config = {"prices": {"argv": [sys.executable, "-c", 'print("{\\"normal\\":15,\\"boundary\\":null,\\"counterexample\\":15}")'],
                             "paths": ["calculator.py"], "cases": {key: {"input": [], "expected": value}
                                for key, value in (("normal", 15), ("boundary", None), ("counterexample", 15))}}}
        with (self.docs / "FORMULA.md").open("a") as out:
            out.write("\n```guardian-formula\n" + json.dumps(config) + "\n```\n")
        self.cmd("git", "add", ".")
        self.cmd(sys.executable, SCRIPTS / "acceptance.py", "prices")
        self.cmd("git", "add", ".")
        self.cmd("git", "commit", "-m", "registered current formula")
        # A handoff in another checkout has no local observation of the old formula.
        witness = self.root / ".git/project-guardian/observed/prices.json"
        witness.unlink()
        self.cmd(*self.approve(self.draft("approval"), "D-042", "approved next contract, implementation pending"))
        self.cmd("git", "add", "docs/tracking")
        self.assertIn("安检绿灯通过", self.cmd("git", "commit", "-m", "approved future requirement"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

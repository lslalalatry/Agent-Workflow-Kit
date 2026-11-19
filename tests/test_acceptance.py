"""End-to-end regressions. Use a temporary project with the candidate's actual Git hook."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

if __package__:
    from .review_fixture import record_fixture_review
else:
    from review_fixture import record_fixture_review

SKILL = Path(os.environ.get("GUARDIAN_TEST_SKILL", Path(__file__).resolve().parents[1] / "skills/project-guardian"))
SCRIPTS = SKILL / "scripts"


def block(tag, config):
    return f"\n```guardian-{tag}\n{json.dumps(config, ensure_ascii=False)}\n```\n"


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.root = Path(work.name)
        self.docs = self.root / "docs/tracking"
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME="Fixture", GIT_COMMITTER_NAME="Fixture",
                        GIT_AUTHOR_EMAIL="qa@example.invalid", GIT_COMMITTER_EMAIL="qa@example.invalid",
                        PYTHONDONTWRITEBYTECODE="1")
        self.call("git", "init", "-b", "main")
        local_skill = self.root / ".agents/skills/project-guardian"
        local_skill.parent.mkdir(parents=True)
        local_skill.symlink_to(SKILL, target_is_directory=True)
        (self.root / ".git/info/exclude").write_text("/.agents/\n")

    def call(self, *argv, ok=True):
        run = subprocess.run(argv, cwd=self.root, env=self.env, capture_output=True, text=True)
        output = run.stdout + run.stderr
        self.assertEqual(run.returncode == 0, ok, output)
        return output

    def init(self, *flags, ok=True):
        return self.call(sys.executable, str(SCRIPTS / "init_project.py"), ".", *flags, ok=ok)

    def commit(self, msg, ok=True):
        record_fixture_review(self.call, SCRIPTS)
        output = self.call("git", "commit", "-m", msg, ok=ok)
        self.assertIn("安检绿灯通过" if ok else "安检红灯拦截", output)
        return output

    def record(self, ident, ok=True):
        return self.call(sys.executable, str(SCRIPTS / "acceptance.py"), ident, ok=ok)

    def status(self, msg):
        with (self.docs / "STATUS.md").open("a") as out:
            out.write("\n" + msg + "\n")

    def test_default_entry_observes_the_real_batch(self):
        self.init()
        (self.root / "batch.json").write_text('{"A":2,"B":17}')
        app = self.root / "dashboard.py"
        app.write_text("import json,sys\nb=(sys.argv[1:] or ['A'])[0]\n"
                       "print(json.dumps({'entrypoint':'dashboard','data':b,'actual':json.load(open('batch.json'))[b]}))\n")
        cfg = {"dashboard": {"covers": ["T1", "M1"], "entrypoint": "dashboard", "data": "B", "expected": 17,
                             "argv": [sys.executable, "dashboard.py"]}}
        (self.docs / "SPEC.md").write_text("从默认入口看 B 批次总计 17。\n" + block("default", cfg))
        todo = self.docs / "TODO.md"
        todo.write_text("| T1 | [~] | 默认入口读 B 批次 |\n")
        self.call("git", "add", ".")
        self.commit("baseline")
        self.assertEqual(json.loads(self.call(sys.executable, "dashboard.py", "B"))["actual"], 17)
        self.status("候选预览为 17")
        self.call("git", "add", "docs/tracking/STATUS.md")
        self.commit("candidate preview")
        todo.write_text(todo.read_text().replace("[~]", "[x]"))
        self.call("git", "add", "docs/tracking/TODO.md")
        self.assertIn("缺少本次实测", self.commit("completion with no evidence", ok=False))
        self.assertIn('"actual":2', self.record("dashboard", ok=False))
        app.write_text(app.read_text().replace("or ['A']", "or ['B']"))
        self.status("默认入口已切换")
        self.call("git", "add", ".")
        self.record("dashboard")
        self.call("git", "add", "docs/tracking/evidence")
        self.commit("verified current default")
        self.assertEqual(json.loads(self.call(sys.executable, "dashboard.py"))["actual"], 17)
        fixed = app.read_text()
        app.write_text(fixed.replace("or ['B']", "or ['A']"))
        self.status("维护已验收入口")
        self.call("git", "add", ".")
        self.assertIn("证据与当前候选版本", self.commit("regression after acceptance", ok=False))
        status = self.docs / "STATUS.md"
        status.write_text(status.read_text().replace("0 / N` | `[ ] 待开始", "0 / N` | `[x] 已验收", 1))
        app.write_text(fixed.replace("or ['B']", "or ['A']"))
        self.call("git", "add", ".")
        self.assertIn("证据与当前候选版本", self.commit("milestone with stale evidence", ok=False))

    def test_formula_compares_all_three_cases_against_production(self):
        self.init("--with-formula")
        prod = self.root / "price.py"
        correct = "def price(rows):\n    n=sum(q for p,q in rows)\n    return sum(p*q for p,q in rows)//n if n else None\n"
        prod.write_text(correct)
        (self.root / "observe.py").write_text("import json,sys\nfrom price import price\n"
                                              "print(json.dumps({k:price(v) for k,v in json.load(sys.stdin).items()}))\n")
        cfg = {"weighted-price":{"paths":["price.py","observe.py"],"argv":[sys.executable,"observe.py"],"cases":{
            "normal":{"input":[[10,2],[20,2]],"expected":15}, "boundary":{"input":[],"expected":None},
            "counterexample":{"input":[[10,1],[20,9]],"expected":19}}}}
        with (self.docs/"FORMULA.md").open("a") as out:
            out.write(block("formula", cfg))
        self.call("git", "add", ".")
        self.record("weighted-price")
        self.call("git", "add", "docs/tracking/evidence")
        self.commit("verified weighted average")
        prod.write_text("def price(rows):\n    return sum(p for p,q in rows)//len(rows) if rows else None\n")
        self.status("调整成交均价实现")
        self.call("git", "add", ".")
        self.assertIn("证据与当前候选版本", self.commit("wrong mean with stale receipt", ok=False))
        self.assertIn('"counterexample":15', self.record("weighted-price", ok=False))
        # Even a correct unstaged implementation must not certify the incorrect staged one.
        prod.write_text(correct + "# reviewed\n")
        self.assertIn("暂存", self.record("weighted-price", ok=False))
        self.call("git", "add", "price.py")
        (self.root / "my-notes.txt").write_text("Unrelated user notes")
        self.record("weighted-price")
        self.call("git", "add", "docs/tracking/evidence")
        self.commit("repaired weighted average")
        self.assertIn("?? my-notes.txt", self.call("git", "status", "--short"))
        self.assertEqual(json.loads((self.docs/"evidence/weighted-price.json").read_text())["actual"],
                         {"normal":15, "boundary":None, "counterexample":19})

    def test_existing_hook_cannot_hide_a_failed_check(self):
        old = self.root / ".git/hooks/pre-commit"
        old.write_text("#!/bin/sh\necho prior-hook\nexit 0\n")
        old.chmod(0o755)
        self.init()
        self.init()
        self.call("git", "add", ".")
        self.assertIn("prior-hook", self.commit("initialize old project"))
        (self.root / "module.py").write_text("value = 1\n")
        self.call("git", "add", "module.py")
        self.assertIn("追踪文档未同步拦截", self.commit("missing status", ok=False))
        self.assertEqual(old.read_text().count("# >>> project-guardian-gatekeeper >>>"), 1)

    def test_formula_flag_integrates_existing_project_profile(self):
        profile = self.root / "AGENTS.md"
        profile.write_text("# 原项目协作约定\n保留业务规则。\n")
        self.init("--with-formula")
        self.assertIn("保留业务规则", profile.read_text())
        self.assertIn("enable_formula_doc: true", profile.read_text())
        (self.root / "price.py").write_text("price = 15\n")
        self.call("git", "add", ".")
        self.assertIn("三组公式样例", self.commit("formula template only", ok=False))

    def test_stale_review_cannot_approve_a_different_index(self):
        self.init()
        self.call("git", "add", ".")
        review = [sys.executable, str(SCRIPTS / "code_review.py")]
        self.assertIn("AI 代码审查", self.call("git", "commit", "-m", "missing", ok=False))
        scope = record_fixture_review(self.call, SCRIPTS)
        extra = self.root / "helper.py"
        extra.write_text("flag = 1\n")
        self.call("git", "add", "helper.py")
        self.assertIn("范围已变化", self.call(*review, "record", "--scope", scope, "--summary", "stale", ok=False))
        self.assertIn("缺少匹配", self.call("git", "commit", "-m", "stale", ok=False))
        record_fixture_review(self.call, SCRIPTS)
        extra.write_text("flag = 2\n")
        self.call("git", "commit", "-m", "reviewed index only")
        self.assertEqual(self.call("git", "show", "HEAD:helper.py"), "flag = 1\n")

    def test_existing_formatter_cannot_change_the_reviewed_commit(self):
        hook = self.root / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\nprintf 'formatted\\n' > tool.txt\ngit add tool.txt\nexit 0\n")
        hook.chmod(0o755)
        self.init()
        self.init()
        self.call("git", "add", ".")
        record_fixture_review(self.call, SCRIPTS)
        self.assertIn("缺少匹配", self.call("git", "commit", "-m", "before formatter", ok=False))
        self.commit("after formatter")
        self.assertEqual(self.call("git", "show", "HEAD:tool.txt"), "formatted\n")

    def test_push_checks_each_commit_and_replays_existing_hook_input(self):
        push_hook = self.root / ".git/hooks/pre-push"
        push_hook.write_text('#!/bin/sh\ncat > .git/old-hook-input\n')
        push_hook.chmod(0o755)
        self.init()
        self.init()
        self.assertEqual(push_hook.read_text().count("# >>> project-guardian-gatekeeper >>>"), 1)
        self.call("git", "add", ".")
        first_scope = record_fixture_review(self.call, SCRIPTS)
        self.call("git", "commit", "-m", "first")
        first = self.call("git", "rev-parse", "HEAD").strip()
        receipt = self.root / ".git/project-guardian/reviews" / (first_scope + ".json")
        receipt.unlink()  # Simulate an earlier commit that lacks local review evidence.
        self.status("second")
        self.call("git", "add", "docs/tracking/STATUS.md")
        self.commit("second")
        second = self.call("git", "rev-parse", "HEAD").strip()
        with tempfile.TemporaryDirectory() as remote:
            self.call("git", "init", "--bare", remote)
            self.assertIn(first, self.call("git", "push", remote, "main", ok=False))
            self.call("git", "--git-dir", remote, "rev-parse", "--verify", "refs/heads/main", ok=False)
            record_fixture_review(self.call, SCRIPTS, "--commit", first)
            self.call("git", "push", remote, "main")
            self.assertEqual(second, self.call("git", "--git-dir", remote, "rev-parse", "refs/heads/main").strip())
            self.assertEqual((self.root / ".git/old-hook-input").read_text().split(),
                             ["refs/heads/main", second, "refs/heads/main", "0" * len(first)])
            receipt.unlink()  # Already on remote. Later pushes check only the outgoing range.
            self.status("third")
            self.call("git", "add", "docs/tracking/STATUS.md")
            self.commit("third")
            self.call("git", "push", remote, "main")

    def test_existing_database_init_failure_then_recovery(self):
        db = self.root / "existing.sqlite"
        with sqlite3.connect(db) as conn:
            conn.execute("create table sample(value integer)")
        original = db.read_bytes()
        self.assertIn("existing.sqlite", self.init(ok=False))
        status = self.docs / "STATUS.md"
        result = next(line for line in status.read_text().splitlines() if "guardian-init" in line)
        self.assertIn("失败", result)
        self.assertIn("existing.sqlite", result)
        self.status("人工交接笔记")
        profile = self.root / "AGENTS.md"
        profile.write_text(profile.read_text().replace('  - "none"', '  - "existing.sqlite"'))
        self.init()
        content = status.read_text()
        self.assertIn("通过", next(line for line in content.splitlines() if "guardian-init" in line))
        self.assertEqual(content.count("guardian-init"), 1)
        self.assertIn("人工交接笔记", content)
        self.assertEqual(db.read_bytes(), original)
        self.assertIn("尚未", (self.docs / "TODO.md").read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)

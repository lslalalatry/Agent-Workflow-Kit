import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "project-guardian"
SCRIPTS_DIR = SKILL_ROOT / "scripts"
INIT_PROJECT = SCRIPTS_DIR / "init_project.py"
QUERY_DOCS = SCRIPTS_DIR / "query_docs.py"

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
CODE_SPAN_RE = re.compile(r"`[^`]*`")
CLI_FLAG_RE = re.compile(r"--[a-z][a-z0-9-]*")


def snapshot_tree(root: Path) -> Dict[str, bytes]:
    files: Dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == ".DS_Store" or "__pycache__" in path.parts:
            continue
        files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def extract_relative_links(md_path: Path) -> List[str]:
    links: List[str] = []
    in_fence = False
    for line in md_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        cleaned = CODE_SPAN_RE.sub("", line)
        for match in LINK_RE.finditer(cleaned):
            raw_target = match.group(1).strip().split()[0].strip("<>")
            if not raw_target or raw_target.startswith("#"):
                continue
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw_target) or raw_target.startswith("mailto:"):
                continue
            if "<" in raw_target or ">" in raw_target:
                continue
            path_part = raw_target.split("#", 1)[0]
            if path_part:
                links.append(path_part)
    return links


class CoherenceTests(unittest.TestCase):
    def test_template_bundle_matches_canonical_project_template(self) -> None:
        canonical = REPO_ROOT / "project-template"
        bundled = SKILL_ROOT / "assets" / "project-template"
        self.assertTrue(canonical.is_dir(), "Missing canonical project-template/")
        self.assertTrue(bundled.is_dir(), "Missing skills/project-guardian/assets/project-template/")
        canonical_tree = snapshot_tree(canonical)
        bundled_tree = snapshot_tree(bundled)
        self.assertEqual(set(canonical_tree.keys()), set(bundled_tree.keys()))
        for rel_path, content in canonical_tree.items():
            self.assertEqual(
                content,
                bundled_tree[rel_path],
                f"Template drift detected in {rel_path}; run python3 scripts/sync_global.py",
            )

    def test_init_project_flags_documented_and_cli_help_clean(self) -> None:
        help_run = subprocess.run(
            [sys.executable, str(INIT_PROJECT), "--help"],
            capture_output=True,
            text=True,
            check=True,
        )
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        flags = set(CLI_FLAG_RE.findall(help_run.stdout)) - {"--help"}
        self.assertTrue(flags, "Expected CLI flags from init_project.py --help")
        for flag in sorted(flags):
            self.assertIn(flag, skill_text, f"{flag} is missing from skills/project-guardian/SKILL.md")

        for subcmd in ([], ["search", "--help"], ["read", "--help"]):
            cmd = [sys.executable, str(QUERY_DOCS), *(subcmd or ["--help"])]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("usage:", proc.stdout.lower())

    def test_internal_markdown_links_resolve(self) -> None:
        md_files: List[Path] = [REPO_ROOT / "README.md", REPO_ROOT / "AGENTS.md"]
        for folder in (REPO_ROOT / "docs", SKILL_ROOT, REPO_ROOT / "project-template"):
            if folder.exists():
                md_files.extend(sorted(folder.rglob("*.md")))

        broken: List[str] = []
        for md_file in md_files:
            for rel_link in extract_relative_links(md_file):
                target = (md_file.parent / rel_link).resolve()
                if not target.exists():
                    broken.append(f"{md_file.relative_to(REPO_ROOT)} -> {rel_link}")

        self.assertEqual(broken, [], f"Broken internal markdown links: {broken}")

    def test_query_docs_progressive_search_and_bounded_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            project.mkdir()
            subprocess.run(
                [
                    sys.executable,
                    str(INIT_PROJECT),
                    str(project),
                    "--with-architecture",
                    "--with-formula",
                    "--with-decisions",
                    "--no-hook",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            decisions_path = project / "docs" / "tracking" / "DECISIONS.md"
            decisions_path.write_text(
                "# DECISIONS\n\n"
                "### D-001 退货扣除口径\n"
                "- **状态**：已批准\n"
                "- **规则**：全额退款订单必须从成交件数与销售额中双扣。\n"
                "- **细则 1**：校验 `refund_status == 'full'`。\n"
                "- **细则 2**：禁止仅扣金额不扣件数。\n"
                "- **细则 3**：每日快照保持幂等重算。\n"
                "- **细则 4**：边界零单返回 NULL。\n",
                encoding="utf-8",
            )
            billing_mod = project / "docs" / "architecture" / "modules" / "billing.md"
            billing_mod.write_text(
                "# 模块设计卡：计费对账 (`billing`)\n\n"
                "## 1. 模块目标与边界\n"
                "遵循 D-001 全额退款双扣口径。\n",
                encoding="utf-8",
            )

            search_proc = subprocess.run(
                [
                    sys.executable,
                    str(QUERY_DOCS),
                    "search",
                    "--root",
                    str(project),
                    "--query",
                    "D-001",
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            search_data = json.loads(search_proc.stdout)
            sources = {item["source"] for item in search_data["results"]}
            self.assertIn("docs/tracking/DECISIONS.md", sources)
            self.assertIn("docs/architecture/modules/billing.md", sources)

            read_proc = subprocess.run(
                [
                    sys.executable,
                    str(QUERY_DOCS),
                    "read",
                    "--root",
                    str(project),
                    "--path",
                    "docs/tracking/DECISIONS.md",
                    "--section",
                    "D-001",
                    "--max-lines",
                    "4",
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            read_data = json.loads(read_proc.stdout)
            self.assertTrue(read_data["truncated"])
            self.assertEqual(read_data["next_start_line"], read_data["start_line"] + 4)
            self.assertIn("D-001 退货扣除口径", read_data["content"])

            traversal = subprocess.run(
                [
                    sys.executable,
                    str(QUERY_DOCS),
                    "read",
                    "--root",
                    str(project),
                    "--path",
                    "../../etc/passwd",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(traversal.returncode, 2)


if __name__ == "__main__":
    unittest.main()

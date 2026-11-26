#!/usr/bin/env python3
"""Universal Project Guardian Gatekeeper (stdlib-only).

Enforces across any language or domain:
1. AGENTS.md presence and <= 20,000-byte anti-truncation cap.
2. Single-trunk Git discipline (only primary trunk; ephemeral exp/* must close).
3. Zero-sprawl storage discipline (no unwhitelisted DBs or >50MB duplicate blobs).
4. Tracking docs integrity (fixed names without dates, STATUS.md <= 100 lines + handoff anchor).
5. Mandatory tracking sync (code changes require STATUS.md update).
"""

from __future__ import annotations

import argparse
import acceptance
import chat_sync
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Dict, List, Set, Tuple

MAX_AGENTS_BYTES = 20_000
MAX_STATUS_LINES = 100
LARGE_FILE_BYTES = 50 * 1024 * 1024  # 50 MB

DB_EXTENSIONS = {".db", ".duckdb", ".sqlite", ".sqlite3", ".mdb", ".accdb"}
DB_COMPANION_SUFFIXES = ("-wal", "-shm", "-journal", ".wal", ".tmp")

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".tox",
    "target",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".storage-check",
}

SUSPICIOUS_COPY_PATTERNS = (
    re.compile(r".*([_-]copy|[_-]backup|\bcopy\b).*\.(db|duckdb|sqlite|sqlite3|csv|parquet|zip|tar|gz)$", re.I),
    re.compile(r".*\.(bak|old|orig)$", re.I),
)

DATE_STAMP_IN_DOC = re.compile(r"(\d{4}[-_]?\d{2}[-_]?\d{2}|\b20\d{6}\b)")


def run_git(root: Path, args: List[str]) -> Tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout.strip()
    except FileNotFoundError:
        return 127, ""


def parse_agents_profile(agents_path: Path, text=None) -> Dict[str, object]:
    profile: Dict[str, object] = {
        "primary_branch": "main",
        "tracking_dir": "docs/tracking",
        "enable_architecture_doc": False,
        "enable_formula_doc": False,
        "enable_decisions_doc": False,
        "allowed_storage_paths": [],
    }
    if text is None:
        if not agents_path.is_file():
            return profile
        text = agents_path.read_text(encoding="utf-8", errors="replace")
    in_allowed_list = False
    allowed: List[str] = []

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        if in_allowed_list:
            stripped = line.strip()
            if stripped.startswith("-"):
                item = stripped.lstrip("-").strip().strip("\"'")
                if item and item.lower() != "none" and not item.startswith("<"):
                    allowed.append(item)
                continue
            in_allowed_list = False

        m = re.match(r"^\s*([a-zA-Z0-9_]+)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip().strip("\"'")
        if key == "primary_branch" and val and not val.startswith("<"):
            profile["primary_branch"] = val
        elif key == "tracking_dir" and val and not val.startswith("<"):
            profile["tracking_dir"] = val.strip("/")
        elif key == "enable_architecture_doc":
            profile["enable_architecture_doc"] = val.lower() in {"true", "yes", "1", "是"}
        elif key == "enable_formula_doc":
            profile["enable_formula_doc"] = val.lower() in {"true", "yes", "1", "是"}
        elif key == "enable_decisions_doc":
            profile["enable_decisions_doc"] = val.lower() in {"true", "yes", "1", "是"}
        elif key == "allowed_storage_paths":
            if val and val.lower() != "none" and not val.startswith("["):
                allowed.append(val)
            else:
                in_allowed_list = True

    profile["allowed_storage_paths"] = allowed
    return profile


def is_whitelisted(rel_posix: str, patterns: List[str]) -> bool:
    for pat in patterns:
        norm = pat.strip().lstrip("./")
        if not norm:
            continue
        if rel_posix == norm or fnmatch.fnmatch(rel_posix, norm):
            return True
        if rel_posix.startswith(norm.rstrip("/") + "/"):
            return True
    return False


def strip_db_companion(rel_posix: str) -> Tuple[bool, str]:
    lower = rel_posix.lower()
    for comp in DB_COMPANION_SUFFIXES:
        if lower.endswith(comp):
            base = rel_posix[: -len(comp)]
            if Path(base).suffix.lower() in DB_EXTENSIONS:
                return True, base
    if Path(rel_posix).suffix.lower() in DB_EXTENSIONS:
        return True, rel_posix
    return False, rel_posix


def check_agents_file(root: Path, errors: List[str]) -> Dict[str, object]:
    agents_path = root / "AGENTS.md"
    if not agents_path.is_file():
        errors.append(
            "[宪章缺失] 根目录缺少 AGENTS.md。请运行 init_project.py 或从 Agent-Workflow-Kit 复制母版。"
        )
        return parse_agents_profile(agents_path)

    size = agents_path.stat().st_size
    if size > MAX_AGENTS_BYTES:
        errors.append(
            f"[体积超限] AGENTS.md 当前 {size} 字节，超过 {MAX_AGENTS_BYTES} 字节安全上限（防平台静默截断）。"
            "请将详细流程移入 docs/tracking/SPEC.md 或 Skill references。"
        )
    return parse_agents_profile(agents_path)


def check_git_branches(
    root: Path, primary_branch: str, errors: List[str], warnings: List[str]
) -> bool:
    code, inside = run_git(root, ["rev-parse", "--is-inside-work-tree"])
    if code != 0 or inside != "true":
        warnings.append("[Git 未初始化] 当前目录尚未初始化 Git 仓库，跳过分支检查。")
        return False

    _, branches_out = run_git(root, ["for-each-ref", "--format=%(refname:short)", "refs/heads/"])
    branches = [b.strip() for b in branches_out.splitlines() if b.strip()]
    _, current_branch = run_git(root, ["symbolic-ref", "--short", "-q", "HEAD"])

    trunk = primary_branch
    if trunk not in branches and "master" in branches and primary_branch == "main":
        trunk = "master"

    if not branches:
        if current_branch and current_branch not in {trunk, "master"}:
            errors.append(
                f"[主分支违规] 初始分支名为 '{current_branch}'，必须使用唯一主分支 '{trunk}'（运行 git branch -M {trunk}）。"
            )
        return True

    if current_branch == trunk:
        extra = [b for b in branches if b != trunk]
        if extra:
            errors.append(
                f"[残留分支拦截] 当前处于主分支 '{trunk}'，但仓库仍残留未收口的分支: {', '.join(extra)}。"
                f" 必须先合并删除（git merge --no-ff <分支> && git branch -d <分支>）或放弃删除（git branch -D <分支>）。"
            )
    elif current_branch.startswith("exp/"):
        other_extra = [b for b in branches if b not in {trunk, current_branch}]
        if other_extra:
            errors.append(
                f"[多实验分支拦截] 同时存在多个非主干分支: {', '.join([current_branch, *other_extra])}。"
                " 同一时间最多只允许 1 条临时 exp/* 分支。"
            )
        else:
            warnings.append(
                f"[实验分支提醒] 当前位于临时分支 '{current_branch}'。本任务结束前必须合并回 '{trunk}' 并删除本分支！"
            )
    else:
        errors.append(
            f"[非法分支名] 当前分支 '{current_branch or 'DETACHED_HEAD'}' 既非主分支 '{trunk}'，也非临时实验分支 'exp/<topic>'。"
        )

    _, wt_out = run_git(root, ["worktree", "list", "--porcelain"])
    wt_count = sum(1 for line in wt_out.splitlines() if line.startswith("worktree "))
    if wt_count > 1:
        warnings.append(
            f"[Worktree 提醒] 检测到 {wt_count} 个 Git worktree。任务完成后请确认清理多余 worktree 且未复制大数据库。"
        )
    return True


def check_storage_sprawl(
    root: Path, has_git: bool, allowed_paths: List[str], errors: List[str]
) -> None:
    seen_unauth_dbs: Set[str] = set()

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel_dir = Path(dirpath).relative_to(root)

        for fname in filenames:
            if fname == ".DS_Store":
                continue
            fpath = Path(dirpath) / fname
            if fpath.is_symlink():
                continue
            rel_posix = (rel_dir / fname).as_posix() if str(rel_dir) != "." else fname

            is_db, base_db_posix = strip_db_companion(rel_posix)
            if is_db:
                if not is_whitelisted(base_db_posix, allowed_paths) and not is_whitelisted(rel_posix, allowed_paths):
                    if base_db_posix not in seen_unauth_dbs:
                        seen_unauth_dbs.add(base_db_posix)
                        errors.append(
                            f"[多余数据库拦截] 发现未在 AGENTS.md 'allowed_storage_paths' 白名单登记的数据库: {base_db_posix}。"
                            " 严禁擅自新建或复制额外数据库；测试请用只读模式或内存/微型夹具，收尾请清理临时库。"
                        )
                continue

            try:
                fsize = fpath.stat().st_size
            except OSError:
                continue

            if fsize > LARGE_FILE_BYTES and not is_whitelisted(rel_posix, allowed_paths):
                mb = fsize / (1024 * 1024)
                errors.append(
                    f"[超大文件拦截] 发现未白名单登记的超大文件 ({mb:.1f} MB > 50 MB): {rel_posix}。"
                )
                continue

            if any(p.match(rel_posix) for p in SUSPICIOUS_COPY_PATTERNS) and not is_whitelisted(
                rel_posix, allowed_paths
            ):
                errors.append(
                    f"[疑似冗余副本拦截] 发现疑似临时备份或重复数据副本: {rel_posix}。请用 Git 管理版本并清理多余文件。"
                )

    if has_git:
        _, staged_out = run_git(root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
        for staged in [s.strip() for s in staged_out.splitlines() if s.strip()]:
            is_db, _ = strip_db_companion(staged)
            if is_db:
                errors.append(
                    f"[Git 污染拦截] 严禁将数据库文件暂存提交进 Git 仓库: {staged}！请将其移出暂存区并加入 .gitignore。"
                )
                continue
            sp = root / staged
            if sp.is_file() and sp.stat().st_size > LARGE_FILE_BYTES:
                mb = sp.stat().st_size / (1024 * 1024)
                errors.append(
                    f"[Git 大文件拦截] 严禁将 >50MB 大文件 ({mb:.1f} MB) 提交进 Git: {staged}！"
                )


def resolve_tracking_dir(root: Path, configured_dir: str) -> Path:
    candidate = root / configured_dir
    if candidate.is_dir():
        return candidate
    if (root / "STATUS.md").is_file() and (root / "SPEC.md").is_file():
        return root
    return candidate


def check_tracking_docs(
    root: Path,
    profile: Dict[str, object],
    has_git: bool,
    hook_mode: str,
    errors: List[str],
    warnings: List[str],
) -> None:
    configured_rel = str(profile["tracking_dir"])
    tdir = resolve_tracking_dir(root, configured_rel)
    rel_tdir = "." if tdir == root else tdir.relative_to(root).as_posix()

    required = ["SPEC.md", "STATUS.md", "TODO.md", "BACKLOG.md"]
    if profile.get("enable_formula_doc"):
        required.append("FORMULA.md")
    if profile.get("enable_decisions_doc"):
        required.append("DECISIONS.md")

    for doc_name in required:
        dpath = tdir / doc_name
        exists = dpath.is_file()
        if hook_mode == "pre-commit":
            name = (Path(rel_tdir) / doc_name).as_posix()
            exists = bool(acceptance.git(root, "ls-files", "--stage", "--", name))
        if not exists:
            shown = doc_name if rel_tdir == "." else f"{rel_tdir}/{doc_name}"
            errors.append(f"[追踪文档缺失] 缺少必选追踪文档: {shown}。")

    if profile.get("enable_architecture_doc"):
        for arch_doc in ("docs/architecture/ARCHITECTURE.md", "docs/architecture/DATA_MODEL.md"):
            exists = (root / arch_doc).is_file()
            if hook_mode == "pre-commit":
                exists = bool(acceptance.git(root, "ls-files", "--stage", "--", arch_doc))
            if not exists:
                errors.append(f"[架构文档缺失] 已启用 enable_architecture_doc，缺少必选架构文档: {arch_doc}。")

    if tdir.is_dir() and tdir != root:
        for child in sorted(tdir.iterdir()):
            if child.is_file() and child.suffix.lower() == ".md":
                if DATE_STAMP_IN_DOC.search(child.stem):
                    errors.append(
                        f"[日期副本拦截] 追踪文档严禁在文件名中带日期后缀分裂副本: {rel_tdir}/{child.name}。"
                        " 请合并回固定无日期标准文档（由 Git 记录历史）。"
                    )

    status_path = tdir / "STATUS.md"
    status_rel = "STATUS.md" if rel_tdir == "." else f"{rel_tdir}/STATUS.md"
    if status_path.is_file() or hook_mode == "pre-commit":
        revision = "" if hook_mode == "pre-commit" else "work"
        lines = acceptance.document(root, status_rel, revision).splitlines()
        if len(lines) > MAX_STATUS_LINES:
            errors.append(
                f"[STATUS 膨胀拦截] {status_rel} 当前共 {len(lines)} 行，超过 {MAX_STATUS_LINES} 行上限！"
                " 请只保留最新焦点与断点锚点，将历史记录移入 BACKLOG.md。"
            )
        joined = "\n".join(lines)
        if "断点接力锚点" not in joined and "Session Handoff Anchor" not in joined:
            errors.append(
                f"[接力锚点缺失] {status_rel} 缺少『断点接力锚点（Session Handoff Anchor）』章节，长任务换窗口将丢失上下文。"
            )

    if not has_git or hook_mode == "init":
        return

    meta_exact = {
        "AGENTS.md",
        "GEMINI.md",
        "README.md",
        "LICENSE",
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
    }

    def is_governance_or_doc(path_str: str) -> bool:
        if path_str in meta_exact:
            return True
        if rel_tdir != "." and path_str.startswith(rel_tdir + "/"):
            return True
        if path_str.startswith("docs/architecture/") and path_str.endswith(".md"):
            return True
        if rel_tdir == "." and path_str in {
            "SPEC.md",
            "STATUS.md",
            "TODO.md",
            "BACKLOG.md",
            "FORMULA.md",
            "DECISIONS.md",
        }:
            return True
        return False

    try:
        changed = set(acceptance.paths(acceptance.git(root, "diff", "--cached", "--name-only", "--no-renames", "-z")))
        revision = ""
        if hook_mode != "pre-commit":
            revision = "work"
            changed.update(acceptance.paths(acceptance.git(root, "diff", "--name-only", "--no-renames", "-z")))
            changed.update(acceptance.paths(acceptance.git(root, "ls-files", "--others", "--exclude-standard", "-z")))
        implementation = sorted(f for f in changed if not is_governance_or_doc(f)
                                and not f.startswith((Path(rel_tdir) / "evidence").as_posix() + "/"))
        if implementation and status_rel not in changed:
            errors.append(f"[追踪文档未同步拦截] 修改了实现文件 {', '.join(implementation[:4])}，请同步 {status_rel} 并在提交前暂存。")
        chat_sync.check_bundle(root, rel_tdir, revision, changed)
        acceptance.check_changes(root, rel_tdir, revision, changed, implementation, profile["enable_formula_doc"])
    except (ValueError, OSError) as exc:
        errors.append(f"[交付验收未通过] {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Universal Project Guardian Guardrails.")
    parser.add_argument("--root", default=None, help="Project root path (defaults to Git root or CWD).")
    parser.add_argument("--hook", choices=["none", "pre-commit", "init"], default="none", help="Git hook mode.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args()

    if args.root:
        root = Path(args.root).resolve()
    else:
        code, git_top = run_git(Path.cwd(), ["rev-parse", "--show-toplevel"])
        root = Path(git_top).resolve() if code == 0 and git_top else Path.cwd().resolve()

    errors: List[str] = []
    warnings: List[str] = []

    profile = check_agents_file(root, errors)
    if args.hook == "pre-commit":
        indexed_profile = acceptance.document(root, "AGENTS.md", "")
        if indexed_profile:
            profile = parse_agents_profile(root / "AGENTS.md", indexed_profile)
        else:
            errors.append("[宪章缺失] 候选提交中缺少 AGENTS.md，请先将项目规则暂存。")
    has_git = check_git_branches(root, str(profile["primary_branch"]), errors, warnings)
    check_storage_sprawl(root, has_git, list(profile["allowed_storage_paths"]), errors)
    check_tracking_docs(root, profile, has_git, args.hook, errors, warnings)

    passed = len(errors) == 0

    if args.json:
        print(
            json.dumps(
                {
                    "root": str(root),
                    "passed": passed,
                    "errors": errors,
                    "warnings": warnings,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        if passed:
            print(f"✅ [Project Guardian 安检绿灯通过] 根目录: {root}")
            for w in warnings:
                print(f"  ⚠️  {w}")
        else:
            print(f"🛑 [Project Guardian 安检红灯拦截] 共发现 {len(errors)} 项违规（根目录: {root}）：", file=sys.stderr)
            for idx, err in enumerate(errors, 1):
                print(f"  {idx}. {err}", file=sys.stderr)
            for w in warnings:
                print(f"  ⚠️  {w}", file=sys.stderr)
            print(
                "\n💡 修复上述全部违规项后再重新提交（严禁使用 --no-verify 绕过安检闸机）。",
                file=sys.stderr,
            )

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

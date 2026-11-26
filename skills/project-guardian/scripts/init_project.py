#!/usr/bin/env python3
"""Bootstrap AGENTS.md, docs/tracking/ templates, single-trunk Git, and pre-commit gatekeeper."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
import re
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
from typing import List

from verify_guardrails import parse_agents_profile, resolve_tracking_dir

HOOK_LOOKUP = """GUARD_SCRIPT=""
for candidate in \\
  "$(git rev-parse --show-toplevel)/.agents/skills/project-guardian/scripts/verify_guardrails.py" \\
  "$HOME/.gemini/config/skills/project-guardian/scripts/verify_guardrails.py" \\
  "$HOME/.codex/skills/project-guardian/scripts/verify_guardrails.py" \\
  "$HOME/Documents/Agent-Workflow-Kit/skills/project-guardian/scripts/verify_guardrails.py"; do
  if [ -f "$candidate" ] && [ -f "${candidate%/*}/code_review.py" ]; then
    GUARD_SCRIPT="$candidate"
    break
  fi
done
if [ -z "$GUARD_SCRIPT" ]; then
  echo "Project Guardian: 找不到新版检查脚本，请安装或更新 project-guardian" >&2
  exit 1
fi
REVIEW_SCRIPT="${GUARD_SCRIPT%/*}/code_review.py"
"""

HOOKS = {
    "pre-commit": HOOK_LOOKUP + """python3 "$REVIEW_SCRIPT" check-staged || exit 1
python3 "$GUARD_SCRIPT" --hook pre-commit || exit 1
""",
    # Git supplies one ref update per line. Replay it for any existing hook below us.
    "pre-push": HOOK_LOOKUP + """guardian_push_refs=$(cat) || exit 1
if [ -n "$guardian_push_refs" ]; then
  python3 "$REVIEW_SCRIPT" check-push <<GUARDIAN_REFS || exit 1
$guardian_push_refs
GUARDIAN_REFS
  exec 0<<GUARDIAN_REFS
$guardian_push_refs
GUARDIAN_REFS
fi
""",
}

DEFAULT_GITIGNORE_LINES = [
    ".DS_Store",
    "__pycache__/",
    ".venv/",
    "node_modules/",
    "*.db",
    "*.duckdb",
    "*.duckdb.wal",
    "*.sqlite",
    "*.sqlite3",
    ".storage-check/",
]


def find_template_root(script_path: Path) -> Path:
    skill_dir = script_path.resolve().parent.parent
    bundled = skill_dir / "assets" / "project-template"
    if bundled.is_dir():
        return bundled
    kit_template = skill_dir.parent.parent / "project-template"
    if kit_template.is_dir():
        return kit_template
    raise FileNotFoundError("Cannot locate project-template directory.")


def ensure_git_repo(target: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(target),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0 and proc.stdout.strip() == "true":
        top = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=target, text=True).strip()
        if Path(top).resolve() != target:
            raise ValueError(f"请从 Git 仓库根目录初始化：{top}")
        return "Git 仓库已存在（保留现有历史）"
    subprocess.run(["git", "init", "-b", "main"], cwd=str(target), check=True, capture_output=True)
    return "已初始化单主线 Git 仓库（唯一主分支 main）"


def ensure_gitignore(target: Path) -> str:
    gi = target / ".gitignore"
    if not gi.exists():
        gi.write_text("\n".join(DEFAULT_GITIGNORE_LINES) + "\n", encoding="utf-8")
        return "已创建默认 .gitignore（自动忽略本地数据库与缓存）"

    existing = gi.read_text(encoding="utf-8", errors="replace").splitlines()
    existing_set = {line.strip() for line in existing}
    missing = [line for line in DEFAULT_GITIGNORE_LINES if line not in existing_set]
    if not missing:
        return ".gitignore 已包含必要忽略规则"
    with gi.open("a", encoding="utf-8") as f:
        if existing and existing[-1].strip():
            f.write("\n")
        f.write("# Project Guardian safe storage ignores\n")
        for line in missing:
            f.write(line + "\n")
    return f"已向 .gitignore 补充 {len(missing)} 条安全忽略项"


def install_hook(target: Path, name: str) -> str:
    def git_path(*args):
        output = subprocess.check_output(["git", "rev-parse", *args], cwd=target, text=True)
        return (target / output.strip()).resolve()

    raw_hook = subprocess.check_output(["git", "rev-parse", "--git-path", f"hooks/{name}"], cwd=target, text=True).strip()
    hook_path = target / raw_hook
    hook_file = hook_path.parent.resolve() / hook_path.name
    common_dir = git_path("--git-common-dir")
    if not any(parent in hook_file.parents for parent in (target, common_dir)):
        raise ValueError(f"Git 使用共享钩子目录，需由该目录的维护者接入检查：{hook_file}")
    hook_file.parent.mkdir(parents=True, exist_ok=True)

    if hook_file.is_symlink():
        raise ValueError(f"已有提交钩子是符号链接，请由维护者在实际钩子中接入检查：{hook_file}")
    current = hook_file.read_text(encoding="utf-8") if hook_file.exists() else ""
    for tag in ("gatekeeper", "original-hook"):
        start, stop = f"# >>> project-guardian-{tag} >>>", f"# <<< project-guardian-{tag} <<<"
        if start in current:
            begin = current.index(start)
            end = current.find(stop, begin)
            if end < 0:
                raise ValueError("既有钩子中的 Project Guardian 区段不完整")
            current = current[:begin] + current[end + len(stop):].removeprefix("\n")
    if current.startswith("#!"):
        shebang, _, body = current.partition("\n")
        words = shlex.split(shebang[2:])
        program = Path(words[0]).name if words else ""
        if program == "env":
            program = next((w for w in words[1:] if not w.startswith("-")), "")
        if program not in {"sh", "bash", "dash", "ksh", "zsh", "ash"}:
            raise ValueError(f"保留已有 {program} 钩子，请在该钩子中显式接入验收脚本：{hook_file}")
    else:
        shebang, body = "#!/bin/sh", current
    checks = HOOKS[name]
    prefix = ""
    if name == "pre-commit" and body.strip():
        # A formatter can re-stage files or exit early. Check the final index in the parent shell.
        prefix = "# >>> project-guardian-original-hook >>>\n(\n:\n# <<< project-guardian-original-hook <<<\n"
        checks = ")\nguardian_status=$?\n[ \"$guardian_status\" -eq 0 ] || exit \"$guardian_status\"\n" + checks
        prefix += body.rstrip("\n") + "\n"
        body = ""
    section = "# >>> project-guardian-gatekeeper >>>\n" + checks + "# <<< project-guardian-gatekeeper <<<\n"
    content = shebang + "\n" + prefix + section + body
    if not hook_file.exists() or hook_file.read_text(encoding="utf-8") != content:
        hook_file.write_text(content, encoding="utf-8")
    mode = hook_file.stat().st_mode
    hook_file.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return f"已挂载 {name} 检查：{hook_file}"


def enable_profile_documents(path: Path, requested: List[str]) -> None:
    profile = parse_agents_profile(path)
    text = path.read_text(encoding="utf-8")
    updated = text
    missing = []
    for key in requested:
        if profile[key]:
            continue
        pattern = re.compile(rf"^(?P<indent>[ \t]*){key}[ \t]*:[^#\r\n]*(?P<comment>#[^\n]*)?$", re.M)
        if pattern.search(updated):
            updated = pattern.sub(lambda m: f"{m['indent']}{key}: true" + ("  " + m["comment"] if m["comment"] else ""), updated)
        else:
            missing.append(f"{key}: true")
    if missing:
        updated = updated.rstrip() + "\n\n```yaml\n" + "\n".join(missing) + "\n```\n"
    if updated != text:
        path.write_text(updated, encoding="utf-8")


def write_init_status(path: Path, result: str) -> None:
    marker = "<!-- guardian-init -->"
    line = f"- **初始化实测**：{result} {marker}"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for i, old in enumerate(lines):
        if marker in old or old == "- **最近一次验证结果**：`初始化门禁自检通过`":
            lines[i] = line
            break
    else:
        lines.append(line)
    updated = "\n".join(lines) + "\n"
    if updated != text:
        path.write_text(updated, encoding="utf-8")


def verify_initial_state(target: Path, status_file: Path, setup_errors: List[str]) -> bool:
    write_init_status(status_file, "尚未检查")
    checker = Path(__file__).with_name("verify_guardrails.py")
    result = subprocess.run([sys.executable, str(checker), "--root", str(target), "--hook", "init", "--json"],
                            cwd=target, capture_output=True, text=True)
    errors = list(setup_errors)
    warnings = []
    try:
        report = json.loads(result.stdout)
        errors.extend(report["errors"])
        warnings.extend(report["warnings"])
        if result.returncode or report.get("passed") is not True:
            if not errors:
                errors.append("检查程序未报告通过")
    except (ValueError, TypeError, KeyError):
        errors.append(f"检查程序未返回有效报告（退出码 {result.returncode}）")
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    outcome = "失败" if errors else "通过"
    details = " ".join(" ".join(str(v).split()) for v in (errors or warnings))
    write_init_status(status_file, f"{stamp} · {outcome}（仓库结构、分支、存储和追踪文档） {details[:300]}")
    for issue in errors + warnings:
        print(issue, file=sys.stderr)
    return not errors


def copy_architecture_bundle(tpl_root: Path, target: Path, logs: List[str]) -> None:
    arch_src = tpl_root / "docs" / "architecture"
    arch_dst = target / "docs" / "architecture"
    if arch_src.is_dir():
        created_arch: List[str] = []
        skipped_arch: List[str] = []
        for src in sorted(arch_src.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(arch_src)
            dst = arch_dst / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                skipped_arch.append(rel.as_posix())
                continue
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            created_arch.append(rel.as_posix())
        if created_arch:
            logs.append(f"已创建架构设计蓝图 (docs/architecture/): {', '.join(created_arch)}")
        if skipped_arch:
            logs.append(f"保留已有架构文档（未覆盖）: {', '.join(skipped_arch)}")

    deploy_src = tpl_root / "deploy"
    deploy_dst = target / "deploy"
    if deploy_src.is_dir():
        for src in sorted(deploy_src.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(deploy_src)
            dst = deploy_dst / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                logs.append(f"已创建部署目录骨架 (deploy/{rel.as_posix()})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize Project Guardian templates and gatekeeper.")
    parser.add_argument("target", nargs="?", default=".", help="Target project directory.")
    parser.add_argument("--minimal", action="store_true", help="Create only the 4 core tracking docs.")
    parser.add_argument("--with-architecture", action="store_true", help="Enable and create modular docs/architecture/ blueprint and deploy/ skeleton.")
    parser.add_argument("--with-formula", action="store_true", help="Enable and create FORMULA.md.")
    parser.add_argument("--with-decisions", action="store_true", help="Enable and create DECISIONS.md.")
    parser.add_argument("--no-hook", action="store_true", help="Skip installing Git pre-commit and pre-push hooks.")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    tpl_root = find_template_root(Path(__file__))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    today_str = datetime.now().strftime("%Y-%m-%d")

    logs: List[str] = []
    try:
        logs.append(ensure_git_repo(target))
    except ValueError as exc:
        parser.exit(1, str(exc) + "\n")
    logs.append(ensure_gitignore(target))

    agents_dst = target / "AGENTS.md"
    if not agents_dst.exists():
        agents_text = (tpl_root / "AGENTS.md").read_text(encoding="utf-8")
        agents_text = agents_text.replace('project_name: "<填写项目名称>"', f'project_name: "{target.name}"')
        if args.with_architecture:
            agents_text = agents_text.replace("enable_architecture_doc: false", "enable_architecture_doc: true")
        if args.with_formula:
            agents_text = agents_text.replace("enable_formula_doc: false", "enable_formula_doc: true")
        if args.with_decisions:
            agents_text = agents_text.replace("enable_decisions_doc: false", "enable_decisions_doc: true")
        agents_dst.write_text(agents_text, encoding="utf-8")
        logs.append("已创建根目录 AGENTS.md")
    else:
        logs.append("沿用已有 AGENTS.md，按所选选项补齐文档开关")

    requested_flags = [name for name, enabled in (("enable_architecture_doc", args.with_architecture),
                                                   ("enable_formula_doc", args.with_formula),
                                                   ("enable_decisions_doc", args.with_decisions)) if enabled]
    if requested_flags:
        enable_profile_documents(agents_dst, requested_flags)
    profile = parse_agents_profile(agents_dst)
    tracking_dst = resolve_tracking_dir(target, profile["tracking_dir"]).resolve()
    if tracking_dst != target and target not in tracking_dst.parents:
        parser.exit(1, "追踪文档目录必须位于目标仓库中。\n")
    tracking_dst.mkdir(parents=True, exist_ok=True)

    docs_to_copy = ["SPEC.md", "STATUS.md", "TODO.md", "BACKLOG.md"]
    if profile["enable_formula_doc"]:
        docs_to_copy.append("FORMULA.md")
    if profile["enable_decisions_doc"]:
        docs_to_copy.append("DECISIONS.md")

    created_docs: List[str] = []
    skipped_docs: List[str] = []
    for doc_name in docs_to_copy:
        src = tpl_root / "docs" / "tracking" / doc_name
        dst = tracking_dst / doc_name
        if dst.exists():
            skipped_docs.append(doc_name)
            continue
        content = src.read_text(encoding="utf-8")
        content = content.replace("YYYY-MM-DD HH:MM", now_str).replace("YYYY-MM-DD", today_str)
        dst.write_text(content, encoding="utf-8")
        created_docs.append(doc_name)

    if created_docs:
        logs.append(f"已创建追踪文档 (docs/tracking/): {', '.join(created_docs)}")
    if skipped_docs:
        logs.append(f"保留已有追踪文档（未覆盖）: {', '.join(skipped_docs)}")

    if profile.get("enable_architecture_doc"):
        copy_architecture_bundle(tpl_root, target, logs)

    setup_errors = []
    if not args.no_hook:
        for hook_name in HOOKS:
            try:
                logs.append(install_hook(target, hook_name))
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                setup_errors.append(f"{hook_name} 钩子接入失败：{exc}")
    verified = verify_initial_state(target, tracking_dst / "STATUS.md", setup_errors)

    print(f"Project Guardian 初始化实测{'通过' if verified else '失败'}：{target}")
    for item in logs:
        print(f"  - {item}")
    return 0 if verified else 1


if __name__ == "__main__":
    sys.exit(main())

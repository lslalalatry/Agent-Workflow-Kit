#!/usr/bin/env python3
"""Synchronize Agent-Workflow-Kit into Antigravity (~/.gemini/config) and Codex (~/.codex)."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import shutil
import stat
import sys


def backup_file_once_per_day(target: Path, stamp: str, dry_run: bool = False) -> None:
    if not target.exists():
        return
    backup = target.parent / f"{target.name}.bak-{stamp}"
    if backup.exists():
        return
    if not dry_run:
        shutil.copy2(target, backup)


def copy_tree_clean(src: Path, dst: Path) -> None:
    if dst.is_symlink():
        dst.unlink()
    elif dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)


def make_scripts_executable(skill_dir: Path) -> None:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        return
    for py_file in scripts_dir.glob("*.py"):
        mode = py_file.stat().st_mode
        py_file.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize Agent-Workflow-Kit into Antigravity (~/.gemini/config) and Codex (~/.codex)."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview target paths without modifying files.")
    args = parser.parse_args()

    kit_root = Path(__file__).resolve().parent.parent
    home = Path.home()
    stamp = datetime.now().strftime("%Y%m%d")

    collab_src = kit_root / "global-rules" / "COLLABORATION_PRINCIPLES.md"
    tpl_src = kit_root / "project-template"
    skill_src = kit_root / "skills" / "project-guardian"
    bundled_tpl = skill_src / "assets" / "project-template"

    agy_root = home / ".gemini" / "config"
    agy_rules_dir = agy_root / "rules"
    agy_skills_dir = agy_root / "skills"
    agy_agents_md = agy_rules_dir / "AGENTS.md"

    codex_root = home / ".codex"
    codex_skills_dir = codex_root / "skills"
    codex_agents_md = codex_root / "AGENTS.md"

    if args.dry_run:
        print("🔍 [dry-run] 将同步以下目标（未写入磁盘）：")
        print(f"  - 打包模板: {tpl_src} -> {bundled_tpl}")
        print(f"  - Antigravity 全局原则(带当日备份): {collab_src} -> {agy_agents_md}")
        print(f"  - Antigravity 全局技能: {skill_src} -> {agy_skills_dir / 'project-guardian'}")
        print(f"  - Codex 全局原则(带当日备份): {collab_src} -> {codex_agents_md}")
        print(f"  - Codex 全局技能: {skill_src} -> {codex_skills_dir / 'project-guardian'}")
        return 0

    # 1. Bundle project-template inside skill assets so init_project.py is 100% self-contained
    copy_tree_clean(tpl_src, bundled_tpl)
    make_scripts_executable(skill_src)

    # 2. Deploy to Antigravity (~/.gemini/config/)
    agy_rules_dir.mkdir(parents=True, exist_ok=True)
    agy_skills_dir.mkdir(parents=True, exist_ok=True)

    backup_file_once_per_day(agy_agents_md, stamp)
    shutil.copy2(collab_src, agy_agents_md)
    copy_tree_clean(skill_src, agy_skills_dir / "project-guardian")
    make_scripts_executable(agy_skills_dir / "project-guardian")

    # Bridge existing Codex general skills (asd-ste100, grill-me) to Antigravity if present
    bridged = []
    for shared_skill in ("asd-ste100", "grill-me"):
        c_skill = codex_skills_dir / shared_skill
        a_skill = agy_skills_dir / shared_skill
        if c_skill.is_dir() and not a_skill.exists():
            copy_tree_clean(c_skill, a_skill)
            make_scripts_executable(a_skill)
            bridged.append(shared_skill)

    # 3. Deploy to Codex (~/.codex/)
    codex_skills_dir.mkdir(parents=True, exist_ok=True)
    backup_file_once_per_day(codex_agents_md, stamp)
    shutil.copy2(collab_src, codex_agents_md)
    copy_tree_clean(skill_src, codex_skills_dir / "project-guardian")
    make_scripts_executable(codex_skills_dir / "project-guardian")

    print("✅ 双端全局同步部署完成！")
    print(f"  - 可见母版总仓: {kit_root}")
    print(f"  - Antigravity 全局原则: {agy_agents_md}")
    print(f"  - Antigravity 全局技能: {agy_skills_dir / 'project-guardian'}")
    if bridged:
        print(f"  - 已桥接通用技能至 Antigravity: {', '.join(bridged)}")
    print(f"  - Codex 全局原则: {codex_agents_md}")
    print(f"  - Codex 全局技能: {codex_skills_dir / 'project-guardian'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

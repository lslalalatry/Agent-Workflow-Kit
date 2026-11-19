#!/usr/bin/env python3
"""Synchronize Agent-Workflow-Kit into Antigravity (~/.gemini/config) and Codex (~/.codex)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import stat
import sys


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
    kit_root = Path(__file__).resolve().parent.parent
    home = Path.home()

    collab_src = kit_root / "global-rules" / "COLLABORATION_PRINCIPLES.md"
    tpl_src = kit_root / "project-template"
    skill_src = kit_root / "skills" / "project-guardian"

    # 1. Bundle project-template inside skill assets so init_project.py is 100% self-contained
    bundled_tpl = skill_src / "assets" / "project-template"
    copy_tree_clean(tpl_src, bundled_tpl)
    make_scripts_executable(skill_src)

    # 2. Deploy to Antigravity (~/.gemini/config/)
    agy_root = home / ".gemini" / "config"
    agy_rules_dir = agy_root / "rules"
    agy_skills_dir = agy_root / "skills"
    agy_rules_dir.mkdir(parents=True, exist_ok=True)
    agy_skills_dir.mkdir(parents=True, exist_ok=True)

    agy_agents_md = agy_rules_dir / "AGENTS.md"
    shutil.copy2(collab_src, agy_agents_md)
    copy_tree_clean(skill_src, agy_skills_dir / "project-guardian")
    make_scripts_executable(agy_skills_dir / "project-guardian")

    # Bridge existing Codex general skills (asd-ste100, grill-me) to Antigravity if present
    codex_root = home / ".codex"
    codex_skills_dir = codex_root / "skills"
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
    codex_agents_md = codex_root / "AGENTS.md"
    if codex_agents_md.exists():
        stamp = datetime.now().strftime("%Y%m%d")
        backup = codex_root / f"AGENTS.md.bak-{stamp}"
        if not backup.exists():
            shutil.copy2(codex_agents_md, backup)
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

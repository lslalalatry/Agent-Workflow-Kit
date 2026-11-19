#!/usr/bin/env python3
"""Bind a review by the current AI to the exact Git trees inspected."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from acceptance import git
from chat_sync import replace


def oid(*args):
    return git(Path.cwd(), *args).decode("ascii").strip()


def empty_tree():
    return oid("hash-object", "-t", "tree", os.devnull)


def trees(commit=None):
    if commit is None:
        head = git(Path.cwd(), "rev-parse", "--verify", "-q", "HEAD^{tree}", optional=True)
        return head.decode().strip() or empty_tree(), oid("write-tree")
    commit = oid("rev-parse", "--verify", "--end-of-options", commit + "^{commit}")
    # Read the actual parent even for a shallow checkout. Missing history must surface.
    header = git(Path.cwd(), "cat-file", "-p", commit).split(b"\n\n", 1)[0].splitlines()
    tree = header[0].split()[1].decode()
    parent = next((line.split()[1].decode() for line in header if line.startswith(b"parent ")), None)
    return (oid("rev-parse", "--verify", parent + "^{tree}") if parent else empty_tree()), tree


def review_file(scope):
    folder = Path(os.fsdecode(git(Path.cwd(), "rev-parse", "--git-path", "project-guardian/reviews").rstrip(b"\n")))
    return folder / (scope + ".json")


def require_review(pair, label):
    base, candidate = pair
    if base == candidate:
        return
    scope = base + ".." + candidate
    file = review_file(scope)
    if file.is_file():
        record = json.loads(file.read_text(encoding="utf-8"))
        if isinstance(record, dict) and record.get("scope") == scope and isinstance(record.get("summary"), str) and record["summary"].strip():
            return
    raise ValueError(f"{label} 缺少匹配的 AI 代码审查。请用 code_review.py show 查看差异，复核并记录后重试。")


def check_push(lines):
    seen = set()
    for line in lines:
        if not line.strip():
            continue
        _, local, target, remote = line.split()
        if not local.strip("0"):  # ref deletion
            continue
        tip = oid("rev-parse", "--verify", local + "^{commit}")
        revisions = [tip]
        if remote.strip("0"):
            # The server-provided old tip must resolve locally. Ask Git to fail if it does not.
            revisions.append("^" + oid("rev-parse", "--verify", remote + "^{commit}"))
        for commit in oid("rev-list", "--reverse", *revisions).splitlines():
            if commit not in seen:
                require_review(trees(commit), f"推送 {target} 的提交 {commit}（show --commit {commit}）")
                seen.add(commit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    show = commands.add_parser("show", help="显示审查范围及实际差异")
    record = commands.add_parser("record", help="记录当前 AI 对该范围的实读结论")
    for command in (show, record):
        command.add_argument("--commit", help="审查一个已有提交，默认审查暂存区")
    record.add_argument("--scope", required=True, help="show 输出的两棵 Git 树")
    record.add_argument("--summary", required=True, help="实际检查的代码、风险及验证结果")
    commands.add_parser("check-staged", help="提交钩子核对暂存区")
    commands.add_parser("check-push", help="读取 Git pre-push 提供的引用")
    args = parser.parse_args()
    if args.command == "check-push":
        check_push(sys.stdin)
        return
    pair = trees(getattr(args, "commit", None))
    scope = "..".join(pair)
    if args.command == "show":
        print("scope " + scope, flush=True)
        sys.stdout.buffer.write(git(Path.cwd(), "diff", "--no-ext-diff", "--no-textconv", "--no-color", "--ignore-submodules=none", *pair, "--"))
    elif args.command == "record":
        if scope != args.scope or not args.summary.strip():
            raise ValueError("审查范围已变化或结论为空。请重新查看差异后记录。")
        file = review_file(scope)
        file.parent.mkdir(parents=True, exist_ok=True)
        result = dict(scope=scope, summary=args.summary.strip(), reviewed_at=datetime.now(timezone.utc).isoformat())
        replace(file, json.dumps(result, ensure_ascii=False, indent=2).encode())
        print(f"已记录 AI 审查 {scope}")
    else:
        require_review(pair, "暂存内容")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as exc:
        raise SystemExit(f"[AI 代码审查] {exc}")

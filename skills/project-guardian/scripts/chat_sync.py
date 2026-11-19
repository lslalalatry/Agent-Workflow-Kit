#!/usr/bin/env python3
"""Read the shared tracking documents and publish a decision against the version read."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import acceptance

DOCS = ("DECISIONS.md", "TODO.md", "SPEC.md", "FORMULA.md", "STATUS.md", "BACKLOG.md")
DECISION_ID = re.compile(r"(?<![A-Za-z0-9_-])D-[0-9]+(?![A-Za-z0-9_-])")
MARKER = re.compile(r"^<!-- guardian-decision (D-[0-9]+) affects=(.*?) -->$", re.M)
META = ".guardian-base.json"


def includes_id(text, ident):
    return re.search(r"(?<![A-Za-z0-9_-])" + re.escape(ident) + r"(?![A-Za-z0-9_-])", text) is not None


def links(ledger):
    result = {}
    for ident, raw in MARKER.findall(ledger):
        names = raw.split(",") if raw else []
        if ident in result or not set(names).issubset(DOCS[1:]):
            raise ValueError(f"{ident} 的决策编号重复或影响范围无效")
        result[ident] = names
    if ledger.count("<!-- guardian-decision ") != len(result):
        raise ValueError("决策同步标记不完整")
    return result


def check_bundle(root, folder, revision, changed):
    ledger = (Path(folder) / DOCS[0]).as_posix()
    relevant = {name: (Path(folder) / name).as_posix() for name in DOCS[1:]}
    if ledger not in changed and changed.isdisjoint(relevant.values()):
        return
    ledger_body = acceptance.document(root, ledger, revision)
    for name, path in relevant.items():
        if path in changed:
            current_ids = set(DECISION_ID.findall(acceptance.document(root, path, revision)))
            older_ids = set(DECISION_ID.findall(acceptance.document(root, path, "HEAD")))
            for ident in current_ids - older_ids:
                if not includes_id(ledger_body, ident):
                    raise ValueError(f"{name} 引用 {ident}，同一版本中缺少对应的 DECISIONS.md 记录")
    if ledger not in changed:
        return
    old = links(acceptance.document(root, ledger, "HEAD"))
    new = links(ledger_body)
    if any(new.get(key) != value for key, value in old.items()):
        raise ValueError("请保留已有决策记录及影响范围，用新编号记录取代关系")
    for ident, affected in new.items():
        if ident in old:
            continue
        for name in affected:
            path = (Path(folder) / name).as_posix()
            body = acceptance.document(root, path, revision)
            if path not in changed or not includes_id(body, ident):
                raise ValueError(f"{ident} 缺少同时交付且引用该编号的 {path}")


def signature(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def read_file(path):
    if path.is_symlink():
        raise ValueError(f"共享文档不能经符号链接写入：{path}")
    return path.read_bytes() if path.exists() else None


def replace(path, data):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        try:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            tmp.unlink()
            raise
    try:
        if path.exists():
            os.chmod(tmp, path.stat().st_mode & 0o777)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


@contextmanager
def lock(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "decision.lock").open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX)
        # Closing the descriptor also releases the lock after failure.
        yield


def finish_write(folder, journal):
    if not journal.exists():
        return
    bundle = json.loads(journal.read_text(encoding="utf-8"))
    if bundle["folder"] != str(folder):
        raise ValueError("上次未完成的写入使用另一追踪目录，请先核对目录配置")
    pending = {}
    for name, entry in bundle["files"].items():
        if name not in DOCS:
            raise ValueError("恢复记录中含未知文件")
        body = entry["text"].encode("utf-8")
        current = read_file(folder / name)
        if current != body:
            if signature(current) != entry["base"]:
                raise ValueError(f"恢复期间 {name} 有其他编辑，请人工合并，已保留现场")
            pending[name] = body
    for name, body in pending.items():
        replace(folder / name, body)
    journal.unlink()


def main():
    from verify_guardrails import parse_agents_profile, resolve_tracking_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["read", "apply"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--draft", type=Path, help="本次对话专用的仓库外临时目录")
    parser.add_argument("--decision", help="新拍板使用新 D-编号")
    parser.add_argument("--affects", nargs="*", choices=DOCS[1:], default=[])
    args = parser.parse_args()
    root = args.root.resolve()
    top = Path(os.fsdecode(acceptance.git(root, "rev-parse", "--show-toplevel")).strip()).resolve()
    if root != top:
        raise ValueError(f"请使用仓库根目录 {top}")
    profile = parse_agents_profile(root / "AGENTS.md")
    folder = resolve_tracking_dir(root, profile["tracking_dir"]).resolve()
    if not folder.is_dir() or (folder != root and root not in folder.parents):
        raise ValueError("请先确认项目追踪目录")
    state = root / os.fsdecode(acceptance.git(root, "rev-parse", "--git-path", "project-guardian")).strip()
    draft = args.draft.resolve() if args.draft else None
    if draft is not None and (draft == root or root in draft.parents):
        raise ValueError("请使用仓库外的临时草稿目录")
    if args.action == "apply" and draft is None:
        raise ValueError("apply 需要 --draft")
    with lock(state):
        journal = state / "decision-pending.json"
        finish_write(folder, journal)
        data = {name: read_file(folder / name) for name in DOCS}
        base = {name: signature(content) for name, content in data.items()}
        metadata = {"root": str(root), "folder": str(folder), "base": base,
                    "rules": signature(read_file(root / "AGENTS.md")),
                    "head": acceptance.git(root, "rev-parse", "--verify", "HEAD", optional=True).decode().strip(),
                    "branch": acceptance.git(root, "symbolic-ref", "-q", "HEAD", optional=True).decode().strip()}
        if args.action == "read":
            if args.decision or args.affects:
                raise ValueError("在 apply 时指定决策和影响范围")
            if draft:
                draft.mkdir(parents=True, exist_ok=True)
                if any(draft.iterdir()):
                    raise ValueError("请为本次读取使用新的空草稿目录")
                for name, content in data.items():
                    if content is not None:
                        (draft / name).write_bytes(content)
                (draft / META).write_text(json.dumps(metadata), encoding="utf-8")
                print(f"已读取最新工作区，请从 {draft} 实读并编辑本次涉及的文件。")
            else:
                for name, content in data.items():
                    if content is not None:
                        print(f"\n--- {name} ---\n" + content.decode("utf-8"))
            return
        if json.loads((draft / META).read_text(encoding="utf-8")) != metadata:
            raise ValueError("草稿过期：工作区或分支已变化。本次写入已拦截，请重新 read，并在最新内容上合并本次改动。")
        updates = {}
        for name in DOCS:
            edited = read_file(draft / name)
            if edited is None and data[name] is not None:
                raise ValueError(f"草稿缺少 {name}，请保留原文件")
            if edited is not None and edited != data[name]:
                updates[name] = edited.decode("utf-8")
        if args.decision:
            ident = args.decision
            if not re.fullmatch(r"D-[0-9]+", ident) or includes_id((data[DOCS[0]] or b"").decode(), ident):
                raise ValueError("请使用当前决策记录中尚未使用的 D-编号")
            affected = sorted(set(args.affects))
            if set(updates) != {DOCS[0], *affected}:
                raise ValueError("请同时更新 DECISIONS.md 和 --affects 列出的全部受影响文档")
            if any(not includes_id(body, ident) for body in updates.values()):
                raise ValueError(f"请在决策和每份受影响文档的相关条目引用 {ident}")
            ledger = updates[DOCS[0]]
            original = (data[DOCS[0]] or b"").decode()
            if set(DECISION_ID.findall(original)) - set(DECISION_ID.findall(ledger)):
                raise ValueError("请保留原有决定编号及其历史，写明新决定的取代关系")
            if links(ledger) != links(original):
                raise ValueError("请保留既有同步标记，新增标记由工具填写")
            updates[DOCS[0]] = ledger.rstrip() + f"\n\n<!-- guardian-decision {ident} affects={','.join(affected)} -->\n"
        elif args.affects or DOCS[0] in updates:
            raise ValueError("记录拍板需要 --decision；一般进度可直接 apply")
        if updates:
            transaction = {"folder": str(folder), "files": {
                name: {"base": base[name], "text": body} for name, body in updates.items()}}
            replace(journal, json.dumps(transaction, ensure_ascii=False).encode())
            finish_write(folder, journal)
            print("已更新工作区：" + ", ".join(updates))
        else:
            print("草稿无变更")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        raise SystemExit(str(exc))

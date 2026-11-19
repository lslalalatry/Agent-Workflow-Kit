#!/usr/bin/env python3
"""Record project-specific observations and verify them against the proposed Git snapshot."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
CASE_NAMES = {"normal", "boundary", "counterexample"}


def git(root, *args, optional=False):
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if proc.returncode and not optional:
        raise ValueError("Git 读取失败：" + proc.stderr.decode(errors="replace").strip())
    return proc.stdout if proc.returncode == 0 else b""


def paths(raw):
    return [os.fsdecode(path) for path in raw.split(b"\0") if path]


def document(root, name, revision):
    if revision == "work":
        path = root / name
        return path.read_text(encoding="utf-8") if path.is_file() else ""
    return git(root, "show", f"{revision}:{name}", optional=True).decode("utf-8")


def parse_checks(source, kind):
    tag = "guardian-" + kind
    if not re.search(r"^```" + tag + r"[ \t]*$", source, re.M):
        return {}
    blocks = re.findall(r"^```" + tag + r"[ \t]*\r?\n(.*?)^```[ \t]*\r?$", source, re.M | re.S)
    if len(blocks) != 1:
        raise ValueError(f"请使用一个完整的 {tag} JSON 块")
    checks = json.loads(blocks[0])
    if not isinstance(checks, dict):
        raise ValueError(f"{tag} 必须是以检查 ID 为键的对象")
    for ident, spec in checks.items():
        if not IDENTIFIER.fullmatch(ident) or not isinstance(spec, dict):
            raise ValueError(f"{tag} 检查 ID 或定义无效：{ident}")
        for key in ("argv", "covers" if kind == "default" else "paths"):
            values = spec.get(key)
            if not isinstance(values, list) or not values or not all(isinstance(v, str) and v.strip() for v in values):
                raise ValueError(f"{ident} 缺少有效的 {key}")
        if kind == "default":
            if "paths" in spec and (not isinstance(spec["paths"], list) or not spec["paths"]
                                    or not all(isinstance(v, str) and v.strip() for v in spec["paths"])):
                raise ValueError(f"{ident} 的 paths 应为非空路径列表")
            if not all(isinstance(spec.get(k), str) and spec[k].strip() for k in ("entrypoint", "data")) or "expected" not in spec:
                raise ValueError(f"{ident} 缺少默认入口、输入批次或期望值")
        else:
            if "covers" in spec and (not isinstance(spec["covers"], list)
                                     or not all(isinstance(v, str) and v.strip() for v in spec["covers"])):
                raise ValueError(f"{ident} 的 covers 应为任务 ID 列表")
            cases = spec.get("cases")
            if not isinstance(cases, dict) or not CASE_NAMES.issubset(cases):
                raise ValueError(f"{ident} 必须提供正常、边界、反例三类样例")
            for name, case in cases.items():
                if not isinstance(case, dict) or not {"input", "expected"}.issubset(case):
                    raise ValueError(f"{ident}/{name} 缺少输入或手算期望值")
    return checks


def completed(source):
    """Read status cells in tracking tables and ordinary Markdown checklists."""
    result = set()
    in_fence = False
    for raw in source.splitlines():
        line = raw.strip()
        if line.startswith(("```", "~~~")):
            in_fence = not in_fence
        if in_fence or not line or line.startswith(">"):
            continue
        if line.startswith("|"):
            cells = [s.strip(" *`\t") for s in line.strip("|").split("|")]
            if any(re.match(r"^\[[xX]\](?:\s|$)", c) for c in cells[1:]):
                result.add(cells[0])
        else:
            item = re.match(r"^[-*+]\s+\[[xX]\]\s+(.*)$", line)
            if item:
                words = item[1].lstrip("*`").split()
                if not words:
                    raise ValueError("完成项缺少任务 ID")
                result.add(words[0].rstrip("*`:："))
    return result


def pack(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":"))


def same_output(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(
            same_output(actual[key], value) for key, value in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            same_output(a, b) for a, b in zip(actual, expected))
    if type(expected) in (int, float):
        return type(actual) in (int, float) and actual == expected
    return type(actual) is type(expected) and actual == expected


def tracking_paths(folder):
    base = Path(folder)
    return {name: (base / name).as_posix() for name in ("SPEC.md", "FORMULA.md", "TODO.md", "STATUS.md", "BACKLOG.md")}


def outside_receipts(path, folder):
    docs = tracking_paths(folder)
    return path not in (docs["TODO.md"], docs["STATUS.md"], docs["BACKLOG.md"]) and not path.startswith((Path(folder) / "evidence").as_posix() + "/")


def matches_inputs(path, spec):
    patterns = spec.get("paths")
    if not patterns:
        return True
    return path == "AGENTS.md" or path in spec["argv"] or path == spec.get("entrypoint") or any(
        fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def snapshot(root, folder, spec):
    digest = hashlib.sha256(pack(spec).encode("utf-8") + b"\0")
    for entry in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if entry:
            path = os.fsdecode(entry.split(b"\t", 1)[1])
            if outside_receipts(path, folder) and matches_inputs(path, spec):
                digest.update(entry + b"\0")
    return digest.hexdigest()


def ensure_candidate_on_disk(root, folder, spec):
    changed = paths(git(root, "diff", "--name-only", "--no-renames", "-z"))
    new = paths(git(root, "ls-files", "--others", "--exclude-standard", "-z"))
    dirty = [path for path in changed + new if outside_receipts(path, folder) and matches_inputs(path, spec)]
    if dirty:
        raise ValueError("实测依赖与暂存候选不一致，请核对这些文件：" + ", ".join(dirty[:5]))


def contracts(root, folder, revision):
    docs = tracking_paths(folder)
    defaults = parse_checks(document(root, docs["SPEC.md"], revision), "default")
    formulas = parse_checks(document(root, docs["FORMULA.md"], revision), "formula")
    if defaults.keys() & formulas.keys():
        raise ValueError("默认入口和公式检查 ID 必须各自唯一")
    return defaults, formulas


def expected_output(spec):
    if "cases" in spec:
        return {name: case["expected"] for name, case in spec["cases"].items()}
    return {"entrypoint": spec["entrypoint"], "data": spec["data"], "actual": spec["expected"]}


def receipt_files(root, folder, ident):
    public = Path(folder) / "evidence" / (ident + ".json")
    private = git(root, "rev-parse", "--git-path", "project-guardian/observed/" + ident + ".json").decode().strip()
    return public, root / private


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, encoding="utf-8", delete=False) as out:
        json.dump(data, out, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        out.write("\n")
    os.replace(out.name, path)


def record(root, folder, ident):
    defaults, formulas = contracts(root, folder, "")
    spec = defaults.get(ident) or formulas.get(ident)
    if spec is None:
        raise ValueError(f"暂存的 SPEC.md / FORMULA.md 中没有检查 {ident}")
    public, private = receipt_files(root, folder, ident)
    private.unlink(missing_ok=True)
    ensure_candidate_on_disk(root, folder, spec)
    version = snapshot(root, folder, spec)
    inputs = {k: v["input"] for k, v in spec.get("cases", {}).items()}
    proc = subprocess.run(spec["argv"], cwd=root, input=pack(inputs), capture_output=True, text=True)
    if proc.returncode:
        raise ValueError(f"{ident} 观察命令退出 {proc.returncode}，请直接检查该命令的输出")
    actual = json.loads(proc.stdout)
    expected = expected_output(spec)
    if not same_output(actual, expected):
        raise ValueError(f"{ident} 实测不符。预期 {pack(expected)[:600]}，实得 {pack(actual)[:600]}")
    ensure_candidate_on_disk(root, folder, spec)
    if snapshot(root, folder, spec) != version:
        raise ValueError("实测期间暂存版本已变更，请重新运行")
    receipt = {"id": ident, "snapshot": version, "observed_at": datetime.now(timezone.utc).isoformat(), "actual": actual}
    write_json(root / public, receipt)
    write_json(private, receipt)
    print(f"{ident} 实测通过。请把 {public} 与本次验收一起暂存。")


def check_receipt(root, folder, ident, spec, revision, version):
    public, private = receipt_files(root, folder, ident)
    raw = document(root, public.as_posix(), revision)
    if not raw or not private.is_file():
        raise ValueError(f"{ident} 缺少本次实测。运行 acceptance.py {ident} --root . 并暂存证据")
    receipt = json.loads(raw)
    if (not isinstance(receipt, dict) or receipt != json.loads(private.read_text())
            or receipt.get("snapshot") != version or receipt.get("id") != ident
            or not same_output(receipt.get("actual"), expected_output(spec))):
        raise ValueError(f"{ident} 证据与当前候选版本或期望不符，请重跑实测并暂存证据")


def check_changes(root, folder, revision, changes, implementation, formula_enabled):
    docs = tracking_paths(folder)
    if not changes:
        return
    promoted = set()
    promoted_milestones = set()
    active = set()
    for name in ("TODO.md", "STATUS.md"):
        path = docs[name]
        done = completed(document(root, path, revision))
        active.update(done)
        if path in changes:
            newly_done = done - completed(document(root, path, "HEAD"))
            promoted.update(newly_done)
            if name == "STATUS.md":
                promoted_milestones.update(newly_done)

    defaults, formulas = contracts(root, folder, revision)
    required = {}
    for task in sorted(promoted):
        matching = {key: spec for key, spec in defaults.items() if task in spec["covers"]}
        if not matching:
            raise ValueError(f"{task} 升为 [x] 缺少已登记的默认入口验收。请先保留 [~] 或在 SPEC.md 配置 guardian-default")
        required.update(matching)

    old_defaults = {}
    if docs["SPEC.md"] in changes:
        old_defaults = parse_checks(document(root, docs["SPEC.md"], "HEAD"), "default")
        for key, previous in old_defaults.items():
            lost = active.intersection(previous["covers"]) - set(defaults.get(key, {}).get("covers", []))
            for task in lost:
                replacements = {i: s for i, s in defaults.items() if task in s["covers"]}
                if not replacements:
                    raise ValueError(f"{task} 仍是 [x]，请保留有效验收或将任务重新打开")
                required.update(replacements)
    for key, spec in defaults.items():
        if not active.intersection(spec["covers"]):
            continue
        contract_changed = docs["SPEC.md"] in changes and spec != old_defaults.get(key)
        receipt_path = (Path(folder) / "evidence" / (key + ".json")).as_posix()
        input_candidates = changes if "paths" in spec else implementation
        if (contract_changed or receipt_path in changes or "AGENTS.md" in changes
                or any(matches_inputs(p, spec) and outside_receipts(p, folder) for p in input_candidates)):
            required[key] = spec

    if formula_enabled or formulas or document(root, docs["FORMULA.md"], revision):
        if not formulas and (implementation or promoted_milestones or
                             (docs["FORMULA.md"] in changes and parse_checks(document(root, docs["FORMULA.md"], "HEAD"), "formula"))):
            raise ValueError("涉算项目尚未登记可执行的三组公式样例，请在 FORMULA.md 配置 guardian-formula")
        previous_formulas = {}
        if docs["FORMULA.md"] in changes:
            previous_formulas = parse_checks(document(root, docs["FORMULA.md"], "HEAD"), "formula")
        for key, spec in formulas.items():
            contract_changed = docs["FORMULA.md"] in changes and spec != previous_formulas.get(key)
            affected = any(matches_inputs(path, spec) for path in changes)
            receipt_path = (Path(folder) / "evidence" / (key + ".json")).as_posix()
            covered = promoted.intersection(spec.get("covers", []))
            if promoted_milestones or covered or contract_changed or affected or receipt_path in changes:
                required[key] = spec

    for ident, spec in required.items():
        if revision == "work":
            ensure_candidate_on_disk(root, folder, spec)
        check_receipt(root, folder, ident, spec, revision, snapshot(root, folder, spec))


if __name__ == "__main__":
    from verify_guardrails import parse_agents_profile, resolve_tracking_dir
    parser = argparse.ArgumentParser(description="实跑已审阅的项目观察命令，记录默认入口或手算样例的结果")
    parser.add_argument("check", help="SPEC.md 或 FORMULA.md 中的检查 ID")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        profile = parse_agents_profile(root / "AGENTS.md")
        folder = resolve_tracking_dir(root, profile["tracking_dir"]).relative_to(root)
        record(root, folder, args.check)
    except (ValueError, OSError, UnicodeError) as exc:
        sys.exit(f"[验收未通过] {exc}")

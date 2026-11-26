#!/usr/bin/env python3
"""
Progressive documentation search & targeted section reader for project-guardian.

Allows agents in large multi-module repositories to:
1. Search compact indexes across tracking docs (SPEC/DECISIONS/FORMULA/TODO/STATUS)
   and architecture docs (docs/architecture/*.md, modules/*.md) without loading full files.
2. Read only matched D-ID / F-ID / heading sections or bounded line ranges.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from verify_guardrails import parse_agents_profile, resolve_tracking_dir

ID_PATTERN = re.compile(r"\b([DF]-\d{3,}|REQ-\d+|M\d+)\b")
HEADING_PATTERN = re.compile(r"^(#{1,4})\s+(.+?)\s*$")
MAX_SNIPPET_CHARS = 120


@dataclass
class DocEntry:
    source: str
    kind: str
    section_id: str
    title: str
    line_start: int
    line_end: int
    snippet: str
    body_text: str


def normalize_snippet(text: str, max_chars: int = MAX_SNIPPET_CHARS) -> str:
    collapsed = " ".join(line.strip() for line in text.splitlines() if line.strip())
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[: max_chars - 3].rstrip() + "..."


def classify_doc(rel_path: str) -> str:
    norm = rel_path.replace("\\", "/")
    name = Path(norm).name.upper()
    if name == "DECISIONS.MD":
        return "decisions"
    if name == "FORMULA.MD":
        return "formulas"
    if name == "SPEC.MD":
        return "lexicon"
    if "/modules/" in f"/{norm}" or norm.startswith("docs/architecture/modules/"):
        return "modules"
    if "docs/architecture/" in norm:
        return "architecture"
    return "tracking"


def collect_doc_files(root: Path, kind_filter: str) -> List[Tuple[Path, str]]:
    agents_path = root / "AGENTS.md"
    tracking_dir = root / "docs" / "tracking"
    if agents_path.exists():
        profile = parse_agents_profile(agents_path)
        configured = str(profile.get("tracking_dir") or "docs/tracking")
        tracking_dir = resolve_tracking_dir(root, configured)

    candidates: List[Path] = []
    for filename in ("DECISIONS.md", "SPEC.md", "FORMULA.md", "TODO.md", "STATUS.md", "BACKLOG.md"):
        path = tracking_dir / filename
        if path.is_file():
            candidates.append(path)

    arch_dir = root / "docs" / "architecture"
    if arch_dir.is_dir():
        for md_file in sorted(arch_dir.glob("*.md")):
            if md_file.is_file():
                candidates.append(md_file)
        modules_dir = arch_dir / "modules"
        if modules_dir.is_dir():
            for md_file in sorted(modules_dir.glob("*.md")):
                if md_file.is_file() and md_file.name != "_TEMPLATE.md":
                    candidates.append(md_file)

    results: List[Tuple[Path, str]] = []
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        rel = resolved.relative_to(root.resolve()).as_posix()
        doc_kind = classify_doc(rel)
        if kind_filter != "all" and doc_kind != kind_filter:
            # SPEC.md is indexed under both 'lexicon' and 'tracking'
            if not (kind_filter == "tracking" and Path(rel).name == "SPEC.md"):
                continue
        results.append((resolved, rel))
    return results


def extract_entries(path: Path, rel_path: str) -> List[DocEntry]:
    lines = path.read_text(encoding="utf-8").splitlines()
    doc_kind = classify_doc(rel_path)
    entries: List[DocEntry] = []

    headings: List[Tuple[int, str, str]] = []
    for idx, line in enumerate(lines, start=1):
        match = HEADING_PATTERN.match(line)
        if match:
            headings.append((idx, match.group(1), match.group(2).strip()))

    if not headings:
        full_body = "\n".join(lines)
        id_match = ID_PATTERN.search(full_body)
        entries.append(
            DocEntry(
                source=rel_path,
                kind=doc_kind,
                section_id=id_match.group(1) if id_match else Path(rel_path).stem,
                title=Path(rel_path).name,
                line_start=1,
                line_end=max(1, len(lines)),
                snippet=normalize_snippet(full_body),
                body_text=full_body,
            )
        )
        return entries

    for idx, (start_line, _hashes, heading_title) in enumerate(headings):
        end_line = headings[idx + 1][0] - 1 if idx + 1 < len(headings) else len(lines)
        section_lines = lines[start_line - 1 : end_line]
        body_text = "\n".join(section_lines)
        body_without_heading = "\n".join(section_lines[1:])
        id_match = ID_PATTERN.search(heading_title) or ID_PATTERN.search(body_without_heading)
        section_id = id_match.group(1) if id_match else f"L{start_line}"
        entries.append(
            DocEntry(
                source=rel_path,
                kind=doc_kind,
                section_id=section_id,
                title=heading_title,
                line_start=start_line,
                line_end=end_line,
                snippet=normalize_snippet(body_without_heading or heading_title),
                body_text=body_text,
            )
        )

    # Also index individual markdown table rows that contain D-xxx / F-xxx or terms in SPEC/DECISIONS/FORMULA
    if Path(rel_path).name in {"SPEC.md", "DECISIONS.md", "FORMULA.md"}:
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not (stripped.startswith("|") and stripped.endswith("|")):
                continue
            if stripped.startswith("| :") or stripped.startswith("|---") or "标准中文名" in stripped or "唯一编码" in stripped:
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if not cells or all(not c or set(c) <= {"-", ":"} for c in cells):
                continue
            id_match = ID_PATTERN.search(stripped)
            row_id = id_match.group(1) if id_match else (cells[1].strip("`") if len(cells) > 1 else f"L{line_no}")
            row_title = " / ".join(c for c in cells[:2] if c)
            entries.append(
                DocEntry(
                    source=rel_path,
                    kind=doc_kind,
                    section_id=row_id,
                    title=row_title,
                    line_start=line_no,
                    line_end=line_no,
                    snippet=normalize_snippet(" | ".join(cells[2:]) or stripped),
                    body_text=stripped,
                )
            )

    return entries


def score_entry(entry: DocEntry, tokens: List[str]) -> int:
    if not tokens:
        return 1
    hay_title = f"{entry.section_id} {entry.title} {entry.source}".lower()
    hay_body = entry.body_text.lower()
    score = 0
    for token in tokens:
        if token in hay_title:
            score += 3
        elif token in hay_body:
            score += 1
        else:
            return 0
    return score


def run_search(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    files = collect_doc_files(root, args.kind)
    tokens = [tok.lower() for tok in args.query.split() if tok.strip()]

    scored: List[Tuple[int, DocEntry]] = []
    for file_path, rel_path in files:
        for entry in extract_entries(file_path, rel_path):
            score = score_entry(entry, tokens)
            if score > 0:
                scored.append((score, entry))

    scored.sort(key=lambda item: (-item[0], item[1].source, item[1].line_start))
    limited = [item[1] for item in scored[: args.limit]]

    if args.json:
        payload = {
            "root": str(root),
            "query": args.query,
            "total_matches": len(scored),
            "returned": len(limited),
            "results": [
                {
                    "source": e.source,
                    "kind": e.kind,
                    "id": e.section_id,
                    "title": e.title,
                    "line_start": e.line_start,
                    "line_end": e.line_end,
                    "snippet": e.snippet,
                }
                for e in limited
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not limited:
        print(f"[query_docs] No matches for query={args.query!r} under {root}")
        return 0

    print(f"[query_docs] {len(limited)}/{len(scored)} match(es) under {root}:")
    for e in limited:
        print(f"- {e.source}:L{e.line_start}-L{e.line_end} | [{e.section_id}] {e.title}")
        if e.snippet:
            print(f"  {e.snippet}")
    return 0


def find_section_range(lines: List[str], section_query: str) -> Optional[Tuple[int, int]]:
    q = section_query.strip().lower()
    headings: List[Tuple[int, str]] = []
    for idx, line in enumerate(lines, start=1):
        match = HEADING_PATTERN.match(line)
        if match:
            headings.append((idx, match.group(2).strip()))

    for idx, (start_line, title) in enumerate(headings):
        end_line = headings[idx + 1][0] - 1 if idx + 1 < len(headings) else len(lines)
        block = "\n".join(lines[start_line - 1 : end_line])
        if q in title.lower() or (ID_PATTERN.match(section_query.strip()) and q in block.lower()):
            return start_line, end_line

    # Fallback: single matching line (e.g. table row containing D-001 or term)
    for line_no, line in enumerate(lines, start=1):
        if q in line.lower():
            return max(1, line_no - 2), min(len(lines), line_no + 2)
    return None


def run_read(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    target = (root / args.path).resolve()
    try:
        rel_path = target.relative_to(root).as_posix()
    except ValueError:
        print(f"[query_docs] Error: path escapes project root: {args.path}", file=sys.stderr)
        return 2

    if not target.is_file():
        print(f"[query_docs] Error: file not found: {rel_path}", file=sys.stderr)
        return 2

    lines = target.read_text(encoding="utf-8").splitlines()
    total_lines = len(lines)

    start_line = args.start_line
    end_line = total_lines

    if args.section:
        found = find_section_range(lines, args.section)
        if found is None:
            print(f"[query_docs] Section {args.section!r} not found in {rel_path}", file=sys.stderr)
            return 1
        sec_start, sec_end = found
        start_line = max(sec_start, args.start_line)
        end_line = sec_end

    if start_line < 1:
        start_line = 1
    window_end = min(end_line, start_line + args.max_lines - 1)
    truncated = window_end < end_line
    sliced = lines[start_line - 1 : window_end]

    if args.json:
        payload = {
            "source": rel_path,
            "start_line": start_line,
            "end_line": window_end,
            "section_end": end_line,
            "total_lines": total_lines,
            "truncated": truncated,
            "next_start_line": window_end + 1 if truncated else None,
            "content": "\n".join(f"L{start_line + idx}: {text}" for idx, text in enumerate(sliced)),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"=== {rel_path} (L{start_line}-L{window_end} / {end_line} total={total_lines}) ===")
    for idx, text in enumerate(sliced):
        print(f"L{start_line + idx}: {text}")
    if truncated:
        print(f"... [truncated; re-run with --start-line {window_end + 1}]")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Progressive search and bounded section reader for project-guardian tracking & architecture docs."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_p = subparsers.add_parser("search", help="Search compact index across tracking & architecture docs.")
    search_p.add_argument("--root", default=".", help="Project root directory (default: current directory).")
    search_p.add_argument("--query", default="", help="Space-separated keywords or ID (e.g. D-001 F-002 media_assets). Empty lists index.")
    search_p.add_argument(
        "--kind",
        default="all",
        choices=["all", "decisions", "formulas", "lexicon", "modules", "architecture", "tracking"],
        help="Restrict search scope (default: all).",
    )
    search_p.add_argument("--limit", type=int, default=20, help="Maximum number of results to return (default: 20).")
    search_p.add_argument("--json", action="store_true", help="Output structured JSON.")

    read_p = subparsers.add_parser("read", help="Read a specific section or bounded line slice of a project doc.")
    read_p.add_argument("--root", default=".", help="Project root directory (default: current directory).")
    read_p.add_argument("--path", required=True, help="Relative path from project root (e.g. docs/tracking/DECISIONS.md).")
    read_p.add_argument("--section", default="", help="Optional D-ID, F-ID, or heading substring to narrow slice.")
    read_p.add_argument("--start-line", type=int, default=1, help="1-based start line (default: 1).")
    read_p.add_argument("--max-lines", type=int, default=80, help="Maximum lines per read (default: 80).")
    read_p.add_argument("--json", action="store_true", help="Output structured JSON.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "search":
        return run_search(args)
    if args.command == "read":
        return run_read(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())

"""Regex search across THIS BRAIN'S OWN Claude Code session JSONL transcripts --
never another project's, and never anything under a decoy or sibling directory.

Usage:
    python search.py "<regex>" [--before N] [--after N] [--limit N]
                               [--max-lines N] [--role user|assistant|any]
                               [--since YYYY-MM-DD] [--verbose] [--root PATH]
    python search.py --session <id> --slice START:END [--verbose] [--root PATH]

Reads transcripts only -- writes nothing, ever. Imports only the standard library, so
it runs whether or not synaptra (or any MCP server) is reachable.

`--root PATH` overrides brain-root resolution -- for the check script's scratch trees
only; the real invocation from the skill never passes it, so it always resolves the
brain root and the transcripts directory fresh, at runtime.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

VERBOSE = False


def log_opened(path: Path) -> None:
    if VERBOSE:
        print(f"[open] {path}", file=sys.stderr)


def brain_root(start: Path | None = None) -> Path | None:
    """Walk up from `start` (default: this file's own directory) to the first
    directory holding both `.claude/` and `CLAUDE.md`. Never hardcoded -- this is
    resolved fresh, every run, relative to where this script actually lives."""
    here = start or Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / ".claude").is_dir() and (candidate / "CLAUDE.md").is_file():
            return candidate
    return None


def encode_root(root: Path) -> str:
    """Encode an absolute path the way Claude Code names a transcript directory under
    `~/.claude/projects/`: every path separator, drive colon, and literal dot becomes
    `-`. Verified against this machine's real `~/.claude/projects/` listing --
    e.g. `C:\\Projects\\second-brain` -> `C--Projects-second-brain`."""
    return re.sub(r"[\\/:.]", "-", str(root))


def extract_text(msg: dict) -> str:
    """Pull plain text out of a message record."""
    m = msg.get("message")
    if not isinstance(m, dict):
        return ""
    content = m.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            t = block.get("type")
            if t == "text":
                parts.append(block.get("text", ""))
            elif t == "tool_use":
                parts.append(
                    f"[tool_use:{block.get('name', '')}] {json.dumps(block.get('input', {}))[:500]}"
                )
            elif t == "tool_result":
                c = block.get("content", "")
                if isinstance(c, list):
                    c = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
                parts.append(f"[tool_result] {str(c)[:500]}")
            elif t == "thinking":
                parts.append(f"[thinking] {block.get('thinking', '')}")
        return "\n".join(parts)
    return ""


def iter_session_files(transcripts_dir: Path):
    """Yield each `.jsonl` path directly under `transcripts_dir`, newest-file-mtime
    order does not matter here -- ordering by match recency happens after parsing,
    from each record's own timestamp. Only ever looks inside `transcripts_dir` --
    never a sibling or parent, which is what keeps AC 8 true."""
    if not transcripts_dir.is_dir():
        return
    for jsonl in sorted(transcripts_dir.glob("*.jsonl")):
        log_opened(jsonl)
        yield jsonl


def load_lines(jsonl_path: Path) -> tuple[list[dict], list[tuple[int, str]]]:
    """Parse a JSONL transcript. Returns (records, malformed) where malformed is a
    list of (line_number, raw_prefix) for any line that failed to parse -- that line
    is skipped, parsing continues with the rest of the file (AC 12)."""
    records: list[dict] = []
    malformed: list[tuple[int, str]] = []
    with jsonl_path.open(encoding="utf-8", errors="replace") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                malformed.append((lineno, line[:200]))
    return records, malformed


def session_timestamp(records: list[dict]) -> datetime | None:
    for rec in records:
        ts = rec.get("timestamp")
        if ts:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(
                    tzinfo=None
                )
            except ValueError:
                pass
    return None


def list_existing_sessions(transcripts_dir: Path) -> list[tuple[str, datetime | None]]:
    """Session id and date for every session in this project, newest first --
    used both for AC 7 (bad --session id) and as the general inventory."""
    out = []
    for path in iter_session_files(transcripts_dir):
        records, _ = load_lines(path)
        out.append((path.stem, session_timestamp(records)))
    out.sort(key=lambda t: (t[1] is not None, t[1]), reverse=True)
    return out


def format_excerpt(rec: dict, max_lines: int) -> str:
    role = rec.get("type", "?")
    if role not in ("user", "assistant"):
        return f"[{role}]"
    text = extract_text(rec).strip()
    if not text:
        return f"[{role}: empty]"
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [
            f"... [truncated, {len(text.splitlines()) - max_lines} more lines -- use --session <id> --slice to expand]"
        ]
    return "\n".join(f"    {ln}" for ln in lines)


def parse_args(argv: list[str] | None = None):
    p = argparse.ArgumentParser(
        description="Search this brain's own Claude Code session transcripts."
    )
    p.add_argument(
        "pattern", nargs="?", help="Regex pattern (required unless --session given)"
    )
    p.add_argument(
        "--before",
        type=int,
        default=2,
        help="Turns of context before each match (default: 2)",
    )
    p.add_argument(
        "--after",
        type=int,
        default=2,
        help="Turns of context after each match (default: 2)",
    )
    p.add_argument(
        "--limit", type=int, default=20, help="Max matches returned (default: 20)"
    )
    p.add_argument(
        "--max-lines",
        type=int,
        default=40,
        help="Truncate each excerpt to N lines (default: 40)",
    )
    p.add_argument("--role", choices=["user", "assistant", "any"], default="any")
    p.add_argument("--since", default=None, help="YYYY-MM-DD")
    p.add_argument("--session", default=None, help="Session id for expand mode")
    p.add_argument("--slice", default=None, help="START:END (1-indexed, inclusive)")
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Log every transcript file opened, to stderr",
    )
    p.add_argument(
        "--projects-dir",
        default=None,
        help=argparse.SUPPRESS,  # test-only override: stand in for ~/.claude/projects
    )
    p.add_argument(
        "--root",
        default=None,
        help=argparse.SUPPRESS,  # test-only override: stand in for the resolved brain root
    )
    return p.parse_args(argv)


def resolve(args) -> tuple[Path | None, Path]:
    """Real resolution: walk up for the brain root, encode it, look under
    `~/.claude/projects/` (or `--projects-dir` / `--root`, test-only overrides for
    the check script's scratch tree -- the skill's real invocation passes neither, so
    every real run resolves both fresh)."""
    root = Path(args.root).resolve() if args.root else brain_root()
    projects_dir = (
        Path(args.projects_dir).resolve()
        if args.projects_dir
        else (Path.home() / ".claude" / "projects")
    )
    if root is None:
        return None, projects_dir / "<unresolved-brain-root>"
    return root, projects_dir / encode_root(root)


def expand_mode(args) -> int:
    root, transcripts_dir = resolve(args)
    if root is None:
        print(
            "Cannot determine brain root: walked up from this script's directory and found no "
            "directory holding both .claude/ and CLAUDE.md. Stopped.",
            file=sys.stderr,
        )
        return 1
    if not transcripts_dir.is_dir():
        print(f"Transcript directory not found: {transcripts_dir}", file=sys.stderr)
        return 1

    for path in iter_session_files(transcripts_dir):
        if path.stem != args.session:
            continue
        records, malformed = load_lines(path)
        for lineno, raw in malformed:
            print(
                f"[malformed] {path.name} line {lineno}: {raw!r} -- skipped",
                file=sys.stderr,
            )
        start, end = 1, len(records)
        if args.slice:
            try:
                s, e = args.slice.split(":")
                start = max(1, int(s))
                end = min(len(records), int(e))
            except ValueError:
                print(
                    f"Invalid --slice '{args.slice}', expected START:END",
                    file=sys.stderr,
                )
                return 2
        print(
            f"session={args.session}  project={transcripts_dir.name}  lines={start}:{end}  total={len(records)}"
        )
        print("---")
        for i in range(start - 1, end):
            rec = records[i]
            role = rec.get("type", "?")
            if role in ("user", "assistant"):
                text = extract_text(rec).strip()
                ts = rec.get("timestamp", "")
                print(f"[{i + 1}] {role}  {ts}")
                for ln in text.splitlines():
                    print(f"    {ln}")
                print()
        return 0

    print(f"Session '{args.session}' not found in {transcripts_dir}.", file=sys.stderr)
    existing = list_existing_sessions(transcripts_dir)
    if existing:
        print("Sessions that do exist in this project, newest first:", file=sys.stderr)
        for sid, ts in existing:
            print(
                f"  {sid}  {ts.isoformat() if ts else 'unknown date'}", file=sys.stderr
            )
    else:
        print("No sessions exist in this project.", file=sys.stderr)
    return 1


def search_mode(args) -> int:
    # AC 5: an invalid regex is reported and NOTHING is searched -- validate before
    # touching the filesystem at all, so zero files are opened on a bad pattern.
    try:
        rx = re.compile(args.pattern, re.IGNORECASE)
    except re.error as e:
        print(f"Invalid regex '{args.pattern}': {e}", file=sys.stderr)
        return 2

    since_dt = None
    if args.since:
        try:
            since_dt = datetime.fromisoformat(args.since)
        except ValueError:
            print(f"Bad --since '{args.since}', expected YYYY-MM-DD", file=sys.stderr)
            return 2

    root, transcripts_dir = resolve(args)
    if root is None:
        print(
            "Cannot determine brain root: walked up from this script's directory and found no "
            "directory holding both .claude/ and CLAUDE.md. Stopped.",
            file=sys.stderr,
        )
        return 1
    if not transcripts_dir.is_dir():
        print(f"Transcript directory not found: {transcripts_dir}", file=sys.stderr)
        return 1

    hits = []
    malformed_reports: list[str] = []
    for path in iter_session_files(transcripts_dir):
        records, malformed = load_lines(path)
        for lineno, raw in malformed:
            malformed_reports.append(f"{path.name} line {lineno}: {raw!r}")
        if not records:
            continue

        session_ts = session_timestamp(records)
        if since_dt and session_ts and session_ts < since_dt:
            continue

        for idx, rec in enumerate(records):
            role = rec.get("type")
            if role not in ("user", "assistant"):
                continue
            if args.role != "any" and role != args.role:
                continue
            text = extract_text(rec)
            if not text:
                continue
            if not rx.search(text):
                continue
            hits.append(
                {
                    "session": path.stem,
                    "project": transcripts_dir.name,
                    "line": idx + 1,
                    "timestamp": rec.get("timestamp", ""),
                    "session_ts": session_ts,
                    "role": role,
                    "records": records,
                    "idx": idx,
                }
            )
            if len(hits) >= args.limit:
                break
        if len(hits) >= args.limit:
            break

    for report in malformed_reports:
        print(
            f"[malformed] {report} -- skipped, other sessions still searched",
            file=sys.stderr,
        )

    if not hits:
        print(f"No matches. Searched: {transcripts_dir}")
        return 0

    # AC 2: newest first.
    hits.sort(
        key=lambda h: (h["session_ts"] is not None, h["session_ts"]), reverse=True
    )

    print(
        f"Found {len(hits)} match(es){' (limit reached)' if len(hits) == args.limit else ''}"
    )
    print("=" * 60)
    for n, h in enumerate(hits, 1):
        records = h["records"]
        start = max(0, h["idx"] - args.before)
        end = min(len(records), h["idx"] + args.after + 1)
        print(f"\n[{n}] session={h['session']}  project={h['project']}")
        print(f"    date={h['timestamp']}  line={h['line']}  role={h['role']}")
        print(f"    context=lines {start + 1}:{end}")
        print()
        for i in range(start, end):
            rec = records[i]
            r = rec.get("type", "?")
            if r not in ("user", "assistant"):
                continue
            marker = ">>>" if i == h["idx"] else "   "
            print(f"  {marker} [{i + 1}] {r}:")
            print(format_excerpt(rec, args.max_lines))
            print()
        print("-" * 60)
    return 0


def main(argv: list[str] | None = None) -> int:
    global VERBOSE
    args = parse_args(argv)
    VERBOSE = args.verbose
    if args.session:
        return expand_mode(args)
    if not args.pattern:
        print("Error: pattern required (or use --session)", file=sys.stderr)
        return 2
    return search_mode(args)


if __name__ == "__main__":
    sys.exit(main())

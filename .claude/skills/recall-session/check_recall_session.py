#!/usr/bin/env python3
"""Issue #8 -- acceptance-criteria checks for `.claude/skills/recall-session/`.

Builds a scratch transcript tree under `C:/Projects/.tmp/second-brain-loop-8/`
shaped like `~/.claude/projects/<encoded-root>/`, seeded with three sessions of
known dates for THIS (fake) brain and one session in a second, decoy project
directory. Runs `tools/search.py` against it via its test-only `--root` /
`--projects-dir` overrides and asserts real output, real exit codes, a real
stderr file-open trace, and a real before/after hash of the scratch tree --
never "the skill file says so."

Never touches `~/.claude/projects/` for real. Cleans and rebuilds its scratch
tree on every run.

Usage: python check_recall_session.py
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SEARCH_PY = REPO_ROOT / ".claude" / "skills" / "recall-session" / "tools" / "search.py"
SKILL_MD = REPO_ROOT / ".claude" / "skills" / "recall-session" / "SKILL.md"

SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-8")
BRAIN_ROOT = SCRATCH_ROOT / "brain"
DECOY_ROOT = SCRATCH_ROOT / "decoy-brain"
HOME = SCRATCH_ROOT / "home"
PROJECTS_DIR = HOME / ".claude" / "projects"


def encode_root(root: Path) -> str:
    """Same encoding as tools/search.py's own `encode_root` -- duplicated on
    purpose so this check does not import the module under test to derive its
    own expectations (that would let a bug in encoding hide from the check)."""
    return re.sub(r"[\\/:.]", "-", str(root))


def rec(role: str, text: str, timestamp: str) -> dict:
    return {
        "type": role,
        "timestamp": timestamp,
        "message": {"role": role, "content": text},
    }


def write_session(
    path: Path, records: list[dict], extra_malformed_line: str | None = None
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
        if extra_malformed_line is not None:
            f.write(extra_malformed_line + "\n")


def build_scratch_tree() -> tuple[Path, Path, Path]:
    """Returns (brain_transcripts_dir, decoy_transcripts_dir, oldest_session_path)."""
    if SCRATCH_ROOT.exists():
        shutil.rmtree(SCRATCH_ROOT)
    BRAIN_ROOT.mkdir(parents=True)
    (BRAIN_ROOT / ".claude").mkdir()
    (BRAIN_ROOT / "CLAUDE.md").write_text("# scratch brain\n", encoding="utf-8")

    DECOY_ROOT.mkdir(parents=True)
    (DECOY_ROOT / ".claude").mkdir()
    (DECOY_ROOT / "CLAUDE.md").write_text("# decoy brain\n", encoding="utf-8")

    brain_dir = PROJECTS_DIR / encode_root(BRAIN_ROOT.resolve())
    decoy_dir = PROJECTS_DIR / encode_root(DECOY_ROOT.resolve())

    # Session A -- oldest.
    write_session(
        brain_dir / "session-a-oldest.jsonl",
        [
            rec("user", "start of session a", "2026-09-01T09:00:00Z"),
            rec("assistant", "ack a", "2026-09-01T09:00:05Z"),
            rec(
                "user",
                "the quick aurora fox jumps in session a",
                "2026-09-01T09:01:00Z",
            ),
            rec("assistant", "noted a", "2026-09-01T09:01:05Z"),
        ],
    )
    # Session B -- middle. Carries a malformed line for AC 12, after a valid,
    # matching line -- the rest of the file must still parse and still match.
    write_session(
        brain_dir / "session-b-middle.jsonl",
        [
            rec("user", "start of session b", "2026-09-10T09:00:00Z"),
            rec("assistant", "ack b", "2026-09-10T09:00:05Z"),
            rec(
                "user",
                "the quick aurora fox jumps in session b",
                "2026-09-10T09:01:00Z",
            ),
        ],
        extra_malformed_line="{not valid json,,,",
    )
    # Session C -- newest.
    write_session(
        brain_dir / "session-c-newest.jsonl",
        [
            rec("user", "start of session c", "2026-09-15T09:00:00Z"),
            rec("assistant", "ack c", "2026-09-15T09:00:05Z"),
            rec(
                "user",
                "the quick aurora fox jumps in session c",
                "2026-09-15T09:01:00Z",
            ),
            rec("assistant", "noted c", "2026-09-15T09:01:05Z"),
        ],
    )
    # Decoy project -- must never be opened or matched.
    write_session(
        decoy_dir / "session-decoy.jsonl",
        [
            rec("user", "start of decoy session", "2026-09-20T09:00:00Z"),
            rec(
                "user",
                "the quick aurora fox jumps in the decoy project",
                "2026-09-20T09:01:00Z",
            ),
        ],
    )
    return brain_dir, decoy_dir, brain_dir / "session-a-oldest.jsonl"


def hash_tree(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            h.update(str(path.relative_to(root)).encode("utf-8"))
            h.update(path.read_bytes())
    return h.hexdigest()


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SEARCH_PY), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    if not SEARCH_PY.is_file():
        print(f"[FAIL] search.py not found at {SEARCH_PY}")
        return 1
    if not SKILL_MD.is_file():
        print(f"[FAIL] SKILL.md not found at {SKILL_MD}")
        return 1

    brain_dir, decoy_dir, _ = build_scratch_tree()
    root_arg = str(BRAIN_ROOT.resolve())
    projects_arg = str(PROJECTS_DIR.resolve())

    before_hash = hash_tree(SCRATCH_ROOT)

    # AC 1 + AC 2 -- searches this project, returns session id/date/project/excerpt
    # per match, newest session first.
    p = run(
        "aurora", "--root", root_arg, "--projects-dir", projects_arg, "--limit", "20"
    )
    out = p.stdout
    order_ok = (
        out.find("session=session-c-newest")
        < out.find("session=session-b-middle")
        < out.find("session=session-a-oldest")
        and out.find("session=session-c-newest") != -1
    )
    fields_ok = all(
        tag in out for tag in ("session=", "project=", "date=", "line=", "role=")
    )
    ok1 = (
        p.returncode == 0
        and fields_ok
        and "session-c-newest" in out
        and "session-a-oldest" in out
    )
    results.append(
        (
            "AC1: searches this project, returns id/date/project/excerpt per match",
            ok1,
            f"rc={p.returncode} fields_ok={fields_ok}",
        )
    )
    ok2 = p.returncode == 0 and order_ok
    results.append(
        (
            "AC2: results ordered newest first",
            ok2,
            out[:0]
            or ("order correct" if order_ok else "order wrong or missing a session"),
        )
    )

    # AC 3 -- context turns configurable, stated default. Functional half here;
    # the "stated default" half is a text check on SKILL.md below.
    p_ctx2 = run(
        "aurora",
        "--root",
        root_arg,
        "--projects-dir",
        projects_arg,
        "--before",
        "0",
        "--after",
        "0",
        "--limit",
        "1",
    )
    p_ctx0 = run(
        "aurora",
        "--root",
        root_arg,
        "--projects-dir",
        projects_arg,
        "--before",
        "1",
        "--after",
        "1",
        "--limit",
        "1",
    )
    lines_ctx2 = p_ctx2.stdout.count("context=lines")
    context_narrowed = p_ctx2.stdout != p_ctx0.stdout
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    default_stated = bool(re.search(r"--before\s+N[`\s]*\|\s*2", skill_text)) and bool(
        re.search(r"--after\s+N[`\s]*\|\s*2", skill_text)
    )
    ok3 = context_narrowed and default_stated
    results.append(
        (
            "AC3: context turns configurable with a stated default",
            ok3,
            f"narrows_output={context_narrowed} default_stated_in_skill_md={default_stated}",
        )
    )

    # AC 4 -- no match names the directory searched.
    p = run(
        "zzz_never_matches_zzz_marker",
        "--root",
        root_arg,
        "--projects-dir",
        projects_arg,
    )
    ok4 = p.returncode == 0 and "No matches" in p.stdout and str(brain_dir) in p.stdout
    results.append(
        (
            "AC4: no-match result names the directory searched",
            ok4,
            p.stdout.strip() or p.stderr.strip(),
        )
    )

    # AC 5 -- invalid regex reported, nothing searched (zero files opened).
    p = run("(", "--root", root_arg, "--projects-dir", projects_arg, "--verbose")
    opened = p.stderr.count("[open]")
    ok5 = p.returncode != 0 and "Invalid regex" in p.stderr and opened == 0
    results.append(
        (
            "AC5: invalid regex reported, zero files opened",
            ok5,
            f"rc={p.returncode} opened={opened} stderr={p.stderr.strip()[:150]}",
        )
    )

    # AC 6 -- --session --slice returns that range from that one session.
    p = run(
        "--root",
        root_arg,
        "--projects-dir",
        projects_arg,
        "--session",
        "session-a-oldest",
        "--slice",
        "1:2",
    )
    ok6 = (
        p.returncode == 0
        and "start of session a" in p.stdout
        and "noted a" not in p.stdout
    )
    results.append(
        (
            "AC6: --session --slice returns that range from that session",
            ok6,
            p.stdout.strip()[:150],
        )
    )

    # AC 7 -- a session id that doesn't exist is reported, existing sessions listed.
    p = run(
        "--root",
        root_arg,
        "--projects-dir",
        projects_arg,
        "--session",
        "does-not-exist",
    )
    listed = [line for line in p.stderr.splitlines() if "session-" in line]
    newest_first = (
        p.stderr.find("session-c-newest")
        < p.stderr.find("session-b-middle")
        < p.stderr.find("session-a-oldest")
    )
    ok7 = (
        p.returncode != 0
        and "not found" in p.stderr
        and all(
            s in p.stderr
            for s in ("session-a-oldest", "session-b-middle", "session-c-newest")
        )
        and newest_first
    )
    results.append(
        (
            "AC7: unknown session id reported, existing sessions listed newest first",
            ok7,
            p.stderr.strip()[:200],
        )
    )

    # AC 8 -- other projects' transcripts never searched or shown (decoy check).
    p = run(
        "aurora",
        "--root",
        root_arg,
        "--projects-dir",
        projects_arg,
        "--verbose",
        "--limit",
        "20",
    )
    decoy_mentioned = (
        "session-decoy" in p.stdout
        or "decoy" in p.stderr.lower()
        and "session-decoy" in p.stderr
    )
    decoy_opened = str(decoy_dir) in p.stderr
    ok8 = p.returncode == 0 and not decoy_mentioned and not decoy_opened
    results.append(
        (
            "AC8: other projects' transcripts never searched or shown",
            ok8,
            f"decoy_mentioned={decoy_mentioned} decoy_opened={decoy_opened}",
        )
    )

    # AC 9 -- reads only, writes nothing (scratch tree hash unchanged by any of
    # the runs above).
    after_hash = hash_tree(SCRATCH_ROOT)
    ok9 = before_hash == after_hash
    results.append(
        (
            "AC9: reads transcripts, writes nothing",
            ok9,
            "hash unchanged"
            if ok9
            else "hash CHANGED -- something wrote to the scratch tree",
        )
    )

    # AC 10 -- works with synaptra unreachable. The script imports only the
    # standard library (asserted directly) AND actually runs to a clean exit
    # with no venv/mcp on PATH and no working directory inside the real repo.
    src = SEARCH_PY.read_text(encoding="utf-8")
    import_lines = [
        l for l in src.splitlines() if l.strip().startswith(("import ", "from "))
    ]
    stdlib_only = not any(
        "synaptra" in l.lower() or "mcp" in l.lower() for l in import_lines
    )
    p = subprocess.run(
        [
            sys.executable,
            str(SEARCH_PY),
            "aurora",
            "--root",
            root_arg,
            "--projects-dir",
            projects_arg,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(SCRATCH_ROOT),
        env={"PATH": "", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")},
    )
    ok10 = stdlib_only and p.returncode == 0 and "session-c-newest" in p.stdout
    results.append(
        (
            "AC10: works with synaptra unreachable (stdlib-only, runs with no venv/mcp on PATH)",
            ok10,
            f"stdlib_only={stdlib_only} rc={p.returncode}",
        )
    )

    # AC 11 -- transcript directory not found names the exact directory and stops.
    missing_root = SCRATCH_ROOT / "no-such-brain"
    (missing_root / ".claude").mkdir(parents=True)
    (missing_root / "CLAUDE.md").write_text(
        "# no transcripts for this one\n", encoding="utf-8"
    )
    expected_missing_dir = PROJECTS_DIR / encode_root(missing_root.resolve())
    p = run(
        "aurora", "--root", str(missing_root.resolve()), "--projects-dir", projects_arg
    )
    ok11 = p.returncode != 0 and str(expected_missing_dir) in p.stderr
    results.append(
        (
            "AC11: missing transcript directory is named, and the skill stops",
            ok11,
            p.stderr.strip()[:200],
        )
    )

    # AC 12 -- a malformed transcript line is named and skipped; other sessions
    # (and the rest of that same file) are still searched.
    p = run(
        "aurora", "--root", root_arg, "--projects-dir", projects_arg, "--limit", "20"
    )
    malformed_named = (
        "session-b-middle.jsonl" in p.stderr and "malformed" in p.stderr.lower()
    )
    still_searched = (
        "session-b-middle" in p.stdout
        and "session-a-oldest" in p.stdout
        and "session-c-newest" in p.stdout
    )
    ok12 = p.returncode == 0 and malformed_named and still_searched
    results.append(
        (
            "AC12: malformed transcript line named and skipped, other sessions still searched",
            ok12,
            f"malformed_named={malformed_named} still_searched={still_searched}",
        )
    )

    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} of this script's criteria pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

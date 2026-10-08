#!/usr/bin/env python3
"""Issue #39 -- the brain learns a managed project's CLAUDE.md and context.

Drives a scratch brain built from `src/` through the owner's door (`claude -p`):
the project is taken in with #38's capability in one session, and asked about in
a fresh one -- what the brain knows must outlive the session that learned it.

  --mode know : AC 2 -- "what do you know about sb-sandbox-alpha?" gets its
                purpose, development method, conventions, and where code and
                tests live (alpha's CLAUDE.md: a greeting command, spec-driven,
                Python 3.11 stdlib-only, small functions named for what they
                return, code in src/, tests in tests/ via unittest).

Usage:
    python check_context.py --build
    python check_context.py --run --mode know
    python check_context.py --verify --mode know

Scratch lives under C:/Projects/.tmp/second-brain-loop-39/. Test projects are the
two private sandboxes only. Costs real money on --run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import scratch_brain as sb

SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-39")
BRAIN = SCRATCH_ROOT / "brain"

MODES = ("know",)


def events(tag: str) -> Path:
    return SCRATCH_ROOT / f"context-events-{tag}.json"


def do_run(mode: str) -> None:
    if mode == "know":
        projects = BRAIN / "projects"
        if projects.exists():
            sb.remove_tree(projects)
        sb.run_owner(
            f"Take this project in: {sb.ALPHA_HTTPS}", events("know-takein"), BRAIN
        )
        sb.run_owner(
            "What do you know about sb-sandbox-alpha?", events("know-ask"), BRAIN
        )


def do_verify(mode: str) -> int:
    results: list[tuple[str, bool, str]] = []

    if mode == "know":
        reply = sb.reply_text(events("know-ask"))
        f = sb.flat(reply)
        purpose = sb.has(r"\bgreet", reply)
        method = sb.has(r"spec[- ]driven|requirement\.md|spec (?:comes )?first", reply)
        conventions = [
            sb.has(r"standard library|stdlib", reply),
            sb.has(r"3\.11", reply),
            sb.has(r"small|named for what they return", reply),
        ]
        code_at = "src/" in f or sb.has(r"\bsrc\b", reply)
        tests_at = "tests/" in f or sb.has(r"\btests\b.{0,40}unittest|unittest", reply)
        ok2 = purpose and method and sum(conventions) >= 2 and code_at and tests_at
        # Informational, not graded: did the asking session open the project's
        # own files, or answer from what was learned at take-in?
        reads = [
            u.get("file_path", "") or u.get("command", "")
            for u in sb.tool_uses(events("know-ask"), "Read", "Bash", "PowerShell")
        ]
        read_project = [r for r in reads if "sb-sandbox-alpha" in sb.flat(r)]
        results.append(
            (
                "AC2: 'what do you know about <project>' gives purpose, method, conventions, code+tests",
                ok2,
                f"purpose={purpose} method={method} conventions={conventions} "
                f"code_at={code_at} tests_at={tests_at} | asked-session reads of the project: {len(read_project)}",
            )
        )

    return sb.report(results)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--mode", choices=MODES, default="know")
    args = ap.parse_args()

    if args.build:
        SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
        sb.build(BRAIN)
        print(f"scratch brain built at {BRAIN}")
        return 0
    if args.run:
        do_run(args.mode)
        return 0
    if args.verify:
        return do_verify(args.mode)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

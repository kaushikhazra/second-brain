#!/usr/bin/env python3
"""Proof for issue #4's AC 8 -- "A memory stored by a beat carries, in its content,
what a future session would get wrong without it; a memory recording only that
something happened is not stored."

Same shape as issue #2's original AC 8 proof, adapted to the heartbeat's `capture`
section: a window with ONE item that merely happened (a sync call) and ONE item that
changes a decision (a migration, with its reason), and a check of the ACTUAL resulting
store count and content against the scratch data -- not the transcript's claim.

The scratch tree is built by `.claude/shared/fixture_scratch_brain.py`, shared with the
other scripted-agent checks. Proved byte-identical to this file's own former
`build_scratch_project()` before the switch.

Never the live store, never the live project. Costs real money per run.

Usage:
    python check_heartbeat_ac8_scripted_agent.py --build
    python check_heartbeat_ac8_scripted_agent.py --run
    python check_heartbeat_ac8_scripted_agent.py --verify --url http://127.0.0.1:8063/mcp
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude

sys.path.insert(0, str(REPO_ROOT / "shared"))

from fixture_scratch_brain import build_scratch_brain  # noqa: E402

SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-4")
SCRATCH_PROJECT = SCRATCH_ROOT / "ac8-heartbeat-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "ac8-heartbeat-scratch-data"

WINDOW = (
    "Had a quick sync call with the hosting provider today. During that call, the "
    "team decided to migrate the staging environment off AWS to a self-hosted VPS, "
    "because the AWS free-tier limits were repeatedly throttling the CI pipeline -- "
    "this replaces the earlier plan to stay on AWS through the beta."
)

CLAUDE_MD = (
    "# CLAUDE.md\n\nScratch test for issue #4's AC 8 proof (heartbeat capture). "
    "Route all memory storage through /create-memory -- never memory_store "
    "directly. There is no surface map or self map in this scratch project; "
    "skip any step that depends on one.\n"
)


def build_scratch_project() -> None:
    build_scratch_brain(
        SCRATCH_PROJECT,
        skills=("create-memory", "heartbeat"),
        shared=("memory/memory-shapes.md",),
        persona=True,
        user=True,
        memory_guard=True,
        mcp="healthy",
        data_dir=SCRATCH_DATA,
        claude_md=CLAUDE_MD,
    )


def do_run() -> None:
    prompt = (
        f'Run /heartbeat "requested by cron". The window since the last beat: {WINDOW}'
    )
    proc = subprocess.run(
        [
            "claude",
            "-p",
            prompt,
            "--permission-mode",
            "bypassPermissions",
            "--mcp-config",
            ".mcp.json",
            "--strict-mcp-config",
            "--output-format",
            "json",
            "--max-budget-usd",
            "0.75",
            "--no-session-persistence",
        ],
        cwd=str(SCRATCH_PROJECT),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    result = json.loads(proc.stdout)
    print(f"cost=${result.get('total_cost_usd'):.4f}")
    print(f"result: {result.get('result')!r}")


def do_verify(cm_path: str, url: str) -> int:
    proc = subprocess.run(
        [cm_path, "--url", url, "--json", "list", "--state", "active", "--limit", "50"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    memories = json.loads(proc.stdout)["data"]["memories"]
    print(f"active memories: {len(memories)}")
    for m in memories:
        print(f"  id={m['id']} type={m['memory_type']} content={m['content']!r}")

    ok_count = len(memories) == 1
    reason_words = ("aws", "throttl", "ci pipeline", "free-tier", "free tier")
    carries_reason = bool(memories) and any(
        w in (memories[0].get("content") or "").lower() for w in reason_words
    )

    print(
        f"\n[{'PASS' if ok_count else 'FAIL'}] AC8: exactly one store, not two: count={len(memories)}"
    )
    print(
        f"[{'PASS' if carries_reason else 'FAIL'}] AC8: content carries the reason (not just that something happened)"
    )

    return 0 if (ok_count and carries_reason) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument("--url", default="http://127.0.0.1:8063/mcp")
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print("scratch project built")
        return 0
    if args.run:
        do_run()
        return 0
    if args.verify:
        return do_verify(args.cm, args.url)

    print("pass one of --build / --run / --verify", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Proof for issue #4's AC 8 -- "A memory stored by a beat carries, in its content,
what a future session would get wrong without it; a memory recording only that
something happened is not stored."

Same shape as issue #2's original AC 8 proof, adapted to the heartbeat's `capture`
section: a window with ONE item that merely happened (a sync call) and ONE item that
changes a decision (a migration, with its reason), and a check of the ACTUAL resulting
store count and content against the scratch data -- not the transcript's claim.

Never the live store, never the live project. Costs real money per run.

Usage:
    python check_heartbeat_ac8_scripted_agent.py --build
    python check_heartbeat_ac8_scripted_agent.py --run
    python check_heartbeat_ac8_scripted_agent.py --verify --url http://127.0.0.1:8063/mcp
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-4")
SCRATCH_PROJECT = SCRATCH_ROOT / "ac8-heartbeat-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "ac8-heartbeat-scratch-data"

WINDOW = (
    "Had a quick sync call with the hosting provider today. During that call, the "
    "team decided to migrate the staging environment off AWS to a self-hosted VPS, "
    "because the AWS free-tier limits were repeatedly throttling the CI pipeline -- "
    "this replaces the earlier plan to stay on AWS through the beta."
)


def build_scratch_project() -> None:
    if SCRATCH_PROJECT.exists():
        shutil.rmtree(SCRATCH_PROJECT)

    for skill in ("create-memory", "heartbeat"):
        dest = SCRATCH_PROJECT / ".claude" / "skills" / skill
        dest.mkdir(parents=True, exist_ok=True)
        src = REPO_ROOT / "skills" / skill
        for f in src.glob("*"):
            if f.is_file():
                shutil.copy(f, dest / f.name)

    (SCRATCH_PROJECT / ".claude" / "shared" / "memory").mkdir(
        parents=True, exist_ok=True
    )
    shutil.copy(
        REPO_ROOT / "shared" / "memory" / "memory-shapes.md",
        SCRATCH_PROJECT / ".claude" / "shared" / "memory" / "memory-shapes.md",
    )

    (SCRATCH_PROJECT / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
    shutil.copy(
        REPO_ROOT / "hooks" / "memory_guard.py",
        SCRATCH_PROJECT / ".claude" / "hooks" / "memory_guard.py",
    )
    (SCRATCH_PROJECT / ".claude" / "settings.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "mcp__synaptra__memory_store|mcp__synaptra__memory_update|mcp__synaptra__memory_relate",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python .claude/hooks/memory_guard.py",
                                    "timeout": 5,
                                }
                            ],
                        }
                    ]
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (SCRATCH_PROJECT / "persona.md").write_text(
        "# Testa -- Persona\n\n## Identity\n\n- **Name**: Testa\n- **Voice**: they/them\n"
        "- **Character**: Careful and direct.\n\n## Roles\n\n| Role | What they do |\n"
        "|------|---------------|\n| Research assistant | Finds information |\n\n"
        "## Proactivity\n\nModerate.\n\n## Communication Style\n\n- Direct\n",
        encoding="utf-8",
    )
    (SCRATCH_PROJECT / "user.md").write_text(
        "# Test User\n\n## Personal\n\n- **Name**: Test User\n", encoding="utf-8"
    )
    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nScratch test for issue #4's AC 8 proof (heartbeat capture). "
        "Route all memory storage through /create-memory -- never memory_store "
        "directly. There is no surface map or self map in this scratch project; "
        "skip any step that depends on one.\n",
        encoding="utf-8",
    )
    (SCRATCH_PROJECT / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "synaptra": {
                        "type": "stdio",
                        "command": str(
                            REPO_ROOT / ".venv" / "Scripts" / "synaptra.exe"
                        ),
                        "args": ["--transport", "stdio"],
                        "env": {
                            "SYNAPTRA_BACKEND": "surrealkv-file",
                            "SYNAPTRA_DB": str(SCRATCH_DATA),
                        },
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
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

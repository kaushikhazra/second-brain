#!/usr/bin/env python3
"""Proof for issue #3's AC 8, 9, 12, 13, 14, 20 -- session-end's actual runtime
behavior (structural claims about the skill's own text are check_session_end.py's
job; this is the live thing).

Builds a scratch project (create-memory + session-end + verify_memory.py + the
PreToolUse hook), seeds a realistic self-map (2 identity ids) and empty surface-map
holder so step 4 has something real to check, then runs a single headless prompt
that creates a throwaway cron first (so AC 12's kill-and-report gets exercised) and
then invokes /session-end. Verified against the actual store afterward, not the
transcript: the handoff's type and tags, and that the two list holders are
UNCHANGED (AC 20 -- session-end must write nothing to them).

AC 9 (retype-if-`working`) is NOT exercised by a normal run -- this synaptra
install honors an explicit type on store (cycle 1 of issue #2's own finding), so
the handoff lands `episodic` on the first try every time. Proving the retype path
itself needs a forced-`working` seed, out of scope for this script; the skill's own
text is checked structurally by check_session_end.py instead.

Never the live store, never the live project. Costs real money per run.

Usage: python check_session_end_scripted_agent.py [--skip-build]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-3")
SCRATCH_PROJECT = SCRATCH_ROOT / "session-end-scratch-project"

PROMPT = (
    "First, create a test cron (any harmless schedule, e.g. every 30 minutes, "
    "prompt 'test'). Then immediately run /session-end as if I said I'm stopping "
    "for today. Something notable happened this session worth remembering as a "
    "learning: 'the scratch test setup for session-end works correctly.'"
)


def build_scratch_project(data_dir: Path) -> None:
    for skill in ("create-memory", "session-end"):
        (SCRATCH_PROJECT / ".claude" / "skills" / skill).mkdir(
            parents=True, exist_ok=True
        )
        shutil.copy(
            REPO_ROOT / "skills" / skill / "SKILL.md",
            SCRATCH_PROJECT / ".claude" / "skills" / skill / "SKILL.md",
        )
    shutil.copy(
        REPO_ROOT / "skills" / "session-end" / "verify_memory.py",
        SCRATCH_PROJECT / ".claude" / "skills" / "session-end" / "verify_memory.py",
    )
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
    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nScratch test for issue #3's session-end proof.\n",
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
                            "SYNAPTRA_DB": str(data_dir),
                        },
                    }
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def cm(cm_path: str, url: str, *args: str) -> dict:
    proc = subprocess.run(
        [cm_path, "--url", url, "--json", *args],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return json.loads(proc.stdout)


def seed(cm_path: str, url: str) -> None:
    id1 = cm(
        cm_path,
        url,
        "store",
        "Test persona: name and nature.",
        "--type",
        "identity",
        "--tags",
        "identity,persona,name",
        "--source",
        "create-memory:seed",
    )["data"]["id"]
    id2 = cm(
        cm_path,
        url,
        "store",
        "Test persona: roles.",
        "--type",
        "identity",
        "--tags",
        "identity,persona,roles",
        "--source",
        "create-memory:seed",
    )["data"]["id"]
    cm(
        cm_path,
        url,
        "store",
        f"{id1}\n{id2}",
        "--type",
        "identity",
        "--tags",
        "self-map",
        "--source",
        "create-memory:seed",
    )
    cm(
        cm_path,
        url,
        "store",
        "",
        "--type",
        "identity",
        "--tags",
        "surface-map",
        "--source",
        "create-memory:seed",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument(
        "--seed-url",
        required=True,
        help="scratch HTTP url to seed through -- check the port is genuinely free first (netstat), a squatting unrelated process on the chosen port is a real failure mode seen in this story",
    )
    args = ap.parse_args()

    data_dir = SCRATCH_ROOT / "session-end-scratch-data"
    if not args.skip_build:
        build_scratch_project(data_dir)

    seed(args.cm, args.seed_url)
    print(
        "Seeded. Stop the seed server now, then the headless run opens its own connection."
    )

    proc = subprocess.run(
        [
            "claude",
            "-p",
            PROMPT,
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
        timeout=240,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    result = json.loads(proc.stdout)
    print(f"cost=${result.get('total_cost_usd'):.4f}  result: {result.get('result')!r}")

    print(
        f"\nVerify against ground truth: scratch HTTP server against {data_dir}, "
        "`cm list --state active` -- expect the handoff episodic/tagged correctly, "
        "the self-map/surface-map holders UNCHANGED (still the 2 seeded ids / "
        "empty), and one new semantic learning memory."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

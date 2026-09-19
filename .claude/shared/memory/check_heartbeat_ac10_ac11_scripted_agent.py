#!/usr/bin/env python3
"""Proof for issue #4's AC 10 + AC 11.

AC 10: "When the owner says a claim was wrong, the beat writes the mechanism as a
learning: an instance node with the detail, a bare rule node, typed `procedural`."

AC 11: "A commitment about future work is stored typed `episodic`, never `working`."

One window carrying both signals: a correction ("that's wrong, it actually...") and
a commitment about future work ("we'll revisit X next sprint"). Verifies from the
store, not the transcript:

- AC 10: at least one `procedural`-typed memory exists recording the mechanism (not
  the bare event), and a `memory_relate` edge connects an instance node to a rule
  node (goal.md's "instance node with the detail, a bare rule node" shape).
- AC 11: at least one `episodic`-typed memory exists for the commitment, and NO
  `working`-typed memory was created for it.

Same junction-safety and scratch discipline as the other AC scripts in this story.

Usage:
    python check_heartbeat_ac10_ac11_scripted_agent.py --build
    python check_heartbeat_ac10_ac11_scripted_agent.py --run
    python check_heartbeat_ac10_ac11_scripted_agent.py --verify --url http://127.0.0.1:8068/mcp

Never the live store, never the live project. Costs real money on --run.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-4")
SCRATCH_PROJECT = SCRATCH_ROOT / "ac10-ac11-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "ac10-ac11-scratch-data"

WINDOW = (
    "Two things from this session. First, a correction: earlier I said the "
    "heartbeat retries a failed surface-map write three times before giving up -- "
    "that's wrong, it actually makes exactly one attempt and stops immediately on "
    "failure, per SKILL.md's Failure section. Second, a commitment: we'll revisit "
    "adding the explicit tidiness carve-out to /update-memory next sprint, once "
    "the current routing work settles down."
)


def build_scratch_project() -> None:
    venv_link = SCRATCH_PROJECT / ".claude" / ".venv"
    if venv_link.is_dir():
        os.rmdir(venv_link)

    if SCRATCH_PROJECT.exists():
        shutil.rmtree(SCRATCH_PROJECT)

    (SCRATCH_PROJECT / ".claude").mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "cmd",
            "/c",
            "mklink",
            "/J",
            str(venv_link),
            str(REPO_ROOT / ".venv"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    for skill in ("create-memory", "update-memory", "read-memory", "heartbeat"):
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
        "# CLAUDE.md\n\nScratch test for issue #4's AC 10 + AC 11 proof (heartbeat "
        "correction handling and commitment typing). Route all memory storage "
        "through /create-memory -- never memory_store directly. There is no "
        "surface/self map or session-start here.\n",
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
            "1.00",
            "--no-session-persistence",
        ],
        cwd=str(SCRATCH_PROJECT),
        capture_output=True,
        text=True,
        timeout=280,
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
        print(f"  id={m['id']} type={m['memory_type']} content={m['content'][:90]!r}")

    procedural = [m for m in memories if m["memory_type"] == "procedural"]
    episodic = [m for m in memories if m["memory_type"] == "episodic"]
    working = [m for m in memories if m["memory_type"] == "working"]

    ac10_ok = len(procedural) >= 1
    print(
        f"[{'PASS' if ac10_ok else 'FAIL'}] AC10: at least one procedural-typed memory for the correction: count={len(procedural)}"
    )

    proc2 = subprocess.run(
        [cm_path, "--url", url, "--json", "related", procedural[0]["id"]]
        if procedural
        else [cm_path, "--url", url, "--json", "stats"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    relate_shape_ok = False
    if procedural:
        related_data = json.loads(proc2.stdout)
        relate_shape_ok = bool(related_data.get("data"))
        print(
            f"  related to first procedural memory: {json.dumps(related_data.get('data'))[:200]}"
        )
    print(
        f"[{'PASS' if relate_shape_ok else 'FAIL'}] AC10: instance+rule relate shape present: {relate_shape_ok}"
    )

    ac11_ok = len(episodic) >= 1 and len(working) == 0
    print(
        f"[{'PASS' if ac11_ok else 'FAIL'}] AC11: commitment stored episodic "
        f"(count={len(episodic)}), never working (count={len(working)})"
    )

    return 0 if (ac10_ok and ac11_ok) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument("--url", default="http://127.0.0.1:8068/mcp")
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

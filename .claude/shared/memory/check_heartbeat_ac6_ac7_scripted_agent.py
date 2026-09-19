#!/usr/bin/env python3
"""Proof for issue #4's AC 6 + AC 7.

AC 6: "The beat prints nothing unless something is failing, something time-bound is
closing, or a message from outside the session is addressed to the owner."

AC 7: "The beat's cron prompt carries the words `requested by cron`, and a beat
invoked without them still runs and says it was invoked by hand."

Two scenarios, two fresh scratch runs (same build, different prompt):

  (a) A genuinely quiet window -- nothing failing, nothing time-bound, no outside
      message, nothing capture-worthy either -- WITH the "requested by cron" marker.
      Assert the beat's final output is minimal: no restating what it checked, no
      unprompted narration of a quiet cycle.
  (b) The SAME quiet window, but the prompt omits "requested by cron" entirely.
      Assert the beat still runs (doesn't refuse or ask for confirmation) and its
      output explicitly says it was invoked by hand / manually, per SKILL.md's
      invocation-source-check text.

Same junction-safety and scratch discipline as the other AC scripts in this story.

Usage:
    python check_heartbeat_ac6_ac7_scripted_agent.py --build
    python check_heartbeat_ac6_ac7_scripted_agent.py --run-a
    python check_heartbeat_ac6_ac7_scripted_agent.py --run-b

Never the live store, never the live project. Costs real money on --run-a/--run-b.
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
SCRATCH_PROJECT = SCRATCH_ROOT / "ac6-ac7-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "ac6-ac7-scratch-data"

QUIET_WINDOW = (
    "Spent some time reorganizing a few local files and re-reading some earlier "
    "notes. Nothing failed, nothing is due soon, no messages came in from outside "
    "this session."
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
        "# CLAUDE.md\n\nScratch test for issue #4's AC 6 + AC 7 proof (heartbeat "
        "silence rule and invocation-source marker). Route all memory storage "
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


def run_claude(prompt: str) -> dict:
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
        timeout=280,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    return json.loads(proc.stdout)


def do_run_a() -> int:
    prompt = f'Run /heartbeat "requested by cron". The window since the last beat: {QUIET_WINDOW}'
    r = run_claude(prompt)
    text = r.get("result") or ""
    print(f"cost=${r.get('total_cost_usd'):.4f}")
    print(f"result: {text!r}")

    # "Minimal" heuristic: short, and doesn't narrate the act of checking.
    narration_words = (
        "i checked",
        "i observed",
        "nothing to report",
        "all clear",
        "no action needed",
        "completed successfully",
        "ran successfully",
    )
    is_narrating = any(w in text.lower() for w in narration_words)
    is_short = len(text) < 300
    ok = is_short and not is_narrating
    print(
        f"[{'PASS' if ok else 'FAIL'}] AC6: output is minimal, not unprompted "
        f"narration of a quiet cycle: len={len(text)}, narrating={is_narrating}"
    )
    return 0 if ok else 1


def do_run_b() -> int:
    # Deliberately NO "requested by cron" marker.
    prompt = f"Run /heartbeat. The window since the last beat: {QUIET_WINDOW}"
    r = run_claude(prompt)
    text = r.get("result") or ""
    print(f"cost=${r.get('total_cost_usd'):.4f}")
    print(f"result: {text!r}")

    hand_words = (
        "by hand",
        "manual",
        "manually",
        "not from the cron",
        "no cron marker",
    )
    said_by_hand = any(w in text.lower() for w in hand_words)
    print(
        f"[{'PASS' if said_by_hand else 'FAIL'}] AC7: beat ran without the marker "
        f"and said it was invoked by hand: {said_by_hand}"
    )
    return 0 if said_by_hand else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run-a", action="store_true")
    ap.add_argument("--run-b", action="store_true")
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print("scratch project built")
        return 0
    if args.run_a:
        return do_run_a()
    if args.run_b:
        return do_run_b()

    print("pass one of --build / --run-a / --run-b", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

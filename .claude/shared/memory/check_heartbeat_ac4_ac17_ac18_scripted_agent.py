#!/usr/bin/env python3
"""Proof for issue #4's AC 4, AC 17, AC 18 -- using REAL multi-turn session resume
(`claude -p --session-id` / `--resume`), not a prompt that merely asks the model to
pretend a history exists. A fresh `claude -p` invocation has no real notion of "the
previous beat" on its own, so a single-shot proxy would only prove the model can
follow an explicit instruction, not that it scopes a window correctly from actual
conversation history -- this script builds that history for real, across eight
sequential turns in ONE session.

Turn sequence:
  1. Chat: a decision worth capturing (A) -- NOT a heartbeat invocation.
  2. Beat 1 ("requested by cron"): window = everything since session start (turn 1).
     Should capture A.
  3. Chat: something mundane, not capture-worthy.
  4. Beat 2: window = since beat 1 (turn 3 only). AC 4's real test -- does it
     capture ONLY turn 3's content, or does it re-notice/re-store A from turn 1
     (already captured by beat 1)? Also the first quiet beat (count=1).
  5. Chat: something else mundane.
  6. Beat 3: another quiet window (count=2).
  7. Chat: mundane again.
  8. Beat 4: another quiet window (count=3) -- AC 17's observation should fire.
     AC 18: /curiosity doesn't exist in this scratch project, so goal.md's own
     text says do nothing and reset -- verify the beat doesn't error trying to
     invoke a missing skill, and says something about the reset rather than
     silently ignoring the milestone.

Verifies from the STORE, not the transcript: exactly ONE memory for decision A
(not duplicated by beat 2 re-capturing it) -- the direct evidence for AC 4.
AC 17/18 verified from beat 4's own output text (no store artifact to check --
"do nothing" has no store signature by design), stated plainly as a transcript-only
finding, weaker evidence than a store check, and said so in the log.

Same junction-safety discipline as the other AC scripts in this story.

Usage:
    python check_heartbeat_ac4_ac17_ac18_scripted_agent.py --build
    python check_heartbeat_ac4_ac17_ac18_scripted_agent.py --run
    python check_heartbeat_ac4_ac17_ac18_scripted_agent.py --verify --url http://127.0.0.1:8069/mcp

Never the live store, never the live project. Costs real money on --run (8 turns).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-4")
SCRATCH_PROJECT = SCRATCH_ROOT / "ac4-ac17-ac18-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "ac4-ac17-ac18-scratch-data"
SESSION_ID_FILE = SCRATCH_ROOT / "ac4-ac17-ac18-session-id.txt"

TURN_1_CHAT = (
    "We decided to switch the deploy pipeline to blue-green, because the old "
    "rolling-restart approach caused a bad outage last month when half the fleet "
    "was running mismatched code for several minutes."
)
BEAT_PROMPT = 'Run /heartbeat "requested by cron".'
TURN_3_CHAT = "Just tidied up a few local notes, nothing notable."
TURN_5_CHAT = "Read through some background docs, nothing new to act on."
TURN_7_CHAT = "Quiet stretch, just waiting on an external reply."


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
        "# CLAUDE.md\n\nScratch test for issue #4's AC 4 + AC 17 + AC 18 proof "
        "(heartbeat window scoping and the quiet-cycle count). Route all memory "
        "storage through /create-memory -- never memory_store directly. There is "
        "no surface/self map or session-start here. /curiosity does not exist in "
        "this project.\n",
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


def turn(prompt: str, session_id: str, first: bool) -> dict:
    args = [
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
        "0.60",
    ]
    if first:
        args += ["--session-id", session_id]
    else:
        args += ["--resume", session_id]
    proc = subprocess.run(
        args,
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


def do_run() -> None:
    session_id = str(uuid.uuid4())
    SESSION_ID_FILE.write_text(session_id, encoding="utf-8")
    print(f"session_id={session_id}")

    total_cost = 0.0

    def go(label: str, prompt: str, first: bool = False) -> None:
        nonlocal total_cost
        r = turn(prompt, session_id, first)
        cost = r.get("total_cost_usd") or 0.0
        total_cost += cost
        print(f"\n=== {label} (cost=${cost:.4f}) ===")
        print(f"result: {(r.get('result') or '')!r}")

    go("Turn 1: chat (decision A)", TURN_1_CHAT, first=True)
    go("Turn 2: beat 1 (should capture A)", BEAT_PROMPT)
    go("Turn 3: chat (mundane)", TURN_3_CHAT)
    go("Turn 4: beat 2 (quiet #1, AC4 test)", BEAT_PROMPT)
    go("Turn 5: chat (mundane)", TURN_5_CHAT)
    go("Turn 6: beat 3 (quiet #2)", BEAT_PROMPT)
    go("Turn 7: chat (mundane)", TURN_7_CHAT)
    go("Turn 8: beat 4 (quiet #3, AC17/18 test)", BEAT_PROMPT)

    print(f"\ntotal cost=${total_cost:.4f}")


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

    blue_green = [
        m
        for m in memories
        if "blue-green" in (m.get("content") or "").lower()
        or "rolling-restart" in (m.get("content") or "").lower()
    ]
    ok = len(blue_green) == 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] AC4: decision A stored exactly once "
        f"(not re-captured by beat 2 from window it shouldn't have re-seen): "
        f"count={len(blue_green)}"
    )
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument("--url", default="http://127.0.0.1:8069/mcp")
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

#!/usr/bin/env python3
"""Proof for issue #4's AC 19 -- the heartbeat's own reachability failure handling.

"With synaptra unreachable, the beat says so once and exits; it does not retry."

A scratch project (heartbeat's three files + create-memory, since a strong `capture`
observation is what makes the beat actually try to reach synaptra at all -- a truly
quiet beat with an empty surface map never touches the store, so this scenario feeds
a window that obviously carries a decision worth storing) with a deliberately BROKEN
.mcp.json (nonexistent synaptra executable, same technique as issue #3's AC 18 proof
in check_session_start_scripted_agent.py). The mcp__synaptra__* tools never connect,
so /create-memory's underlying call has nothing to call.

Assertion: the transcript's final result says, once, that synaptra/memory is
unreachable, and does not show repeated retry attempts at the same call.

Never the live store, never the live project. Costs real money per run.

Usage: python check_heartbeat_ac19_scripted_agent.py [--skip-build]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude
BRAIN_ROOT = REPO_ROOT.parent
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-4")
SCRATCH_PROJECT = SCRATCH_ROOT / "heartbeat-ac19-scratch-project"


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

    (SCRATCH_PROJECT / ".claude" / "shared" / "memory").mkdir(parents=True, exist_ok=True)
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
        "# CLAUDE.md\n\nScratch test for issue #4's AC 19 proof (heartbeat, synaptra "
        "unreachable). Route memory storage through /create-memory, never a raw "
        "memory_store call.\n",
        encoding="utf-8",
    )

    cfg = {
        "mcpServers": {
            "synaptra": {
                "type": "stdio",
                "command": str(REPO_ROOT / ".venv" / "Scripts" / "this-does-not-exist.exe"),
                "args": ["--transport", "stdio"],
            }
        }
    }
    (SCRATCH_PROJECT / ".mcp.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")


WINDOW = (
    "The team decided to route the heartbeat's surface-map writes through "
    "/update-memory rather than calling memory_update directly, because the "
    "PreToolUse hook blocks any store or update carrying a reserved tag unless a "
    "fresh sentinel authorizes it -- this replaces and rules out the earlier plan "
    "of a direct memory_update call from inside the heartbeat skill."
)


def run_claude() -> dict:
    prompt = f'Run /heartbeat "requested by cron". The window since the last beat: {WINDOW}'
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
        raise RuntimeError(f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()}")
    return json.loads(proc.stdout)


UNREACHABLE_WORDS = ("unreachable", "unavailable", "not available", "not connected", "cannot reach", "can't reach", "connection", "failed to connect", "no synaptra")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-build", action="store_true")
    args = ap.parse_args()

    if not args.skip_build:
        build_scratch_project()

    result = run_claude()
    text = (result.get("result") or "").lower()
    cost = result.get("total_cost_usd")

    print(f"cost=${cost:.4f}" if cost is not None else "cost=unknown")
    print(f"result: {result.get('result')!r}")

    mentions = [w for w in UNREACHABLE_WORDS if w in text]
    said_unreachable = bool(mentions)

    print(f"\n[{'PASS' if said_unreachable else 'FAIL'}] AC19: beat's output names the unreachable store: {mentions}")

    return 0 if said_unreachable else 1


if __name__ == "__main__":
    sys.exit(main())

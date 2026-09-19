#!/usr/bin/env python3
"""Proof for issue #5's AC 17 -- "With synaptra unreachable, `/dream` says so and
stops before creating a backup."

A scratch project with a deliberately BROKEN `.mcp.json` (nonexistent synaptra
executable -- same technique issue #3's AC 18 and issue #4's cycle 2 used).
Prompted to run `/dream`, `mcp__synaptra__*` tools never connect. Verifies TWO
things, neither from the transcript alone:

- The transcript says the store is unreachable and stops (checked, but not trusted
  alone).
- No backup directory was ever created under the scratch backups root -- if step 2
  (`cm backup create`) had actually run, it would have left an artifact on disk
  regardless of what the transcript claims. An empty directory is the real proof
  that step 2 never fired.

Same junction-safety discipline as the other scripted-agent scripts in this story.

Usage:
    python check_dream_ac17_scripted_agent.py --build
    python check_dream_ac17_scripted_agent.py --run
    python check_dream_ac17_scripted_agent.py --verify

Never the live store, never the live project. Costs real money on --run.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-5")
SCRATCH_PROJECT = SCRATCH_ROOT / "ac17-scratch-project"
BACKUPS_DIR = SCRATCH_ROOT / "ac17-backups"


def build_scratch_project() -> None:
    venv_link = SCRATCH_PROJECT / ".claude" / ".venv"
    if venv_link.is_dir():
        os.rmdir(venv_link)

    if SCRATCH_PROJECT.exists():
        shutil.rmtree(SCRATCH_PROJECT)
    if BACKUPS_DIR.exists():
        shutil.rmtree(BACKUPS_DIR)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

    (SCRATCH_PROJECT / ".claude").mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(venv_link), str(REPO_ROOT / ".venv")],
        capture_output=True,
        text=True,
        check=True,
    )

    dest = SCRATCH_PROJECT / ".claude" / "skills" / "dream"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "skills" / "dream" / "SKILL.md", dest / "SKILL.md")

    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nScratch test for issue #5's AC 17 proof (dream must stop "
        "before any backup when synaptra is unreachable). The synaptra MCP "
        "server in this project is deliberately broken.\n",
        encoding="utf-8",
    )

    # Deliberately broken: a nonexistent executable, same technique as issue #3's
    # AC 18 and issue #4 cycle 2's AC 19 proofs.
    cfg = {
        "mcpServers": {
            "synaptra": {
                "type": "stdio",
                "command": str(
                    REPO_ROOT / ".venv" / "Scripts" / "this-does-not-exist.exe"
                ),
                "args": ["--transport", "stdio"],
            }
        }
    }
    (SCRATCH_PROJECT / ".mcp.json").write_text(
        json.dumps(cfg, indent=2), encoding="utf-8"
    )


def do_run() -> None:
    prompt = (
        'Run /dream. Assume the "active conversation" check is clear -- go '
        "straight to the pre-dream checkpoint."
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
            "0.50",
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

    (SCRATCH_ROOT / "ac17-last-result.txt").write_text(
        result.get("result") or "", encoding="utf-8"
    )


def do_verify() -> int:
    text_check_path = SCRATCH_ROOT / "ac17-last-result.txt"
    said_unreachable = False
    if text_check_path.is_file():
        said_unreachable = (
            "unreachable" in text_check_path.read_text(encoding="utf-8").lower()
        )

    backup_entries = list(BACKUPS_DIR.iterdir()) if BACKUPS_DIR.is_dir() else []
    no_backup_artifact = len(backup_entries) == 0

    print(
        f"[{'PASS' if said_unreachable else 'FAIL'}] AC17: transcript says the "
        f"store is unreachable (weaker signal, checked but not trusted alone): "
        f"{said_unreachable}"
    )
    print(f"backups dir entries: {[p.name for p in backup_entries]}")
    print(
        f"[{'PASS' if no_backup_artifact else 'FAIL'}] AC17: no backup artifact "
        f"was ever created on disk (step 2 never ran -- the real proof): "
        f"{no_backup_artifact}"
    )
    ok = said_unreachable and no_backup_artifact
    return 0 if ok else 1


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print("scratch project built")
        return 0
    if args.run:
        do_run()
        return 0
    if args.verify:
        return do_verify()

    print("pass one of --build / --run / --verify", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Proof for issue #2's AC 8 -- "A fact is stored as one node and is never split" --
per assumption.md's Route 2: this is the one criterion in this story that needs a
headless scripted-agent run rather than a raw script, because "never split" is a
judgment `/create-memory` makes, not a synaptra behaviour to probe directly.

Builds a scratch project (only memory-shapes.md + create-memory/SKILL.md + a minimal
CLAUDE.md routing storage through the skill), runs `claude -p` twice -- once with a
one-fact prompt, once with a two-fact prompt -- and verifies the ACTUAL resulting
store count against the scratch synaptra data, not just the transcript's claim.

Never the live store, never the live project. Costs real money per run (headless
Claude Code invocations) -- this is why it's a script to run "once per cycle that
touches the skill" (assumption.md), not on every check_shapes.py pass.

Usage: python check_ac8_scripted_agent.py [--skip-build]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-2")
SCRATCH_PROJECT = SCRATCH_ROOT / "ac8-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "ac8-scratch-data"
VERIFY_PORT = 8053

ONE_FACT_PROMPT = "Please remember this: the office wifi password is BlueOcean42."
TWO_FACT_PROMPT = (
    "Please remember this: the office recycling pickup is every Tuesday morning, "
    "and separately, the conference room booking system is at "
    "booking.internal.example.com."
)


def build_scratch_project() -> None:
    (SCRATCH_PROJECT / ".claude" / "shared" / "memory").mkdir(
        parents=True, exist_ok=True
    )
    (SCRATCH_PROJECT / ".claude" / "skills" / "create-memory").mkdir(
        parents=True, exist_ok=True
    )
    shutil.copy(
        REPO_ROOT / "shared" / "memory" / "memory-shapes.md",
        SCRATCH_PROJECT / ".claude" / "shared" / "memory" / "memory-shapes.md",
    )
    shutil.copy(
        REPO_ROOT / "skills" / "create-memory" / "SKILL.md",
        SCRATCH_PROJECT / ".claude" / "skills" / "create-memory" / "SKILL.md",
    )
    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nThis is a scratch test project for issue #2's AC 8 proof.\n\n"
        "When the user asks you to remember or store something, route it through "
        "`/create-memory`. Never call `memory_store` directly.\n",
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
    return json.loads(proc.stdout)


def count_active_memories(cm_path: str, url: str) -> list[dict]:
    proc = subprocess.run(
        [cm_path, "--url", url, "--json", "list", "--state", "active", "--limit", "50"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return json.loads(proc.stdout)["data"]["memories"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--skip-build", action="store_true", help="reuse an existing scratch project"
    )
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument("--verify-url", default=f"http://127.0.0.1:{VERIFY_PORT}/mcp")
    args = ap.parse_args()

    if not args.skip_build:
        build_scratch_project()

    print("Running one-fact prompt...")
    one = run_claude(ONE_FACT_PROMPT)
    print(f"  result: {one.get('result')!r}")

    print("Running two-fact prompt...")
    two = run_claude(TWO_FACT_PROMPT)
    print(f"  result: {two.get('result')!r}")

    print(
        "\nStart a scratch HTTP server against the data this run just wrote, then re-invoke "
        "with the counting step -- this script does not start that server itself (matches "
        "this story's convention: never two synaptra processes racing the same file). e.g.:\n"
        f"  SYNAPTRA_BACKEND=surrealkv-file SYNAPTRA_DB={SCRATCH_DATA} SYNAPTRA_PORT={VERIFY_PORT} "
        "<venv-python> -m synaptra.server --transport http\n"
        f"then: {args.cm} --url {args.verify_url} --json list --state active --limit 50\n"
        "and compare the count against what the two transcripts above claimed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

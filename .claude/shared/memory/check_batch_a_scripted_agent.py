#!/usr/bin/env python3
"""Proof for issue #2's Batch A -- AC 5, 11, 17, 20 -- per Velasari's decision
(2026-09-19, over crosschat) to extend AC 8's scripted-agent methodology to the
remaining skill-judgment criteria, batched to control cost. AC 11 folded into this
batch (absent from the original three-group split; a correction scenario is its
natural home, and this batch already tests /update-memory's wrong-vs-incomplete
judgment).

Builds a scratch project carrying memory-shapes.md, create-memory/SKILL.md and
update-memory/SKILL.md, seeds one fact directly (not through the agent -- the seed
isn't under test), then runs three headless `claude -p` scenarios:

  1. AC 5 + AC 20: ask it to remember the same fact, reworded -- expect recall,
     no duplicate created.
  2. AC 17: tell it the fact is now wrong (a URL moved) -- expect an in-place
     rewrite, same id.
  3. AC 11: give it a correction about its OWN behaviour (importance-setting
     habit) -- expect a `learning` constellation, typed `procedural`, instance
     --supports--> procedure.

Verifies every claim against the actual scratch store afterward -- never the
transcript alone. Never the live store, never the live project. Costs real money
per run.

Usage: python check_batch_a_scripted_agent.py [--skip-build]
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
SCRATCH_PROJECT = SCRATCH_ROOT / "batch-a-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "batch-a-scratch-data"
VERIFY_PORT = 8054

SEED_CONTENT = "The deploy runbook lives at wiki.example.com/deploy-old."
SCENARIO_1_PROMPT = "Please remember that our deploy runbook can be found at wiki.example.com/deploy-old."
SCENARIO_2_PROMPT = (
    "Correction: the deploy runbook is NOT at wiki.example.com/deploy-old anymore, "
    "that link is dead. It moved to wiki.example.com/deploy-new."
)
SCENARIO_3_PROMPT = (
    "One thing to correct about how you work: you keep setting importance to 0.9 for "
    "routine, low-stakes facts. Stop doing that - only set importance explicitly when "
    "something is genuinely significant (0.8 or above), otherwise leave it unset and "
    "let the store score it."
)


def build_scratch_project() -> None:
    for skill in ("create-memory", "update-memory"):
        (SCRATCH_PROJECT / ".claude" / "skills" / skill).mkdir(
            parents=True, exist_ok=True
        )
        shutil.copy(
            REPO_ROOT / "skills" / skill / "SKILL.md",
            SCRATCH_PROJECT / ".claude" / "skills" / skill / "SKILL.md",
        )
    (SCRATCH_PROJECT / ".claude" / "shared" / "memory").mkdir(
        parents=True, exist_ok=True
    )
    shutil.copy(
        REPO_ROOT / "shared" / "memory" / "memory-shapes.md",
        SCRATCH_PROJECT / ".claude" / "shared" / "memory" / "memory-shapes.md",
    )
    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nScratch test project for issue #2's Batch A proof "
        "(AC 5, 11, 17, 20). Nothing here is real.\n\nWhen the user asks you to "
        "remember, correct, or update something, route it through `/create-memory` "
        "or `/update-memory` as appropriate. Never call `memory_store` or "
        "`memory_update` directly.\n",
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


def seed(cm_path: str, url: str) -> str:
    proc = subprocess.run(
        [
            cm_path,
            "--url",
            url,
            "--json",
            "store",
            SEED_CONTENT,
            "--type",
            "semantic",
            "--tags",
            "runbook,deploy",
            "--source",
            "seed",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return json.loads(proc.stdout)["data"]["id"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument(
        "--seed-url",
        required=True,
        help="scratch HTTP url to seed through, before the headless runs",
    )
    ap.add_argument("--verify-url", default=f"http://127.0.0.1:{VERIFY_PORT}/mcp")
    args = ap.parse_args()

    if not args.skip_build:
        build_scratch_project()

    seed_id = seed(args.cm, args.seed_url)
    print(
        f"Seeded fact id={seed_id}. Stop the seed server now, then re-run the three "
        f"scenarios below against the same {SCRATCH_DATA} directory (headless "
        f"claude -p opens its own connection)."
    )

    total_cost = 0.0
    for name, prompt in (
        ("Scenario 1 (AC5+AC20)", SCENARIO_1_PROMPT),
        ("Scenario 2 (AC17)", SCENARIO_2_PROMPT),
        ("Scenario 3 (AC11)", SCENARIO_3_PROMPT),
    ):
        print(f"\nRunning {name}...")
        result = run_claude(prompt)
        cost = result.get("total_cost_usd", 0.0)
        total_cost += cost
        print(f"  cost=${cost:.4f}  result: {result.get('result')!r}")

    print(f"\nTotal cost this run: ${total_cost:.4f}")
    print(
        f"\nStart a scratch HTTP server against {SCRATCH_DATA} on port {VERIFY_PORT}, "
        f"then `{args.cm} --url {args.verify_url} --json list --state active --limit 50` "
        "to verify against ground truth -- this script does not start that server "
        "itself (same concurrent-process caution as every other script in this story)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

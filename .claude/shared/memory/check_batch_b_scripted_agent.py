#!/usr/bin/env python3
"""Proof for issue #2's Batch B -- AC 13, AC 15 -- per Velasari's batching decision.

Builds a scratch project carrying memory-shapes.md, create-memory/SKILL.md and
read-memory/SKILL.md, seeds a `learning` constellation directly (instance, bare
procedure, boundary, with instance--supports-->procedure and boundary--part_of-->
procedure edges), then asks a question that should land on it via recall.

Uses --output-format stream-json (not the plain json used by AC 8 and Batch A) because
AC 15 is a claim about ORDER -- "pulls the boundary before the rule is applied" -- and
a final-summary format can't show sequencing. stream-json exposes each tool_use/
tool_result event in order.

AC 13 is cleanly ground-truth-checkable: does the final response name which retrieval
tool it used? AC 15 is NOT clean even with the full trace -- synaptra's memory_recall
returns a ranked bag of results in one call, not one call per node, so there is no
strict "fetch boundary, then fetch rule" tool-call sequence to observe. The best
available evidence is (a) whether the boundary's content appears in the recall
tool_result at all, and (b) whether the response's own final, synthesized conclusion
correctly incorporates the boundary as a qualifier rather than stating the rule as
unconditional. Both are printed for a human (or a future cycle) to read, not
auto-scored -- forcing a PASS/FAIL out of genuinely ambiguous evidence would be less
honest than showing the evidence.

Never the live store, never the live project. Costs real money per run.

Usage: python check_batch_b_scripted_agent.py [--skip-build]
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
SCRATCH_PROJECT = SCRATCH_ROOT / "batch-b-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "batch-b-scratch-data"
VERIFY_PORT = 8055

INSTANCE_CONTENT = (
    "We deployed on a Friday afternoon without a tested rollback plan ready. "
    "The release broke, and nobody was around to fix it until Monday."
)
PROCEDURE_CONTENT = (
    "Don't deploy on Friday afternoon without a tested rollback plan ready."
)
BOUNDARY_CONTENT = (
    "This does not apply to small, easily-revertible config-only changes - those are "
    "safe to deploy any time, including Friday."
)
QUESTION_PROMPT = "What's the rule about deploying on Fridays?"


def build_scratch_project() -> None:
    for skill in ("create-memory", "read-memory"):
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
        "# CLAUDE.md\n\nScratch test project for issue #2's Batch B proof "
        "(AC 13, 15). Nothing here is real.\n\nWhen the user asks a question that "
        "touches something previously stored, route it through `/read-memory` rather "
        "than guessing or answering from general knowledge.\n",
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


def cm(cm_path: str, url: str, *args: str) -> dict:
    proc = subprocess.run(
        [cm_path, "--url", url, "--json", *args],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return json.loads(proc.stdout)


def seed_constellation(cm_path: str, url: str) -> None:
    inst = cm(
        cm_path,
        url,
        "store",
        INSTANCE_CONTENT,
        "--type",
        "procedural",
        "--tags",
        "deploy,friday,incident",
        "--source",
        "seed",
    )["data"]["id"]
    proc = cm(
        cm_path,
        url,
        "store",
        PROCEDURE_CONTENT,
        "--type",
        "procedural",
        "--tags",
        "deploy,friday,rule",
        "--source",
        "seed",
    )["data"]["id"]
    bound = cm(
        cm_path,
        url,
        "store",
        BOUNDARY_CONTENT,
        "--type",
        "procedural",
        "--tags",
        "deploy,friday,boundary",
        "--source",
        "seed",
    )["data"]["id"]
    cm(cm_path, url, "relate", inst, proc, "--type", "supports")
    cm(cm_path, url, "relate", bound, proc, "--type", "part_of")


def run_claude_stream(prompt: str) -> list[dict]:
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
            "stream-json",
            "--verbose",
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
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument(
        "--seed-url", required=True, help="scratch HTTP url to seed through"
    )
    args = ap.parse_args()

    if not args.skip_build:
        build_scratch_project()

    seed_constellation(args.cm, args.seed_url)
    print(
        f"Seeded the constellation. Stop the seed server now, then this script's "
        f"headless run will open its own connection to {SCRATCH_DATA}."
    )

    events = run_claude_stream(QUESTION_PROMPT)

    tool_calls = []
    final_text = None
    cost = None
    for ev in events:
        if ev.get("type") == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls.append((block["name"], block.get("input")))
        if ev.get("type") == "result":
            final_text = ev.get("result")
            cost = ev.get("total_cost_usd")

    print("\n--- Tool calls, in order ---")
    for name, inp in tool_calls:
        print(f"  {name}  {json.dumps(inp)[:150]}")

    print(f"\n--- Final response ---\n{final_text}")

    ac13_ok = final_text is not None and any(
        tool in (final_text or "")
        for tool in ("memory_recall", "memory_list", "memory_get", "memory_related")
    )
    print(f"\n[AC13] names the retrieval tool used in its own response: {ac13_ok}")
    print(
        "[AC15] NOT auto-scored -- read the tool calls and final response above. "
        "Check: did the boundary's content appear in a recall/related result, and does "
        "the response's own final synthesized takeaway correctly qualify the rule with "
        "the boundary, rather than stating it as unconditional?"
    )
    print(f"\nCost: ${cost}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

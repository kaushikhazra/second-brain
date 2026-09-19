#!/usr/bin/env python3
"""Proof for issue #2's Batch C -- AC 16, AC 21, AC 22 -- per Velasari's batching
decision. Builds a scratch project carrying memory-shapes.md, create-memory,
update-memory and delete-memory, seeds data directly, runs four headless scenarios
(AC 21 needed two attempts -- see below), verifies against ground truth.

Scenario 1 (AC 16): a purely cosmetic edit request on an ordinary fact. Expect
refusal, with a stated reason, and zero writes (verify updated_at == created_at
afterward).

Scenario 2 (AC 22): ask to delete just the procedure node of a seeded learning
constellation, leaving the instance and boundary. Expect refusal or at minimum no
unilateral deletion. NOTE, recorded honestly rather than auto-passed: the one real
run of this scenario refused to act, correctly flagged the boundary would be
orphaned, but ALSO (a) mischaracterized the instance as "safe either way" to leave
behind (the shapes file says the opposite -- an instance with no procedure is "a
story with no point"), and (b) offered the user an option that, if accepted, would
still produce the exact orphaned state AC 22 forbids. The follow-up ("yes, do that
anyway") was never tested. This script does not auto-score AC 22 -- print the
transcript and the ground-truth store state, let a human read both.

Scenario 3 (AC 21, first attempt): "the build server was upgraded from 16GB to
32GB" -- ambiguous framing that the agent (defensibly) read as a plain fact
correction (update in place, per the shapes file's fact-update rule), not a
supersession. Included for the record; does not exercise the archive path.

Scenario 4 (AC 21, second attempt): "we took a NEW reading; keep the OLD one for
history" -- unambiguous supersession framing. This is the one that actually proves
the archive-by-default half: expect a new fact stored, a `supersedes` edge, and the
old fact ARCHIVED (not deleted, still retrievable).

Scenario 5 (AC 21, never-true half): a fact that was wrong from the start. Expect
permanent deletion, with the reason stated (never true, not superseded).

Never the live store, never the live project. Costs real money per run.

Usage: python check_batch_c_scripted_agent.py [--skip-build]
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
SCRATCH_PROJECT = SCRATCH_ROOT / "batch-c-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "batch-c-scratch-data"

TIDY_FACT = "The team standup is at 9:30am."
LEARNING_INSTANCE = "We merged a PR without running the full test suite once, and it broke the build for two days."
LEARNING_PROCEDURE = "Always run the full test suite before merging a PR."
LEARNING_BOUNDARY = (
    "This does not apply to documentation-only PRs with no code changes."
)
NEVER_TRUE_FACT = "The office is located in Building C."
OLD_READING = "Server room temperature reading (2026-08-01): 19C."

SCENARIO_1_PROMPT = (
    "Can you go tidy up the wording on the standup memory? It's a bit awkward, just "
    "polish the phrasing, nothing about the actual meaning needs to change."
)
SCENARIO_2_PROMPT = (
    "Please delete just the rule memory about always running the full test suite "
    "before merging a PR - the one that says the bare rule, not the story about it "
    "breaking the build. Just that one node."
)
SCENARIO_4_PROMPT = (
    "We just took a fresh server room temperature reading: 22C today. The old reading "
    "(19C from 2026-08-01) is now out of date, but I don't want it just deleted - it's "
    "useful history for our thermal logs. Please handle it appropriately."
)
SCENARIO_5_PROMPT = (
    "I just found out the office was never actually in Building C - that was wrong "
    "from the start, someone misread the lease. Please sort it out."
)


def build_scratch_project() -> None:
    for skill in ("create-memory", "update-memory", "delete-memory"):
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
        "# CLAUDE.md\n\nScratch test project for issue #2's Batch C proof "
        "(AC 16, 21, 22). Nothing here is real.\n\nWhen the user asks to change, "
        "tidy, archive, or delete something, route it through `/update-memory` or "
        "`/delete-memory` as appropriate. Never call `memory_update`, "
        "`memory_archive`, or `memory_delete` directly.\n",
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


def seed(cm_path: str, url: str) -> dict[str, str]:
    ids = {}
    ids["tidy"] = cm(
        cm_path,
        url,
        "store",
        TIDY_FACT,
        "--type",
        "semantic",
        "--tags",
        "standup,schedule",
        "--source",
        "seed",
    )["data"]["id"]
    ids["instance"] = cm(
        cm_path,
        url,
        "store",
        LEARNING_INSTANCE,
        "--type",
        "procedural",
        "--tags",
        "code-review,testing,incident",
        "--source",
        "seed",
    )["data"]["id"]
    ids["procedure"] = cm(
        cm_path,
        url,
        "store",
        LEARNING_PROCEDURE,
        "--type",
        "procedural",
        "--tags",
        "code-review,testing,rule",
        "--source",
        "seed",
    )["data"]["id"]
    ids["boundary"] = cm(
        cm_path,
        url,
        "store",
        LEARNING_BOUNDARY,
        "--type",
        "procedural",
        "--tags",
        "code-review,testing,boundary",
        "--source",
        "seed",
    )["data"]["id"]
    cm(cm_path, url, "relate", ids["instance"], ids["procedure"], "--type", "supports")
    cm(cm_path, url, "relate", ids["boundary"], ids["procedure"], "--type", "part_of")
    ids["never_true"] = cm(
        cm_path,
        url,
        "store",
        NEVER_TRUE_FACT,
        "--type",
        "semantic",
        "--tags",
        "office,location",
        "--source",
        "seed",
    )["data"]["id"]
    ids["old_reading"] = cm(
        cm_path,
        url,
        "store",
        OLD_READING,
        "--type",
        "semantic",
        "--tags",
        "infra,temperature-log",
        "--source",
        "seed",
    )["data"]["id"]
    return ids


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument("--seed-url", required=True)
    args = ap.parse_args()

    if not args.skip_build:
        build_scratch_project()

    ids = seed(args.cm, args.seed_url)
    print(f"Seeded: {ids}")
    print("Stop the seed server now before running the headless scenarios below.\n")

    total_cost = 0.0
    for name, prompt in (
        ("Scenario 1 (AC16)", SCENARIO_1_PROMPT),
        ("Scenario 2 (AC22)", SCENARIO_2_PROMPT),
        ("Scenario 4 (AC21 archive path)", SCENARIO_4_PROMPT),
        ("Scenario 5 (AC21 delete path)", SCENARIO_5_PROMPT),
    ):
        print(f"Running {name}...")
        result = run_claude(prompt)
        cost = result.get("total_cost_usd", 0.0)
        total_cost += cost
        print(f"  cost=${cost:.4f}  result: {result.get('result')!r}\n")

    print(f"Total cost this run: ${total_cost:.4f}")
    print(
        f"Verify against ground truth: start a scratch HTTP server against "
        f"{SCRATCH_DATA}, then `cm get`/`cm list` each seeded id (`{ids}`) and "
        "compare against what each scenario's result claimed. AC22 needs a human "
        "read of the transcript and the store state together -- not auto-scored here."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

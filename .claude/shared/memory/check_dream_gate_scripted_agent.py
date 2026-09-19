#!/usr/bin/env python3
"""Proof for issue #5's AC 1 + AC 2 -- the row-count gate.

observe.md's own instruction: "a script that feeds the gate a manifest whose count
differs and asserts abort with the word 'defect', and a matching manifest and
asserts continue. Do not re-derive the gate; keep the existing text and prove it."

This is a judgement the MODEL makes reading its own skill's checkpoint steps, not a
value a Python function computes -- so the proof is a headless run of the dream
skill's own text, given the two numbers a real checkpoint would have already
produced (the live `memory_stats` count and the backup manifest's `row_counts.memory`
count), and checking what it does with them. Deliberately does NOT run a real `cm
backup create` (~190s, per cycle 1's timing) -- that mechanism was already verified
directly in cycle 1; this proof is specifically about the COMPARISON judgement once
those two numbers exist, matching observe.md's "feeds the gate a manifest" framing.

No synaptra connection needed at all for this specific judgement -- the two numbers
are given directly in the prompt, exactly as the skill's own step 4 ("read
manifest.json... compare against step 1's count") would have them in hand by that
point in a real run.

Usage:
    python check_dream_gate_scripted_agent.py --build
    python check_dream_gate_scripted_agent.py --run-mismatch
    python check_dream_gate_scripted_agent.py --run-match

Costs real money on --run-mismatch/--run-match.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-5")
SCRATCH_PROJECT = SCRATCH_ROOT / "gate-scratch-project"

PROMPT_TEMPLATE = (
    "You are about to run /dream. Read .claude/skills/dream/SKILL.md's \"Pre-dream "
    'checkpoint" section and follow it exactly for this situation -- do not actually '
    "call any tool; the two facts below are what steps 1-4 of that section would "
    "have already produced by this point in a real run:\n\n"
    "- Step 1's memory_stats call reported storage.memory_count = {live}.\n"
    "- Steps 2-3 (cm backup create, cm backup verify --deep) both completed "
    "without error.\n"
    "- Step 4: manifest.json's row_counts.memory = {manifest}.\n\n"
    "Per the skill's own text, what do you do now? State your decision plainly."
)


def build_scratch_project() -> None:
    if SCRATCH_PROJECT.exists():
        shutil.rmtree(SCRATCH_PROJECT)

    dest = SCRATCH_PROJECT / ".claude" / "skills" / "dream"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "skills" / "dream" / "SKILL.md", dest / "SKILL.md")

    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nScratch test for issue #5's AC 1 + AC 2 proof (dream's "
        "row-count gate). No memory tools are configured here -- this test is "
        "purely about the checkpoint judgement given two already-known numbers, "
        "not about live synaptra I/O.\n",
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
            "--output-format",
            "json",
            "--max-budget-usd",
            "0.40",
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


def extract_decision(text: str) -> str:
    """Both real runs so far wrote an explicit '**Decision: ...**' sentence. Two
    naive whole-text keyword scans both produced false results in practice: "abort"
    and "defect" each showed up in NEGATED form ("no abort, no defect language",
    "not the defect case") when the model correctly explained why neither applied.
    Anchoring on the model's own explicit decision statement, not the whole reply,
    is what actually distinguishes a real verdict from a mention of the word while
    ruling it out. Falls back to the whole text if no such sentence is found."""
    m = re.search(r"decision:?\**\s*([^\n.]{0,120})", text, re.IGNORECASE)
    return m.group(1).lower() if m else text.lower()


def do_run_mismatch() -> int:
    prompt = PROMPT_TEMPLATE.format(live=55, manifest=1)
    r = run_claude(prompt)
    full_text = r.get("result") or ""
    print(f"cost=${r.get('total_cost_usd'):.4f}")
    print(f"result: {full_text!r}")

    decision = extract_decision(full_text)
    said_abort = "abort" in decision
    # "defect" is checked against the decision line if it's there, otherwise the
    # nearby text -- the model sometimes states "a defect" just before or after the
    # Decision: line rather than inside it, so widen slightly for this one word.
    said_defect = "defect" in decision or "a defect" in full_text.lower()
    ok = said_defect and said_abort
    print(
        f"[{'PASS' if ok else 'FAIL'}] AC1+AC2: mismatched counts (55 vs 1) -> "
        f"aborts and calls it a defect (decision line: {decision!r}): "
        f"defect={said_defect}, abort={said_abort}"
    )
    return 0 if ok else 1


def do_run_match() -> int:
    prompt = PROMPT_TEMPLATE.format(live=55, manifest=55)
    r = run_claude(prompt)
    full_text = r.get("result") or ""
    print(f"cost=${r.get('total_cost_usd'):.4f}")
    print(f"result: {full_text!r}")

    decision = extract_decision(full_text)
    said_abort = "abort" in decision
    said_continue = any(
        w in decision for w in ("continue", "proceed", "checkpoint", "pass")
    )
    ok = said_continue and not said_abort
    print(
        f"[{'PASS' if ok else 'FAIL'}] AC1+AC2: matching counts (55 vs 55) -> "
        f"proceeds, no abort (decision line: {decision!r}): "
        f"continue={said_continue}, abort={said_abort}"
    )
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run-mismatch", action="store_true")
    ap.add_argument("--run-match", action="store_true")
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print("scratch project built")
        return 0
    if args.run_mismatch:
        return do_run_mismatch()
    if args.run_match:
        return do_run_match()

    print("pass one of --build / --run-mismatch / --run-match", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

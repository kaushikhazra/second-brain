#!/usr/bin/env python3
"""Proof for issue #5's AC 1 + AC 2 (the row-count gate) and AC 3 (a non-zero
command exit).

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
    python check_dream_gate_scripted_agent.py --run-nonzero-exit

Costs real money on --run-mismatch/--run-match/--run-nonzero-exit.
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

BACKUP_PATH = (
    "C:/Projects/.tmp/second-brain-loop-5/gate-proof-backups/cm-20260919T170000Z"
)
BRAIN_DB_PATH = "C:/scratch-brain/.claude/synaptra-data"

PROMPT_TEMPLATE = (
    "You are about to run /dream. Read .claude/skills/dream/SKILL.md's \"Pre-dream "
    'checkpoint" section and follow it exactly for this situation -- do not actually '
    "call any tool; the facts below are what steps 1-4 of that section would "
    "have already produced by this point in a real run:\n\n"
    "- Step 1's memory_stats call reported storage.memory_count = {live}.\n"
    f"- Step 2 (cm backup create) completed without error, backup path: {BACKUP_PATH}\n"
    "- Step 3 (cm backup verify --deep) completed without error.\n"
    "- Step 4: manifest.json's row_counts.memory = {manifest}.\n"
    f"- This brain's SYNAPTRA_DB path (from .mcp.json) is: {BRAIN_DB_PATH}\n\n"
    "Per the skill's own text, what do you do now? State your decision plainly, "
    "and if you proceed, state exactly what you would tell the owner."
)

NONZERO_EXIT_PROMPT_TEMPLATE = (
    "You are about to run /dream. Read .claude/skills/dream/SKILL.md's \"Pre-dream "
    'checkpoint" section and follow it exactly for this situation -- do not actually '
    "call any tool; the facts below are what steps 1-3 of that section would have "
    "already produced by this point in a real run:\n\n"
    "- Step 1's memory_stats call reported storage.memory_count = {live}.\n"
    "- Step 2 (cm backup create) completed without error.\n"
    "- Step 3 (cm backup verify --deep) exited non-zero with this output:\n"
    '  "{error_text}"\n\n'
    "Per the skill's own text, what do you do now? State your decision plainly, "
    "and include the command's own error output in your answer."
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


def mentions_affirmatively(word: str, text: str) -> bool:
    """True iff `word` appears somewhere NOT immediately preceded by a negation
    ("no abort", "not a defect", "isn't the X case", "no ... language"). A model
    correctly explaining why a failure mode does NOT apply legitimately uses the
    word while negating it -- caught as a false result twice already (once for
    "defect" in the mismatch/match scenarios, once for "abort" in this cycle's
    AC 4 run when no explicit 'Decision:' line existed and the fallback whole-text
    scan hit the same trap). One shared, negation-aware check from here on,
    instead of re-deriving a narrower fix per word per scenario."""
    for m in re.finditer(re.escape(word), text, re.IGNORECASE):
        preceding = text[max(0, m.start() - 15) : m.start()]
        if re.search(r"\b(no|not|n't|isn't|neither)\s*$", preceding, re.IGNORECASE):
            continue
        return True
    return False


def do_run_mismatch() -> int:
    prompt = PROMPT_TEMPLATE.format(live=55, manifest=1)
    r = run_claude(prompt)
    full_text = r.get("result") or ""
    print(f"cost=${r.get('total_cost_usd'):.4f}")
    print(f"result: {full_text!r}")

    said_abort = mentions_affirmatively("abort", full_text)
    said_defect = mentions_affirmatively("defect", full_text)
    ok = said_defect and said_abort
    print(
        f"[{'PASS' if ok else 'FAIL'}] AC1+AC2: mismatched counts (55 vs 1) -> "
        f"aborts and calls it a defect: defect={said_defect}, abort={said_abort}"
    )
    return 0 if ok else 1


def do_run_match() -> int:
    prompt = PROMPT_TEMPLATE.format(live=55, manifest=55)
    r = run_claude(prompt)
    full_text = r.get("result") or ""
    print(f"cost=${r.get('total_cost_usd'):.4f}")
    print(f"result: {full_text!r}")

    said_abort = mentions_affirmatively("abort", full_text)
    said_continue = any(
        mentions_affirmatively(w, full_text)
        for w in ("continue", "proceed", "checkpoint at")
    )
    ok12 = said_continue and not said_abort
    print(
        f"[{'PASS' if ok12 else 'FAIL'}] AC1+AC2: matching counts (55 vs 55) -> "
        f"proceeds, no abort: continue={said_continue}, abort={said_abort}"
    )

    # AC 4: path, count, AND the rollback command, all three, said to the owner
    # before any reshaping.
    lower = full_text.lower()
    said_path = BACKUP_PATH.lower() in lower
    said_count = "55" in full_text
    said_restore_cmd = "cm backup restore" in lower and "--target" in lower
    ok4 = said_path and said_count and said_restore_cmd
    print(
        f"[{'PASS' if ok4 else 'FAIL'}] AC4: checkpoint report states path, count, "
        f"and the rollback command: path={said_path}, count={said_count}, "
        f"restore_cmd={said_restore_cmd}"
    )

    return 0 if (ok12 and ok4) else 1


ERROR_TEXT = "Error: manifest checksum mismatch, exit 1"


def do_run_nonzero_exit() -> int:
    prompt = NONZERO_EXIT_PROMPT_TEMPLATE.format(live=55, error_text=ERROR_TEXT)
    r = run_claude(prompt)
    full_text = r.get("result") or ""
    print(f"cost=${r.get('total_cost_usd'):.4f}")
    print(f"result: {full_text!r}")

    said_abort = mentions_affirmatively("abort", full_text)
    # AC 3: "with the command's own error shown" -- the exact string, not a
    # paraphrase or summary of it.
    showed_exact_error = ERROR_TEXT in full_text
    ok = said_abort and showed_exact_error
    print(
        f"[{'PASS' if ok else 'FAIL'}] AC3: non-zero verify exit -> aborts and "
        f"shows the command's own error verbatim: abort={said_abort}, "
        f"showed_exact_error={showed_exact_error}"
    )
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run-mismatch", action="store_true")
    ap.add_argument("--run-match", action="store_true")
    ap.add_argument("--run-nonzero-exit", action="store_true")
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print("scratch project built")
        return 0
    if args.run_mismatch:
        return do_run_mismatch()
    if args.run_match:
        return do_run_match()
    if args.run_nonzero_exit:
        return do_run_nonzero_exit()

    print(
        "pass one of --build / --run-mismatch / --run-match / --run-nonzero-exit",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())

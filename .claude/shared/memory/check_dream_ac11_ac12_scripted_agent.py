#!/usr/bin/env python3
"""Proof for issue #5's AC 11 + AC 12.

AC 11: "The dream reports counts before and after: active, archived, retyped,
relations added."
AC 12: "The dream reports any memory it wanted to change and could not, by id,
with the reason."

Same technique as the AC 1/2/3 gate proofs: rather than running all six acts live
(expensive, slow, and Acts 1-4's own judgement is proven separately elsewhere),
give the model the established facts Acts 1-4 would have already produced by the
time Act 5 runs, and check what it reports. This tests Act 5's OWN reporting
discipline specifically, not Acts 1-4's judgement (already covered: AC 7/8's
archive rule, AC 9's retype mechanism, AC 10's relate rule are each proven by
their own scripts).

No synaptra connection needed -- purely a reporting-discipline judgement given
already-known facts, same shape as the gate proofs.

Usage:
    python check_dream_ac11_ac12_scripted_agent.py --build
    python check_dream_ac11_ac12_scripted_agent.py --run

Costs real money on --run.
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
SCRATCH_PROJECT = SCRATCH_ROOT / "ac11-ac12-scratch-project"

PROMPT = (
    "You are running /dream. Read .claude/skills/dream/SKILL.md's Act 5 (\"Seal "
    'the dream") and follow it exactly. Do not call any tool. Acts 1-4 have '
    "already happened; here is exactly what they produced:\n\n"
    "- Before this dream: 55 active memories.\n"
    "- Act 2 archived 3 memories: ids AAAA1111-1111-1111-1111-111111111111, "
    "BBBB2222-2222-2222-2222-222222222222, CCCC3333-3333-3333-3333-333333333333.\n"
    "- Act 2 retyped 2 memories: ids DDDD4444-4444-4444-4444-444444444444 (working "
    "-> episodic), EEEE5555-5555-5555-5555-555555555555 (episodic -> procedural).\n"
    "- Act 4 added 5 relations.\n"
    "- Act 4 attempted one relation that was NOT made: tried to relate "
    "FFFF6666-6666-6666-6666-666666666666 to GGGG7777-7777-7777-7777-777777777777, "
    "but GGGG7777... is archived (not active), so per AC 10 the link was skipped.\n"
    "- Act 2 also considered archiving HHHH8888-8888-8888-8888-888888888888 (looked "
    "stale, retrievability 0.1), but that id is the surface-map holder -- "
    "memory_guard.py refused the call.\n\n"
    "Now perform Act 5's reporting step. What exactly do you report to the owner?"
)


def build_scratch_project() -> None:
    if SCRATCH_PROJECT.exists():
        shutil.rmtree(SCRATCH_PROJECT)

    dest = SCRATCH_PROJECT / ".claude" / "skills" / "dream"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "skills" / "dream" / "SKILL.md", dest / "SKILL.md")

    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nScratch test for issue #5's AC 11 + AC 12 proof (dream's "
        "Act 5 reporting discipline). No memory tools are configured here -- this "
        "test is purely about what Act 5 reports given already-known facts.\n",
        encoding="utf-8",
    )


def do_run() -> int:
    proc = subprocess.run(
        [
            "claude",
            "-p",
            PROMPT,
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
    result = json.loads(proc.stdout)
    full_text = result.get("result") or ""
    print(f"cost=${result.get('total_cost_usd'):.4f}")
    print(f"result: {full_text!r}")

    # AC 11: all four counts, as numbers, present somewhere in the report.
    has_active = bool(re.search(r"\b52\b", full_text))  # 55 - 3 archived = 52
    has_archived = bool(
        re.search(
            r"\barchived\b.{0,15}\b3\b|\b3\b.{0,15}archived", full_text, re.IGNORECASE
        )
    )
    has_retyped = bool(
        re.search(
            r"\bretyped\b.{0,15}\b2\b|\b2\b.{0,15}retyped", full_text, re.IGNORECASE
        )
    )
    has_relations = bool(
        re.search(
            r"\brelations?\b.{0,20}\b5\b|\b5\b.{0,20}relations?",
            full_text,
            re.IGNORECASE,
        )
    )
    ok11 = has_active and has_archived and has_retyped and has_relations
    print(
        f"[{'PASS' if ok11 else 'FAIL'}] AC11: reports all four counts "
        f"(active=52, archived=3, retyped=2, relations=5): "
        f"active={has_active}, archived={has_archived}, retyped={has_retyped}, relations={has_relations}"
    )

    # AC 12: both blocked changes named by id, with the reason.
    named_skipped_relation = "GGGG7777" in full_text and (
        "not active" in full_text.lower() or "archived" in full_text.lower()
    )
    named_blocked_archive = "HHHH8888" in full_text and (
        "surface-map" in full_text.lower() or "protected" in full_text.lower()
    )
    ok12 = named_skipped_relation and named_blocked_archive
    print(
        f"[{'PASS' if ok12 else 'FAIL'}] AC12: both blocked changes reported by id "
        f"with the reason: skipped_relation={named_skipped_relation}, "
        f"blocked_archive={named_blocked_archive}"
    )

    return 0 if (ok11 and ok12) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print("scratch project built")
        return 0
    if args.run:
        return do_run()

    print("pass one of --build / --run", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

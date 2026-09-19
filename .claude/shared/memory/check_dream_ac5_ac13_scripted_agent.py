#!/usr/bin/env python3
"""Proof for issue #5's AC 5 + AC 13 -- the heartbeat cron deleted before
reshaping and recreated after, both CONFIRMED with their own `CronList` read-back.

Crons are strictly session-scoped ("Jobs live only in this Claude session --
nothing is written to disk, and the job is gone when Claude exits", per
CronCreate's own tool description) -- there is no way to check "is the cron
running again" from OUTSIDE a scripted-agent's session after that session's
`claude -p` process has already exited, because the cron itself would already be
gone regardless of whether the dream behaved correctly. So this proof captures
the ACTUAL tool-call sequence DURING the run via `--output-format stream-json`,
not a check performed after the session ends.

The scenario: one ephemeral session first simulates what `/session-start` would
have already done (create a heartbeat cron), then runs the dream's Prerequisites
step 1 and Act 6 exactly as written (skipping the checkpoint and Acts 1-5 --
those are proven separately elsewhere; this is specifically about the
delete-confirm-recreate-confirm cron sequence). The full tool trace is parsed
afterward to assert the actual call order: CronList, CronDelete, CronList (proving
the delete), CronCreate, CronList (proving the recreate) -- not the model's prose
claim that it did these things.

Usage:
    python check_dream_ac5_ac13_scripted_agent.py --build
    python check_dream_ac5_ac13_scripted_agent.py --run

Costs real money on --run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-5")
SCRATCH_PROJECT = SCRATCH_ROOT / "ac5-ac13-scratch-project"
STREAM_FILE = SCRATCH_ROOT / "ac5-ac13-stream.jsonl"

PROMPT = (
    "This is a two-part scripted test, in ONE session.\n\n"
    "Part A: simulate that /session-start already ran and created the heartbeat "
    'cron. Call CronCreate yourself now with schedule="*/30 * * * *" and '
    "prompt='Run /heartbeat \"requested by cron\"'.\n\n"
    "Part B: now run /dream. Skip the pre-dream checkpoint and Acts 1-5 entirely "
    "-- assume they already completed successfully (those are proven by other "
    'tests). Follow ONLY the skill\'s "Prerequisites" step 1 (disable the '
    'heartbeat cron, confirmed) and "Act 6 -- Restart the heartbeat" (recreate '
    "it, confirmed) exactly as .claude/skills/dream/SKILL.md states them, in "
    "that order, with nothing in between. Actually make the real tool calls each "
    "step asks for -- don't just describe what you would do."
)


def build_scratch_project() -> None:
    if SCRATCH_PROJECT.exists():
        shutil.rmtree(SCRATCH_PROJECT)

    dest = SCRATCH_PROJECT / ".claude" / "skills" / "dream"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "skills" / "dream" / "SKILL.md", dest / "SKILL.md")

    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nScratch test for issue #5's AC 5 + AC 13 proof (the "
        "dream's cron delete-confirm-recreate-confirm sequence). No memory tools "
        "are configured here -- this test is purely about the cron sequence.\n",
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
            "stream-json",
            "--verbose",
            "--max-budget-usd",
            "0.60",
            "--no-session-persistence",
        ],
        cwd=str(SCRATCH_PROJECT),
        capture_output=True,
        text=True,
        timeout=200,
    )
    STREAM_FILE.write_text(proc.stdout, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()[:500]}"
        )

    calls: list[tuple[str, dict]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "tool_use" and block.get("name") in (
                    "CronList",
                    "CronCreate",
                    "CronDelete",
                ):
                    calls.append((block["name"], block.get("input", {})))

    print(f"tool calls in order: {[c[0] for c in calls]}")

    names = [c[0] for c in calls]
    # Expected shape: CronCreate (Part A's simulated session-start), then
    # CronList, CronDelete, CronList (Prerequisites, confirmed), then
    # CronCreate, CronList (Act 6, confirmed).
    ok_sequence = (
        names.count("CronList") >= 2
        and names.count("CronDelete") >= 1
        and names.count("CronCreate") >= 2
    )
    # The delete must be followed somewhere later by a CronList (confirm), and
    # the LAST CronCreate must be followed by a CronList (confirm) too.
    delete_idx = names.index("CronDelete") if "CronDelete" in names else -1
    confirmed_delete = delete_idx != -1 and "CronList" in names[delete_idx + 1 :]
    last_create_idx = (
        len(names) - 1 - names[::-1].index("CronCreate")
        if "CronCreate" in names
        else -1
    )
    confirmed_recreate = (
        last_create_idx != -1 and "CronList" in names[last_create_idx + 1 :]
    )

    ok = ok_sequence and confirmed_delete and confirmed_recreate
    print(
        f"[{'PASS' if ok else 'FAIL'}] AC5+AC13: delete confirmed with a CronList, "
        f"recreate confirmed with a CronList: sequence_ok={ok_sequence}, "
        f"confirmed_delete={confirmed_delete}, confirmed_recreate={confirmed_recreate}"
    )
    return 0 if ok else 1


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

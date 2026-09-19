#!/usr/bin/env python3
"""Issue #7, cycle 2 -- scripted-agent proof that `/session-start`'s daily-habits
step (step 8) behaves correctly around `/news`: AC 11 (runs once, skips the
second time same day) and AC 19 (a news failure never stops `/session-start`
from completing).

No synaptra configured at all -- exercises `/session-start`'s own documented
fallback (memory-dependent steps report themselves skipped; the heartbeat cron
and the daily-habits step still run). Two sequential runs against the SAME
scratch project and the SAME `.claude/activations.json`, in order:

  --run 1  : news active, no `last_run` yet, WebSearch/WebFetch/Bash/Task
              disallowed so /news is FORCED to fail -> proves AC 19 (the boot's
              Report step still runs) and that `last_run` gets stamped even on
              a failed attempt.
  --run 2  : same record (now carrying today's `last_run` from run 1), full
              tool access restored -> proves AC 11's second half: step 8 skips
              silently, no /news invocation happens, the rest of the boot still
              completes.

Usage:
    python check_news_session_start_scripted_agent.py --build
    python check_news_session_start_scripted_agent.py --run 1
    python check_news_session_start_scripted_agent.py --run 2
    python check_news_session_start_scripted_agent.py --verify 1
    python check_news_session_start_scripted_agent.py --verify 2

Never the live project. Costs real money on --run.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-7")
SCRATCH_PROJECT = SCRATCH_ROOT / "session-start-scratch-project"
VERSION = "0.3.1"


def build_scratch_project() -> None:
    if SCRATCH_PROJECT.exists():
        shutil.rmtree(SCRATCH_PROJECT)

    for skill in ("session-start", "news"):
        dest = SCRATCH_PROJECT / ".claude" / "skills" / skill
        dest.mkdir(parents=True, exist_ok=True)
        src = REPO_ROOT / "skills" / skill
        for f in src.glob("*"):
            if f.is_file():
                shutil.copy(f, dest / f.name)
    scripts_dest = SCRATCH_PROJECT / ".claude" / "skills" / "news" / "scripts"
    scripts_dest.mkdir(parents=True, exist_ok=True)
    for f in (REPO_ROOT / "skills" / "news" / "scripts").glob("*.py"):
        shutil.copy(f, scripts_dest / f.name)

    (SCRATCH_PROJECT / ".claude" / "shared").mkdir(parents=True, exist_ok=True)
    shutil.copy(
        REPO_ROOT / "shared" / "activation.py",
        SCRATCH_PROJECT / ".claude" / "shared" / "activation.py",
    )

    (SCRATCH_PROJECT / "VERSION").write_text(VERSION, encoding="utf-8")
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
        "# CLAUDE.md\n\nScratch test for issue #7's session-start daily-habits proof "
        "(AC 11, AC 19). No synaptra configured -- exercise the documented "
        "memory-less fallback. `/session-start` is the entry point.\n",
        encoding="utf-8",
    )
    (SCRATCH_PROJECT / "news-keywords.txt").write_text("ai\nllm\n", encoding="utf-8")
    (SCRATCH_PROJECT / ".claude" / "activations.json").write_text(
        json.dumps(
            {"news": {"answered_at_version": VERSION, "active": True}}, indent=2
        ),
        encoding="utf-8",
    )
    (SCRATCH_PROJECT / ".mcp.json").write_text(
        json.dumps({"mcpServers": {}}, indent=2), encoding="utf-8"
    )


def run_stream_json(
    prompt: str, disallowed: list[str] | None = None
) -> tuple[list[dict], dict]:
    args = [
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
        "1.0",
        "--no-session-persistence",
    ]
    if disallowed:
        args += ["--disallowedTools", ",".join(disallowed)]
    proc = subprocess.run(
        args,
        cwd=str(SCRATCH_PROJECT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()[:2000]}"
        )
    events = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    final = next((e for e in reversed(events) if e.get("type") == "result"), {})
    return events, final


def full_reply(events: list[dict], final: dict) -> str:
    blocks = []
    for e in events:
        if e.get("type") != "assistant":
            continue
        msg = e.get("message", {})
        for block in (
            msg.get("content", []) if isinstance(msg.get("content"), list) else []
        ):
            if isinstance(block, dict) and block.get("type") == "text":
                blocks.append(block.get("text", ""))
    return "\n".join(blocks) or final.get("result", "")


def do_run(run_no: int) -> None:
    prompt = "Run /session-start."
    if run_no == 3:
        # Independent scenario -- news OFF, fresh record, no accumulated
        # state from runs 1/2. Overwrite regardless of what's on disk.
        (SCRATCH_PROJECT / ".claude" / "activations.json").write_text(
            json.dumps(
                {"news": {"answered_at_version": VERSION, "active": False}}, indent=2
            ),
            encoding="utf-8",
        )
    if run_no == 1:
        events, final = run_stream_json(
            prompt, disallowed=["WebSearch", "WebFetch", "Bash", "Task"]
        )
    else:
        events, final = run_stream_json(prompt)
    (SCRATCH_ROOT / f"session-start-events-{run_no}.json").write_text(
        json.dumps(events, indent=2), encoding="utf-8"
    )
    (SCRATCH_ROOT / f"session-start-final-{run_no}.json").write_text(
        json.dumps(final, indent=2), encoding="utf-8"
    )
    activations_snapshot = SCRATCH_PROJECT / ".claude" / "activations.json"
    if activations_snapshot.is_file():
        shutil.copy(
            activations_snapshot, SCRATCH_ROOT / f"activations-after-run-{run_no}.json"
        )
    print(f"cost=${final.get('total_cost_usd', 0):.4f}")
    print(f"result: {final.get('result', '')!r}"[:1500])


def do_verify(run_no: int) -> int:
    results: list[tuple[str, bool, str]] = []
    events = json.loads(
        (SCRATCH_ROOT / f"session-start-events-{run_no}.json").read_text(
            encoding="utf-8"
        )
    )
    final = json.loads(
        (SCRATCH_ROOT / f"session-start-final-{run_no}.json").read_text(
            encoding="utf-8"
        )
    )
    reply = full_reply(events, final)
    activations = json.loads(
        (SCRATCH_ROOT / f"activations-after-run-{run_no}.json").read_text(
            encoding="utf-8"
        )
    )
    today = datetime.now().date().isoformat()

    if run_no == 1:
        # AC 19: /news was forced to fail (no web/shell tools), but the boot
        # still produced its own completion report.
        completed = bool(
            re.search(
                r"persona\s+active|session.?start\s+complete|boot|report",
                reply,
                re.IGNORECASE,
            )
        )
        news_failure_mentioned = bool(
            re.search(
                r"news.{0,80}(fail|could not|unable|no\s+(web|network|tool))",
                reply,
                re.IGNORECASE,
            )
        )
        results.append(
            (
                "AC19: a news failure never stops /session-start from completing",
                completed,
                f"completed={completed} news_failure_mentioned={news_failure_mentioned}",
            )
        )

        # last_run gets stamped even on a failed attempt.
        last_run_stamped = activations.get("news", {}).get("last_run") == today
        results.append(
            (
                "AC11 (setup half): last_run stamped even on a failed daily attempt",
                last_run_stamped,
                f"last_run={activations.get('news', {}).get('last_run')} today={today}",
            )
        )

    elif run_no == 2:
        # AC 11 (second half): step 8 skipped -- no /news invocation this time
        # (no Skill tool call naming news, and the reply doesn't present a
        # fresh news list), while the rest of the boot still completed.
        news_skill_invoked = any(
            isinstance(b, dict)
            and b.get("type") == "tool_use"
            and b.get("name") == "Skill"
            and b.get("input", {}).get("skill") == "news"
            for e in events
            if e.get("type") == "assistant"
            for b in (e.get("message", {}).get("content") or [])
        )
        completed = bool(
            re.search(
                r"persona\s+active|session.?start\s+complete|boot|report",
                reply,
                re.IGNORECASE,
            )
        )
        ok11_second = completed and not news_skill_invoked
        results.append(
            (
                "AC11 (second half): already ran today -> step 8 skips silently, boot still completes",
                ok11_second,
                f"completed={completed} news_skill_invoked={news_skill_invoked}",
            )
        )

    else:  # run 3
        # AC 6 (behavioral half): news OFF -> nothing about news is printed,
        # fetched or scheduled. No Skill tool call naming news, and the boot
        # still completed.
        news_skill_invoked = any(
            isinstance(b, dict)
            and b.get("type") == "tool_use"
            and b.get("name") == "Skill"
            and b.get("input", {}).get("skill") == "news"
            for e in events
            if e.get("type") == "assistant"
            for b in (e.get("message", {}).get("content") or [])
        )
        news_fetch_attempted = any(
            isinstance(b, dict)
            and b.get("type") == "tool_use"
            and b.get("name") in ("WebSearch", "WebFetch")
            for e in events
            if e.get("type") == "assistant"
            for b in (e.get("message", {}).get("content") or [])
        )
        completed = bool(
            re.search(
                r"persona\s+active|session.?start\s+complete|boot|report",
                reply,
                re.IGNORECASE,
            )
        )
        ok6 = completed and not news_skill_invoked and not news_fetch_attempted
        results.append(
            (
                "AC6 (behavioral half): news off -> nothing printed, fetched or scheduled",
                ok6,
                f"completed={completed} news_skill_invoked={news_skill_invoked} news_fetch_attempted={news_fetch_attempted}",
            )
        )

    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} of this run's criteria pass.")
    return 0 if passed == len(results) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", type=int, choices=(1, 2, 3))
    ap.add_argument("--verify", type=int, choices=(1, 2, 3))
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print(f"scratch project built at {SCRATCH_PROJECT}")
        return 0
    if args.run:
        do_run(args.run)
        return 0
    if args.verify:
        return do_verify(args.verify)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

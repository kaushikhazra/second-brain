#!/usr/bin/env python3
"""Issue #41 -- the owner opts a project into monitoring; the heartbeat spots
issues the brain has not seen.

Drives a scratch brain built from `src/` through the owner's door (`claude -p`,
`--resume` for the owner's answer). Alpha and beta are taken in; the owner says
yes to watching alpha and no to beta. Heartbeats are fired the way the cron fires
them: `Run /heartbeat "requested by cron"`, each a fresh session.

  --mode optin : AC 1 -- after take-in the brain asks whether to monitor
                 AC 2 (first half) -- the owner's yes/no is stored per project
  --mode beat  : AC 3 -- beat 1 reads monitored projects only: alpha's open
                 issues are reported, beta (not monitored) is never read
                 AC 4 -- each of alpha's open issues reported: project, number, title
                 AC 5 (first half) -- beat 2 reports none of them again

Expected issues are read live from GitHub (read-only) so the check follows the
sandbox, not a hardcoded list.

Usage:
    python check_monitor.py --all
    python check_monitor.py --build
    python check_monitor.py --run --mode optin
    python check_monitor.py --verify --mode optin

Scratch lives under C:/Projects/.tmp/second-brain-loop-41/ (overridable with
SB_CHECK_SCRATCH). Costs real money on --run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import scratch_brain as sb

SCRATCH_ROOT = Path(
    os.environ.get("SB_CHECK_SCRATCH", "C:/Projects/.tmp/second-brain-loop-41")
)
BRAIN = SCRATCH_ROOT / "brain"
SETTINGS = BRAIN / ".claude" / "projects"

BEAT = 'Run /heartbeat "requested by cron"'

MODES = ("optin", "beat")


def events(tag: str) -> Path:
    return SCRATCH_ROOT / f"monitor-events-{tag}.json"


def owner(prompt: str, tag: str, resume: str | None = None) -> None:
    sb.run_owner(prompt, events(tag), BRAIN, resume=resume)


def settings(name: str) -> dict:
    f = SETTINGS / f"{name}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def live_open_issues(slug: str) -> dict[str, str]:
    """Read-only, straight from GitHub -- what 'open' means right now."""
    out = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "-R",
            slug,
            "--state",
            "open",
            "--json",
            "number,title",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {str(i["number"]): i["title"] for i in json.loads(out.stdout or "[]")}


def reported(reply: str, number: str, title: str) -> bool:
    """Number and title of one issue, in the same line of the reply."""
    for line in reply.splitlines():
        if re.search(rf"#\s?{number}\b", line) and title.lower()[:20] in line.lower():
            return True
    return False


def do_run(mode: str) -> None:
    if mode == "optin":
        owner(f"Take this project in: {sb.ALPHA_HTTPS}", "takein-alpha")
        owner(
            "Yes, watch it.",
            "answer-alpha",
            resume=sb.session_id(events("takein-alpha")),
        )
        owner(f"Take this project in: {sb.BETA_HTTPS}", "takein-beta")
        owner(
            "No, don't watch this one.",
            "answer-beta",
            resume=sb.session_id(events("takein-beta")),
        )
    else:  # beat
        owner(BEAT, "beat-1")
        owner(BEAT, "beat-2")


def do_verify(mode: str) -> int:
    results: list[tuple[str, bool, str]] = []

    if mode == "optin":
        asked = [
            sb.has(
                r"(?:monitor|watch)[^?\n]{0,120}\?",
                sb.final_text(events(f"takein-{p}")),
            )
            for p in ("alpha", "beta")
        ]
        results.append(
            (
                "AC1: after taking a project in, the brain asks whether to monitor it",
                all(asked),
                f"asked alpha={asked[0]} beta={asked[1]}",
            )
        )
        on = settings("sb-sandbox-alpha").get("monitor")
        off = settings("sb-sandbox-beta").get("monitor")
        results.append(
            (
                "AC2 (first half): the owner's answer switches monitoring on/off per project",
                on is True and off is False,
                f"alpha.monitor={on!r} beta.monitor={off!r}",
            )
        )

    else:  # beat
        alpha_open = live_open_issues("kaushikhazra/sb-sandbox-alpha")
        beta_open = live_open_issues("kaushikhazra/sb-sandbox-beta")
        beat1 = sb.final_text(events("beat-1"))
        beat2 = sb.final_text(events("beat-2"))

        each = {n: reported(beat1, n, t) for n, t in alpha_open.items()}
        named_project = sb.has(r"sb-sandbox-alpha", beat1)
        results.append(
            (
                "AC4: a new issue is reported once: project, number, title",
                bool(alpha_open) and all(each.values()) and named_project,
                f"alpha_open={sorted(alpha_open)} reported={each} project_named={named_project}",
            )
        )

        beta_seen = settings("sb-sandbox-beta").get("seen_issues")
        beta_named = any(t.lower()[:20] in beat1.lower() for t in beta_open.values())
        alpha_seen = sorted(settings("sb-sandbox-alpha").get("seen_issues", {}))
        results.append(
            (
                "AC3: each beat checks the open issues of monitored projects only",
                alpha_seen == sorted(alpha_open)
                and beta_seen is None
                and not beta_named,
                f"alpha_seen={alpha_seen} beta_seen={beta_seen} beta_issue_in_reply={beta_named}",
            )
        )

        again = {n: reported(beat2, n, t) for n, t in alpha_open.items()}
        results.append(
            (
                "AC5 (first half): issues already reported are not reported again",
                not any(again.values()),
                f"reported_again_on_beat_2={again}",
            )
        )

    return sb.report(results)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # see check_clone.py
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--mode", choices=MODES, default="optin")
    ap.add_argument(
        "--all",
        action="store_true",
        help="build, then run and verify every mode in order",
    )
    args = ap.parse_args()

    if args.all or args.build:
        SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
        sb.build(BRAIN)
    if args.all:
        failed = 0
        for mode in MODES:
            do_run(mode)
            failed += do_verify(mode)
        print(f"\n#41 regression: {len(MODES) - failed}/{len(MODES)} modes pass.")
        return 1 if failed else 0
    if args.build:
        print(f"scratch brain built at {BRAIN}")
        return 0
    if args.run:
        do_run(args.mode)
        return 0
    if args.verify:
        return do_verify(args.mode)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

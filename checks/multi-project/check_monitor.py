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

  --mode change    : AC 2 (second half) -- off, list, back on
  --mode lifecycle : AC 4 on a genuinely new issue (opened on alpha by the check,
                     always closed again) and AC 5 (second half) -- closed drops off
  --mode failure   : AC 6 -- a monitored GitLab project with no sign-in: told on
                     the first beat, not the second (#40's insteadOf stand-in; no
                     GitLab host contacted)
  --mode restart   : AC 7 -- a fresh session's beat: the seen record on disk
                     matches what is open, and nothing old resurfaces

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

ALPHA_SLUG = "kaushikhazra/sb-sandbox-alpha"
TEST_TITLE = "Check #41: temporary issue (opened and closed by check_monitor.py)"

# AC 6's GitLab project: the #40 stand-in -- gitlab.com URL, local bare repo via
# insteadOf, no GitLab credentials on this machine, so no GitLab host contacted.
GITLAB_URL = "https://gitlab.com/kaushikhazra/sb-gitlab-demo.git"
GITLAB_BARE = SCRATCH_ROOT / "sb-gitlab-demo.git"
GIT_ENV = {
    "GIT_CONFIG_COUNT": "1",
    "GIT_CONFIG_KEY_0": f"url.{GITLAB_BARE.as_posix()}.insteadOf",
    "GIT_CONFIG_VALUE_0": GITLAB_URL,
}

MODES = ("optin", "beat", "change", "lifecycle", "failure", "restart")


def events(tag: str) -> Path:
    return SCRATCH_ROOT / f"monitor-events-{tag}.json"


def owner(prompt: str, tag: str, resume: str | None = None) -> None:
    sb.run_owner(prompt, events(tag), BRAIN, resume=resume, extra_env=GIT_ENV)


def gh(*args: str) -> str:
    out = subprocess.run(
        ["gh", *args], capture_output=True, text=True, encoding="utf-8"
    )
    return out.stdout.strip()


def test_issue_number() -> str:
    """Written by --run lifecycle so --verify can find the issue it made."""
    f = SCRATCH_ROOT / "lifecycle-issue.txt"
    return f.read_text(encoding="utf-8").strip() if f.is_file() else ""


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
    elif mode == "beat":
        owner(BEAT, "beat-1")
        owner(BEAT, "beat-2")
    elif mode == "change":
        owner("Stop watching sb-sandbox-alpha's issues.", "change-off")
        owner("Which projects are you watching?", "change-list")
        owner("Start watching sb-sandbox-alpha's issues again.", "change-on")
    elif mode == "lifecycle":
        # The sandbox is the loop's to change; the issue is always closed again.
        url = gh(
            "issue",
            "create",
            "-R",
            ALPHA_SLUG,
            "--title",
            TEST_TITLE,
            "--body",
            "Opened by second-brain's #41 check. Closed by it within minutes.",
        )
        number = url.rstrip("/").rsplit("/", 1)[-1]
        (SCRATCH_ROOT / "lifecycle-issue.txt").write_text(number, encoding="utf-8")
        try:
            owner(BEAT, "life-1")
            owner(BEAT, "life-2")
        finally:
            gh(
                "issue",
                "close",
                number,
                "-R",
                ALPHA_SLUG,
                "--comment",
                "Closed by the #41 check.",
            )
        owner(BEAT, "life-3")
    elif mode == "failure":
        work = SCRATCH_ROOT / "sb-gitlab-demo.work"
        for old in (GITLAB_BARE, work):
            if old.exists():
                sb.remove_tree(old)
        sb.git("clone", "-q", sb.ALPHA_HTTPS, str(work), cwd=SCRATCH_ROOT)
        sb.git("clone", "-q", "--bare", str(work), str(GITLAB_BARE), cwd=SCRATCH_ROOT)
        sb.remove_tree(work)
        owner(f"Take this project in: {GITLAB_URL}", "takein-gitlab")
        owner(
            "Yes, watch it.",
            "answer-gitlab",
            resume=sb.session_id(events("takein-gitlab")),
        )
        owner(BEAT, "fail-1")
        owner(BEAT, "fail-2")
    else:  # restart -- a fresh session long after; only the files carry over
        owner(BEAT, "restart")


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

    elif mode == "change":
        off_reply = sb.final_text(events("change-off"))
        listed = sb.final_text(events("change-list"))
        # After "off", the list must not show alpha as watched.
        # table rows and list items only -- not a hint like "to start watching
        # one, say 'monitor sb-sandbox-alpha'"
        alpha_lines = [
            l
            for l in listed.splitlines()
            if "sb-sandbox-alpha" in l and l.lstrip().startswith(("|", "-", "*"))
        ]
        alpha_listed_on = any(
            sb.has(r"\bon\b|watch(?:ed|ing)|monitor(?:ed|ing)", l)
            and not sb.has(r"\boff\b|not\W+(?:watch|monitor)", l)
            for l in alpha_lines
        )
        none_watched = sb.has(r"\bnone\b|not watching any|no projects?|nothing", listed)
        on_now = settings("sb-sandbox-alpha").get("monitor")
        results.append(
            (
                "AC2 (second half): the owner switches monitoring off/on later and lists what is monitored",
                sb.has(r"sb-sandbox-alpha", off_reply)
                and (none_watched or (alpha_lines and not alpha_listed_on))
                and on_now is True,
                f"list_after_off: alpha_lines={len(alpha_lines)} alpha_shown_on={alpha_listed_on} "
                f"none_watched={none_watched} | monitor_after_on={on_now!r}",
            )
        )

    elif mode == "lifecycle":
        n = test_issue_number()
        l1, l2, l3 = (sb.final_text(events(f"life-{i}")) for i in (1, 2, 3))
        once = reported(l1, n, TEST_TITLE) and not reported(l2, n, TEST_TITLE)
        results.append(
            (
                "AC4: a genuinely new issue is reported once: project, number, title",
                bool(n) and once and sb.has(r"sb-sandbox-alpha", l1),
                f"issue=#{n} beat1_reported={reported(l1, n, TEST_TITLE)} beat2_reported={reported(l2, n, TEST_TITLE)}",
            )
        )
        seen = settings("sb-sandbox-alpha").get("seen_issues", {})
        closed_mentioned = bool(n) and sb.has(rf"#\s?{n}\b", l3)
        results.append(
            (
                "AC5 (second half): closed issues drop off",
                bool(n) and n not in seen and not closed_mentioned,
                f"issue=#{n} still_in_seen={n in seen} mentioned_after_close={closed_mentioned}",
            )
        )

    elif mode == "failure":
        f1 = sb.final_text(events("fail-1"))
        f2 = sb.final_text(events("fail-2"))
        cause = r"not signed in|sign(?:ed)? in|glab auth login|GITLAB_TOKEN|unreachable|can'?t reach"
        told_first = sb.has(r"sb-gitlab-demo", f1) and sb.has(cause, f1)
        told_again = sb.has(r"sb-gitlab-demo", f2) and sb.has(cause, f2)
        recorded = settings("sb-gitlab-demo").get("issues_failure")
        results.append(
            (
                "AC6: tracker unreachable or not signed in -> told once, not every beat",
                told_first and not told_again and bool(recorded),
                f"told_on_beat_1={told_first} told_again_on_beat_2={told_again} recorded={recorded!r}",
            )
        )

    elif mode == "restart":
        reply = sb.final_text(events("restart"))
        alpha_open = live_open_issues(ALPHA_SLUG)
        seen = settings("sb-sandbox-alpha").get("seen_issues", {})
        # every open issue -- all were seen before the restart, so none is new
        resurfaced = {n: reported(reply, n, t) for n, t in alpha_open.items()}
        results.append(
            (
                "AC7: what the brain has seen survives a restart; nothing old resurfaces",
                sorted(seen) == sorted(alpha_open) and not any(resurfaced.values()),
                f"seen_on_disk={sorted(seen)} open_now={sorted(alpha_open)} resurfaced={resurfaced}",
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

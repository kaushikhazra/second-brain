#!/usr/bin/env python3
"""Issue #40 -- the brain works with whichever issue tracker a project uses.

Drives a scratch brain built from `src/` through the owner's door (`claude -p`).
Three projects are taken in:

  sb-sandbox-alpha   GitHub   -- the real private sandbox
  sb-gitlab-demo     GitLab   -- https://gitlab.com/kaushikhazra/sb-gitlab-demo.git
  sb-bitbucket-demo  Bitbucket (unsupported) -- https://bitbucket.org/...

The GitLab and Bitbucket URLs never leave this machine: git's
`url.<local bare repo>.insteadOf=<that URL>`, passed to the brain's session as
GIT_CONFIG_* environment, turns every fetch into a local one while the clone's
`origin` stays the gitlab.com / bitbucket.org address. No GitLab host is ever
contacted (multi-project-assumptions.md). GitLab credentials are absent on this
machine, so AC 5 sees a real "missing".

  --mode detect   : AC 1 -- each take-in names code host, tracker and how it knows
                    AC 4 -- Bitbucket: still managed, issue work said unavailable
                    AC 5 (first half) -- GitLab: what credentials are needed, said
  --mode trackers : AC 3 -- "which trackers can you work with?" -> GitHub, GitLab
  --mode override : AC 2 -- the owner sets alpha's tracker to GitLab
  --mode restart  : AC 6 -- a fresh session reports alpha's tracker as GitLab
                    AC 5 (second half) -- asked about sb-gitlab-demo again, the
                    credentials notice is not repeated

Usage:
    python check_tracker.py --all
    python check_tracker.py --build
    python check_tracker.py --run --mode detect
    python check_tracker.py --verify --mode detect

Scratch lives under C:/Projects/.tmp/second-brain-loop-40/ (overridable with
SB_CHECK_SCRATCH). Costs real money on --run.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import scratch_brain as sb

SCRATCH_ROOT = Path(
    os.environ.get("SB_CHECK_SCRATCH", "C:/Projects/.tmp/second-brain-loop-40")
)
BRAIN = SCRATCH_ROOT / "brain"
PROJECTS = BRAIN / "projects"
SETTINGS = BRAIN / ".claude" / "projects"

GITLAB_URL = "https://gitlab.com/kaushikhazra/sb-gitlab-demo.git"
BITBUCKET_URL = "https://bitbucket.org/kaushikhazra/sb-bitbucket-demo.git"
GITLAB_BARE = SCRATCH_ROOT / "sb-gitlab-demo.git"
BITBUCKET_BARE = SCRATCH_ROOT / "sb-bitbucket-demo.git"

# Reaches the brain's own git calls: the two URLs resolve to local bare repos.
GIT_ENV = {
    "GIT_CONFIG_COUNT": "2",
    "GIT_CONFIG_KEY_0": f"url.{GITLAB_BARE.as_posix()}.insteadOf",
    "GIT_CONFIG_VALUE_0": GITLAB_URL,
    "GIT_CONFIG_KEY_1": f"url.{BITBUCKET_BARE.as_posix()}.insteadOf",
    "GIT_CONFIG_VALUE_1": BITBUCKET_URL,
}

MODES = ("detect", "trackers", "override", "restart")


def events(tag: str) -> Path:
    return SCRATCH_ROOT / f"tracker-events-{tag}.json"


def owner(prompt: str, tag: str) -> None:
    sb.run_owner(prompt, events(tag), BRAIN, extra_env=GIT_ENV)


def make_bare(url: str, bare: Path, extra_file: str | None) -> None:
    """A local bare repo with a sandbox's history, plus one host-typical file."""
    work = bare.with_suffix(".work")
    for old in (bare, work):
        if old.exists():
            sb.remove_tree(old)
    sb.git("clone", "-q", url, str(work), cwd=SCRATCH_ROOT)
    if extra_file:
        (work / extra_file).write_text(
            "# host-typical file for check_tracker.py\n", encoding="utf-8"
        )
        sb.git("add", extra_file, cwd=work)
        sb.git("commit", "-q", "-m", f"add {extra_file}", cwd=work)
    sb.git("clone", "-q", "--bare", str(work), str(bare), cwd=SCRATCH_ROOT)
    sb.remove_tree(work)


def build() -> None:
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    sb.build(BRAIN)
    make_bare(sb.ALPHA_HTTPS, GITLAB_BARE, ".gitlab-ci.yml")
    make_bare(sb.BETA_HTTPS, BITBUCKET_BARE, "bitbucket-pipelines.yml")


def settings(name: str) -> dict:
    f = SETTINGS / f"{name}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def do_run(mode: str) -> None:
    if mode == "detect":
        owner(f"Take this project in: {sb.ALPHA_HTTPS}", "detect-github")
        owner(f"Take this project in: {GITLAB_URL}", "detect-gitlab")
        owner(f"Take this project in: {BITBUCKET_URL}", "detect-bitbucket")
    elif mode == "trackers":
        owner("Which issue trackers can you work with?", "trackers")
    elif mode == "override":
        owner(
            "sb-sandbox-alpha's issues are kept in GitLab, not GitHub. Use GitLab as its issue tracker.",
            "override",
        )
    else:  # restart -- fresh sessions, nothing carried over but the files
        owner("Which issue tracker does sb-sandbox-alpha use?", "restart-alpha")
        owner("Which issue tracker does sb-gitlab-demo use?", "restart-gitlab")


def do_verify(mode: str) -> int:
    results: list[tuple[str, bool, str]] = []

    if mode == "detect":
        gh = sb.reply_text(events("detect-github"))
        gl = sb.reply_text(events("detect-gitlab"))
        bb = sb.reply_text(events("detect-bitbucket"))
        ok_gh = sb.has(r"github", gh) and sb.has(r"remote|origin|URL|address", gh)
        ok_gl = (
            sb.has(r"gitlab", gl)
            and sb.has(r"remote|origin|URL|address", gl)
            and sb.has(r"\.gitlab-ci\.yml", gl)
        )
        ok_bb = sb.has(r"bitbucket", bb) and sb.has(r"remote|origin|URL|address", bb)
        results.append(
            (
                "AC1: on take-in the brain names code host, tracker and how it knows",
                ok_gh and ok_gl and ok_bb,
                f"github={ok_gh} gitlab(+.gitlab-ci.yml)={ok_gl} bitbucket={ok_bb}",
            )
        )

        managed = (PROJECTS / "sb-bitbucket-demo" / ".git").is_dir()
        origin = (
            sb.git(
                "remote", "get-url", "origin", cwd=PROJECTS / "sb-bitbucket-demo"
            ).stdout.strip()
            if managed
            else ""
        )
        unavailable = (
            sb.has(
                r"(?:not|isn't|aren't|no)\W+(?:\w+\W+){0,4}(?:available|supported)|unsupported",
                bb,
            )
            and sb.has(r"monitor|watch", bb)
            and sb.has(r"issue", bb)
        )
        results.append(
            (
                "AC4: an unsupported tracker -> still managed; monitoring and issue work said unavailable",
                managed and origin == BITBUCKET_URL and unavailable,
                f"managed={managed} origin={origin!r} said_unavailable={unavailable}",
            )
        )

        needed = sb.has(r"glab auth login|GITLAB_TOKEN", gl)
        results.append(
            (
                "AC5 (first half): missing GitLab credentials -> the owner is told what is needed",
                needed,
                f"named_what_is_needed={needed}",
            )
        )

    elif mode == "trackers":
        reply = sb.reply_text(events("trackers"))
        named = sb.has(r"github", reply) and sb.has(r"gitlab", reply)
        # Naming GitLab while saying support is GitHub-only is not listing it --
        # #40 cycle 2's removal demo answered "Right now, only **GitHub**" and
        # then mentioned GitLab in the explanation.
        github_only = sb.has(r"only\W+(?:\*\*)?github\b(?!\W+(?:and|&))", reply)
        results.append(
            (
                "AC3: the brain lists the trackers it works with: GitHub and GitLab",
                named and not github_only,
                f"github+gitlab named={named} github_only={github_only}",
            )
        )

    elif mode == "override":
        reply = sb.reply_text(events("override"))
        stored = settings("sb-sandbox-alpha").get("override", {}).get("tracker")
        confirmed = sb.has(r"gitlab", reply)
        results.append(
            (
                "AC2: the owner overrides the tracker explicitly",
                stored == "gitlab" and confirmed,
                f"stored_override={stored!r} reply_confirms={confirmed}",
            )
        )

    else:  # restart
        alpha = sb.reply_text(events("restart-alpha"))
        gitlab = sb.reply_text(events("restart-gitlab"))
        survived = sb.has(r"gitlab", alpha) and sb.has(
            r"set by (?:you|the owner)|you (?:set|told|chose)|overrid", alpha
        )
        results.append(
            (
                "AC6: what was overridden survives a restart",
                survived,
                f"alpha_reported_gitlab_as_overridden={survived}",
            )
        )
        repeated = sb.has(r"glab auth login|GITLAB_TOKEN", gitlab)
        told_before = "gitlab" in settings("sb-gitlab-demo").get("credentials_told", [])
        results.append(
            (
                "AC5 (second half): the credentials notice is given once, not repeated",
                told_before and not repeated and sb.has(r"gitlab", gitlab),
                f"recorded_as_told={told_before} repeated_on_second_ask={repeated}",
            )
        )

    return sb.report(results)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # see check_clone.py
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--mode", choices=MODES, default="detect")
    ap.add_argument(
        "--all",
        action="store_true",
        help="build, then run and verify every mode in order",
    )
    args = ap.parse_args()

    if args.all:
        build()
        failed = 0
        for mode in MODES:
            do_run(mode)
            failed += do_verify(mode)
        print(f"\n#40 regression: {len(MODES) - failed}/{len(MODES)} modes pass.")
        return 1 if failed else 0
    if args.build:
        build()
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

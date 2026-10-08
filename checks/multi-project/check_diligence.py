#!/usr/bin/env python3
"""Issue #42 -- the brain runs due diligence with the owner before any work.

Drives a scratch brain built from `src/` through the owner's door (`claude -p`,
`--resume` for the owner's answer in the same conversation). Alpha and beta are
taken in first, the way an owner would.

"Nothing was created" is judged on the object: before each turn the check
snapshots the project clone (branches, working tree, `.claude/specs/`) and the
brain (`.claude/loop/`, its own git status); after the turn they must match.

  --mode present : AC 1 -- alpha #2: what it asks, its criteria, size and risk,
                   open questions, and the question whether to start
                   AC 2 (first half) -- that turn created nothing
  --mode no      : AC 2 -- the owner says no in the same conversation; still
                   nothing created
                   AC 3 (first half) -- the no is recorded
  --mode again   : AC 3 -- a fresh session raising alpha #2 again: no second
                   walk-through, no question, nothing created
  --mode vague   : AC 4 -- beta #2 (no criteria): cannot converge, asks for
                   criteria, does not offer to start, creates nothing
  --mode yes     : AC 5 -- alpha #1, owner says yes: the reply states the
                   branch and the development method (spec-driven)

Usage:
    python check_diligence.py --all
    python check_diligence.py --build
    python check_diligence.py --run --mode present
    python check_diligence.py --verify --mode present

Scratch lives under C:/Projects/.tmp/second-brain-loop-42/ (overridable with
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
    os.environ.get("SB_CHECK_SCRATCH", "C:/Projects/.tmp/second-brain-loop-42")
)
BRAIN = SCRATCH_ROOT / "brain"
ALPHA = BRAIN / "projects" / "sb-sandbox-alpha"
BETA = BRAIN / "projects" / "sb-sandbox-beta"
SETTINGS = BRAIN / ".claude" / "projects"

MODES = ("present", "no", "again", "vague", "yes")


def events(tag: str) -> Path:
    return SCRATCH_ROOT / f"diligence-events-{tag}.json"


def owner(prompt: str, tag: str, resume: str | None = None) -> None:
    sb.run_owner(prompt, events(tag), BRAIN, resume=resume, budget="3.0")


def settings(name: str) -> dict:
    f = SETTINGS / f"{name}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def snapshot() -> dict:
    """Everything a start of work would change."""

    def project(p: Path) -> dict:
        specs = p / ".claude" / "specs"
        return {
            "branches": sb.git(
                "branch", "--list", "--format=%(refname:short)", cwd=p
            ).stdout.split(),
            "status": sb.git(
                "status", "--porcelain", "--untracked-files=all", cwd=p
            ).stdout.splitlines(),
            "specs": sorted(str(f.relative_to(p)) for f in specs.rglob("*"))
            if specs.exists()
            else [],
        }

    loop = BRAIN / ".claude" / "loop"
    return {
        "alpha": project(ALPHA),
        "beta": project(BETA),
        "brain_loop": sorted(str(f.relative_to(BRAIN)) for f in loop.rglob("*"))
        if loop.exists()
        else [],
        "brain_status": [
            l
            for l in sb.git(
                "status", "--porcelain", "--untracked-files=all", cwd=BRAIN
            ).stdout.splitlines()
            # the brain's own runtime files are not work on an issue
            if not any(
                s in l
                for s in (
                    ".claude/projects/",
                    ".claude/activations.json",
                    ".claude/scheduled_tasks",
                )
            )
        ],
    }


def snap_file(tag: str) -> Path:
    return SCRATCH_ROOT / f"snapshot-{tag}.json"


def turn(prompt: str, tag: str, resume: str | None = None) -> None:
    snap_file(f"{tag}-before").write_text(
        json.dumps(snapshot(), indent=2), encoding="utf-8"
    )
    owner(prompt, tag, resume)
    snap_file(f"{tag}-after").write_text(
        json.dumps(snapshot(), indent=2), encoding="utf-8"
    )


def unchanged(tag: str) -> tuple[bool, str]:
    def flatten(snap: dict) -> dict:
        out = {}
        for key, value in snap.items():
            if isinstance(value, dict):
                out.update({f"{key}.{k}": v for k, v in value.items()})
            else:
                out[key] = value
        return out

    before = flatten(json.loads(snap_file(f"{tag}-before").read_text(encoding="utf-8")))
    after = flatten(json.loads(snap_file(f"{tag}-after").read_text(encoding="utf-8")))
    diff = {k: (before[k], after[k]) for k in before if before[k] != after[k]}
    return not diff, f"changed={diff}" if diff else "nothing changed"


ASKS_TO_START = r"(?:shall|should|do you want|want me to|would you like)[^?\n]{0,80}(?:start|begin|go ahead|work on)[^?\n]*\?"


def do_run(mode: str) -> None:
    if mode == "present":
        owner(f"Take this project in: {sb.ALPHA_HTTPS}", "takein-alpha")
        owner(f"Take this project in: {sb.BETA_HTTPS}", "takein-beta")
        turn("Let's work on sb-sandbox-alpha issue #2.", "present")
    elif mode == "no":
        turn("No.", "no", resume=sb.session_id(events("present")))
    elif mode == "again":
        turn("Let's work on sb-sandbox-alpha issue #2.", "again")
    elif mode == "vague":
        turn("Let's work on sb-sandbox-beta issue #2.", "vague")
    else:  # yes
        owner("Let's work on sb-sandbox-alpha issue #1.", "yes-present")
        owner("Yes, go ahead.", "yes", resume=sb.session_id(events("yes-present")))


def do_verify(mode: str) -> int:
    results: list[tuple[str, bool, str]] = []

    if mode == "present":
        r = sb.final_text(events("present"))
        parts = {
            "asks": sb.has(r"empty name|clear error", r),
            "criteria": sb.has(r"acceptance criteria|criteria", r),
            "size": sb.has(r"\bsize\b|small|medium|large", r),
            "risk": sb.has(r"\brisk", r),
            "questions": sb.has(r"open questions?|question", r),
            "asks_to_start": sb.has(ASKS_TO_START, r),
        }
        results.append(
            (
                "AC1: the brain presents what it asks, criteria, size and risk, open questions",
                all(parts.values()),
                str(parts),
            )
        )
        ok, detail = unchanged("present")
        results.append(
            ("AC2 (first half): presenting the diligence starts nothing", ok, detail)
        )

    elif mode == "no":
        ok, detail = unchanged("no")
        results.append(
            ("AC2: nothing starts without the owner's yes (owner said no)", ok, detail)
        )
        d = settings("sb-sandbox-alpha").get("decisions", {}).get("2", {})
        results.append(
            (
                "AC3 (first half): a no is recorded",
                d.get("answer") == "no" and bool(d.get("updated_at")),
                f"decision={d}",
            )
        )

    elif mode == "again":
        r = sb.final_text(events("again"))
        walked_again = sb.has(ASKS_TO_START, r) or (
            sb.has(r"\brisk", r) and sb.has(r"open questions?", r)
        )
        said_set_aside = sb.has(
            r"\bno\b|set aside|declined|passed on|said no|not now|later", r
        )
        ok, detail = unchanged("again")
        results.append(
            (
                "AC3: the brain does not ask again until the issue changes",
                said_set_aside and not walked_again and ok,
                f"walked_through_again={walked_again} said_set_aside={said_set_aside} | {detail}",
            )
        )

    elif mode == "vague":
        r = sb.final_text(events("vague"))
        cannot = sb.has(
            r"can(?:no|')t\W+converge|cannot converge|no (?:checkable|clear) (?:acceptance )?criteria|without criteria",
            r,
        )
        asks_for = sb.has(
            r"criteria[^.\n]{0,80}\?|(?:give|send|add|tell)[^.\n]{0,40}criteria", r
        )
        offers = sb.has(ASKS_TO_START, r)
        ok, detail = unchanged("vague")
        results.append(
            (
                "AC4: no checkable criteria -> says it cannot converge, asks for criteria, does not start",
                cannot and asks_for and not offers and ok,
                f"cannot_converge={cannot} asks_for_criteria={asks_for} offers_to_start={offers} | {detail}",
            )
        )

    else:  # yes
        r = sb.reply_text(events("yes"))
        branch = sb.has(r"branch[^\n]{0,60}`?[\w./-]*1[\w./-]*`?|`feature/1[\w-]*`", r)
        method = sb.has(r"spec[- ]?(?:driven|first)|requirement\.md", r)
        d = settings("sb-sandbox-alpha").get("decisions", {}).get("1", {})
        results.append(
            (
                "AC5: on yes the brain states the branch and the development method",
                branch and method and d.get("answer") == "yes",
                f"branch_stated={branch} method_stated={method} decision={d.get('answer')!r}",
            )
        )

    return sb.report(results)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # see check_clone.py
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--mode", choices=MODES, default="present")
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
        print(f"\n#42 regression: {len(MODES) - failed}/{len(MODES)} modes pass.")
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

#!/usr/bin/env python3
"""Issue #43 -- the brain follows a project's own development method, and loop
engineering when it has none.

Drives a scratch brain built from `src/` through the owner's door (`claude -p`,
`--resume` for the owner's answers). Alpha (CLAUDE.md states a method:
spec-driven) and beta (no CLAUDE.md) are taken in first, the way an owner would.

  --mode detect : AC 1 -- before starting, the brain tells the owner which method it
                  found in alpha #1, and that it found none in beta #1; neither
                  turn changes anything

Usage:
    python check_method.py --all
    python check_method.py --build
    python check_method.py --run --mode detect
    python check_method.py --verify --mode detect

Scratch lives under C:/Projects/.tmp/second-brain-loop-43/ (overridable with
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
    os.environ.get("SB_CHECK_SCRATCH", "C:/Projects/.tmp/second-brain-loop-43")
)
BRAIN = SCRATCH_ROOT / "brain"
ALPHA = BRAIN / "projects" / "sb-sandbox-alpha"
BETA = BRAIN / "projects" / "sb-sandbox-beta"

MODES = ("detect", "follow")

BASELINE = "method-baseline.json"


def events(tag: str) -> Path:
    return SCRATCH_ROOT / f"method-events-{tag}.json"


def owner(prompt: str, tag: str, resume: str | None = None) -> None:
    sb.run_owner(prompt, events(tag), BRAIN, resume=resume, budget="3.0")


def snapshot() -> dict:
    """Everything a start of work would change, in both projects and the brain."""

    def project(p: Path) -> dict:
        specs = p / ".claude" / "specs"
        loop = p / ".claude" / "loop"
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
            "loop": sorted(str(f.relative_to(p)) for f in loop.rglob("*"))
            if loop.exists()
            else [],
        }

    return {"alpha": project(ALPHA), "beta": project(BETA)}


def turn(prompt: str, tag: str, resume: str | None = None) -> None:
    before = SCRATCH_ROOT / f"method-snapshot-{tag}-before.json"
    after = SCRATCH_ROOT / f"method-snapshot-{tag}-after.json"
    before.write_text(json.dumps(snapshot(), indent=2), encoding="utf-8")
    owner(prompt, tag, resume)
    after.write_text(json.dumps(snapshot(), indent=2), encoding="utf-8")


def unchanged(tag: str) -> tuple[bool, str]:
    def read(kind: str) -> dict:
        f = SCRATCH_ROOT / f"method-snapshot-{tag}-{kind}.json"
        return json.loads(f.read_text(encoding="utf-8"))

    before, after = read("before"), read("after")
    diff = {
        f"{p}.{k}": (before[p][k], after[p][k])
        for p in before
        for k in before[p]
        if before[p][k] != after[p][k]
    }
    return not diff, f"changed={diff}" if diff else "nothing changed"


def sha(ref: str, cwd: Path) -> str:
    return sb.git("rev-parse", "--verify", "-q", ref, cwd=cwd).stdout.strip()


def remote_main() -> str:
    out = sb.git("ls-remote", "--heads", "origin", "main", cwd=ALPHA).stdout.split()
    return out[0] if out else ""


def do_run(mode: str) -> None:
    if mode == "detect":
        owner(f"Take this project in: {sb.ALPHA_HTTPS}", "takein-alpha")
        owner(f"Take this project in: {sb.BETA_HTTPS}", "takein-beta")
        turn("Let's work on sb-sandbox-alpha issue #1.", "detect-alpha")
        turn("Let's work on sb-sandbox-beta issue #1.", "detect-beta")
    elif mode == "follow":
        # Alpha carries feature/1-* branches from earlier runs on the shared remote;
        # the owner says to ignore them so the brain builds on a branch of its own.
        (SCRATCH_ROOT / BASELINE).write_text(
            json.dumps(
                {
                    "main": sha("main", ALPHA),
                    "origin_main": remote_main(),
                    "branches": sb.git(
                        "branch", "--all", "--format=%(refname:short)", cwd=ALPHA
                    ).stdout.split(),
                }
            ),
            encoding="utf-8",
        )
        owner("Let's work on sb-sandbox-alpha issue #1.", "follow-present")
        owner(
            "Yes, go ahead. Build it fresh on a new branch of your own; leave the older "
            "feature/1-* branches alone.",
            "follow",
            resume=sb.session_id(events("follow-present")),
        )


def do_verify(mode: str) -> int:
    results: list[tuple[str, bool, str]] = []

    if mode == "detect":
        ra = sb.final_text(events("detect-alpha"))
        rb = sb.final_text(events("detect-beta"))
        alpha_found = sb.has(
            r"spec[- ]?(?:driven|first)|requirement\.md|\bspec\b[^\n]{0,80}requirement",
            ra,
        )
        beta_none = sb.has(
            r"no (?:development |stated |documented )?(?:method|process|workflow)"
            r"|(?:method|process)[^.\n]{0,40}\b(?:none|not stated|isn'?t stated|not documented)"
            r"|brain'?s own (?:method|loops?)|no `?CLAUDE\.md`?"
            r"|found none|doesn'?t (?:state|have|specify|document)[^.\n]{0,30}(?:method|process)"
            r"|none (?:is |was )?(?:stated|found)",
            rb,
        )
        beta_loop = sb.has(r"loop", rb)
        ok_a, detail_a = unchanged("detect-alpha")
        ok_b, detail_b = unchanged("detect-beta")
        results.append(
            (
                "AC1: before starting, the brain tells the owner the method it found, or that it found none",
                alpha_found and beta_none and beta_loop and ok_a and ok_b,
                f"alpha_method_named={alpha_found} beta_says_none={beta_none} "
                f"beta_names_loops={beta_loop} | alpha: {detail_a} | beta: {detail_b}",
            )
        )

    elif mode == "follow":
        base = json.loads((SCRATCH_ROOT / BASELINE).read_text(encoding="utf-8"))
        new = sorted(
            b
            for b in sb.git(
                "branch", "--format=%(refname:short)", cwd=ALPHA
            ).stdout.split()
            if b != "main"
            and f"origin/{b}" not in base["branches"]
            and b not in base["branches"]
        )
        # AC 2 -- alpha's own method (spec first): requirement, design and task exist on
        # the new branch, written before any change under src/, and no loop was made
        specs: dict[str, list[str]] = {}
        for b in new:
            listing = sb.git(
                "ls-tree", "-r", "--name-only", b, cwd=ALPHA
            ).stdout.split()
            found = [f for f in listing if f.startswith(".claude/specs/")]
            if {"requirement.md", "design.md", "task.md"} <= {
                Path(f).name for f in found
            }:
                specs[b] = found
        spec_branch = next(iter(specs), "")
        spec_before_code = False
        if spec_branch:
            # order of the brain's own writes (the owner's door), else of the commits
            paths = [
                i.get("file_path", "").replace("\\", "/")
                for i in sb.tool_uses(events("follow"), "Write", "Edit")
            ]
            first = lambda items, mark: next(
                (n for n, x in enumerate(items) if mark in x), None
            )
            s_w, c_w = first(paths, "/.claude/specs/"), first(paths, "/src/")
            log = sb.git(
                "log",
                "--reverse",
                "--format=%H",
                "--name-only",
                f"main..{spec_branch}",
                cwd=ALPHA,
            ).stdout.splitlines()
            s_c, c_c = first(log, ".claude/specs/"), first(log, "src/")
            by_writes = s_w is not None and c_w is not None and s_w < c_w
            by_commits = s_c is not None and c_c is not None and s_c < c_c
            spec_before_code = by_writes or by_commits
        no_loop = not (ALPHA / ".claude" / "loop").exists() and not any(
            sb.git(
                "ls-tree", "-r", "--name-only", b, ".claude/loop", cwd=ALPHA
            ).stdout.strip()
            for b in new
        )
        results.append(
            (
                "AC2: a project with its own method gets that method",
                bool(spec_branch) and spec_before_code and no_loop,
                f"new_branches={new} spec_branch={spec_branch!r} spec_before_code={spec_before_code} no_loop_folder={no_loop}",
            )
        )
        # AC 4 -- work on a feature branch, never merged: main did not move locally or
        # on the remote, no merge commit exists, no new branch was folded into main
        merges = sb.git(
            "log", "--merges", "--format=%h", "--all", cwd=ALPHA
        ).stdout.split()
        folded = [
            b
            for b in new
            if sb.git("merge-base", "--is-ancestor", b, "main", cwd=ALPHA).returncode
            == 0
            and sha(b, ALPHA) != sha("main", ALPHA)
        ]
        main_same = sha("main", ALPHA) == base["main"]
        remote_same = remote_main() == base["origin_main"]
        on_feature = bool(new)
        results.append(
            (
                "AC4: work happens on a feature branch; the brain never merges",
                on_feature and main_same and remote_same and not merges and not folded,
                f"feature_branch={new} main_unmoved={main_same} origin_main_unmoved={remote_same} merges={merges} folded_into_main={folded}",
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

    if args.all or args.build:
        SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
        sb.build(BRAIN)
    if args.all:
        failed = 0
        for mode in MODES:
            do_run(mode)
            failed += do_verify(mode)
        print(f"\n#43 regression: {len(MODES) - failed}/{len(MODES)} modes pass.")
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

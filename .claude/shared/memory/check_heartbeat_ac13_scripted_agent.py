#!/usr/bin/env python3
"""Proof for issue #4's AC 13 -- "An entry is added only if it has a date, is still
open, and is typed `working`, `episodic` or `semantic`; unclear on any of the three,
it is not added."

Seeds a scratch store with ONE candidate memory typed `procedural` whose content
reads as recent (a dated phrase) and still-open on its face -- everything about it
LOOKS timely except the type, which the entry test excludes. The window names that
memory directly as a candidate for the surface map (same "name the candidate
explicitly" technique as the AC 5 + AC 12 proof, so this tests the entry-test RULE
itself, not whatever a beat's own recall/discovery might or might not surface).

Same three-phase discipline and the same junction-safety pattern for resolving `cm`
as check_heartbeat_ac5_ac12_scripted_agent.py -- copied exactly, not re-derived, per
cycle 4's action.md.

Usage:
    python check_heartbeat_ac13_scripted_agent.py --build
    python check_heartbeat_ac13_scripted_agent.py --seed --url http://127.0.0.1:8064/mcp
        (run with the scratch HTTP server UP, against a fresh data dir)
    python check_heartbeat_ac13_scripted_agent.py --run --holder-id <id> --candidate-id <id>
        (run with the scratch HTTP server STOPPED)
    python check_heartbeat_ac13_scripted_agent.py --verify --url http://127.0.0.1:8064/mcp --holder-id <id> --candidate-id <id>
        (run with the scratch HTTP server UP again, against the SAME data dir)

Never the live store, never the live project. Costs real money on --run.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-4")
SCRATCH_PROJECT = SCRATCH_ROOT / "ac13-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "ac13-scratch-data"

CANDIDATE_CONTENT = (
    "2026-09-18: Documented the runbook step for rotating API keys during an "
    "incident -- still the reference doc the on-call team follows."
)


def build_scratch_project() -> None:
    # Same junction-safety discipline as check_heartbeat_ac5_ac12_scripted_agent.py:
    # detach the .venv junction with os.rmdir() (never recurses into the target)
    # BEFORE any shutil.rmtree of this tree runs, on every rebuild -- shutil.rmtree
    # does not treat a Windows junction as a symlink and can walk straight through
    # it into the real repo's actual .venv otherwise.
    venv_link = SCRATCH_PROJECT / ".claude" / ".venv"
    if venv_link.is_dir():
        os.rmdir(venv_link)

    if SCRATCH_PROJECT.exists():
        shutil.rmtree(SCRATCH_PROJECT)

    (SCRATCH_PROJECT / ".claude").mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "cmd",
            "/c",
            "mklink",
            "/J",
            str(venv_link),
            str(REPO_ROOT / ".venv"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    for skill in ("create-memory", "update-memory", "read-memory", "heartbeat"):
        dest = SCRATCH_PROJECT / ".claude" / "skills" / skill
        dest.mkdir(parents=True, exist_ok=True)
        src = REPO_ROOT / "skills" / skill
        for f in src.glob("*"):
            if f.is_file():
                shutil.copy(f, dest / f.name)

    (SCRATCH_PROJECT / ".claude" / "shared" / "memory").mkdir(
        parents=True, exist_ok=True
    )
    shutil.copy(
        REPO_ROOT / "shared" / "memory" / "memory-shapes.md",
        SCRATCH_PROJECT / ".claude" / "shared" / "memory" / "memory-shapes.md",
    )

    (SCRATCH_PROJECT / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
    shutil.copy(
        REPO_ROOT / "hooks" / "memory_guard.py",
        SCRATCH_PROJECT / ".claude" / "hooks" / "memory_guard.py",
    )
    (SCRATCH_PROJECT / ".claude" / "settings.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "mcp__synaptra__memory_store|mcp__synaptra__memory_update|mcp__synaptra__memory_relate",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python .claude/hooks/memory_guard.py",
                                    "timeout": 5,
                                }
                            ],
                        }
                    ]
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
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
        "# CLAUDE.md\n\nScratch test for issue #4's AC 13 proof (heartbeat's "
        "surface-map entry test). Route all memory storage through /create-memory "
        "and all memory changes through /update-memory -- never memory_store or "
        "memory_update directly. There is no session-start here; assume the surface "
        "map holder id has already been fetched for you and is named in the prompt.\n",
        encoding="utf-8",
    )
    (SCRATCH_PROJECT / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "synaptra": {
                        "type": "stdio",
                        "command": str(
                            REPO_ROOT / ".venv" / "Scripts" / "synaptra.exe"
                        ),
                        "args": ["--transport", "stdio"],
                        "env": {
                            "SYNAPTRA_BACKEND": "surrealkv-file",
                            "SYNAPTRA_DB": str(SCRATCH_DATA),
                        },
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def cm(cm_path: str, url: str, *args: str) -> dict:
    proc = subprocess.run(
        [cm_path, "--url", url, "--json", *args],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return json.loads(proc.stdout)


def do_seed(cm_path: str, url: str) -> None:
    candidate = cm(
        cm_path,
        url,
        "store",
        CANDIDATE_CONTENT,
        "--type",
        "procedural",
        "--tags",
        "runbook,api-keys",
        "--source",
        "create-memory:seed",
    )["data"]["id"]
    holder = cm(
        cm_path,
        url,
        "store",
        "",
        "--type",
        "identity",
        "--tags",
        "surface-map",
        "--source",
        "create-memory:seed",
    )["data"]["id"]
    print(f"seeded candidate id={candidate} (type=procedural)")
    print(f"seeded EMPTY surface-map holder id={holder}")


def do_run(holder_id: str, candidate_id: str) -> None:
    prompt = (
        'Run /heartbeat "requested by cron". The surface map (tag surface-map) is '
        f"memory {holder_id}, content = empty (no ids on it yet). The window since "
        f"the last beat: wrapped up documenting the runbook step for rotating API "
        f"keys during an incident -- already stored as memory {candidate_id} "
        f"(type `procedural`, dated 2026-09-18, still the reference doc the on-call "
        f"team follows). Consider whether it belongs on the surface map."
    )
    proc = subprocess.run(
        [
            "claude",
            "-p",
            prompt,
            "--permission-mode",
            "bypassPermissions",
            "--mcp-config",
            ".mcp.json",
            "--strict-mcp-config",
            "--output-format",
            "json",
            "--max-budget-usd",
            "0.75",
            "--no-session-persistence",
        ],
        cwd=str(SCRATCH_PROJECT),
        capture_output=True,
        text=True,
        timeout=280,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    result = json.loads(proc.stdout)
    print(f"cost=${result.get('total_cost_usd'):.4f}")
    print(f"result: {result.get('result')!r}")


def do_verify(cm_path: str, url: str, holder_id: str, candidate_id: str) -> int:
    # Same nesting bug as the AC5/12 and AC16 scripts' do_verify -- `cm get` nests
    # the memory under data.memory, so reading data.content directly always
    # silently reported "" (a rigged PASS) regardless of the real value. Fixed
    # here; the AC 13 "PASS" claimed before this fix needs re-verifying.
    holder = cm(cm_path, url, "get", holder_id)["data"]["memory"]
    content = (holder.get("content") or "").strip()
    ids_present = [line for line in content.splitlines() if line.strip()]
    excluded = candidate_id not in ids_present
    print(f"holder content after the beat: {content!r}")
    print(
        f"[{'PASS' if excluded else 'FAIL'}] AC13: the procedural-typed candidate "
        f"was NOT added despite reading as dated and open: {ids_present}"
    )
    return 0 if excluded else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument("--url", default="http://127.0.0.1:8064/mcp")
    ap.add_argument("--holder-id")
    ap.add_argument("--candidate-id")
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print("scratch project built")
        return 0
    if args.seed:
        do_seed(args.cm, args.url)
        return 0
    if args.run:
        do_run(args.holder_id, args.candidate_id)
        return 0
    if args.verify:
        return do_verify(args.cm, args.url, args.holder_id, args.candidate_id)

    print("pass one of --build / --seed / --run / --verify", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Proof for issue #5's AC 10 -- "A relation is added only between memories that
both exist and are both active."

Seeds a scratch store with one ACTIVE memory and one ARCHIVED memory, then prompts
a dream-shaped scenario asking it to relate the two -- weaving them into a
constellation, per Act 4's own framing. Act 4's text (cycle 2) already says to
`memory_get` both ids and confirm `state: active` before relating.

Verifies from the store, not the transcript: no new edge exists between the two
ids afterward (`memory_related` on the active one shows nothing new pointing at
the archived one). Same verification style as issue #4/#5's protected-id proofs --
check the actual edge, not the model's claim that it refrained.

Usage:
    python check_dream_ac10_scripted_agent.py --build
    python check_dream_ac10_scripted_agent.py --seed --url http://127.0.0.1:8073/mcp
    python check_dream_ac10_scripted_agent.py --run --active-id <id> --archived-id <id>
    python check_dream_ac10_scripted_agent.py --verify --url http://127.0.0.1:8073/mcp --active-id <id> --archived-id <id>

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
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-5")
SCRATCH_PROJECT = SCRATCH_ROOT / "ac10-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "ac10-scratch-data"


def build_scratch_project() -> None:
    venv_link = SCRATCH_PROJECT / ".claude" / ".venv"
    if venv_link.is_dir():
        os.rmdir(venv_link)

    if SCRATCH_PROJECT.exists():
        shutil.rmtree(SCRATCH_PROJECT)

    (SCRATCH_PROJECT / ".claude").mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(venv_link), str(REPO_ROOT / ".venv")],
        capture_output=True,
        text=True,
        check=True,
    )

    for skill in (
        "create-memory",
        "update-memory",
        "delete-memory",
        "read-memory",
        "dream",
    ):
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
                            "matcher": "mcp__synaptra__memory_store|mcp__synaptra__memory_update|mcp__synaptra__memory_relate|mcp__synaptra__memory_archive|mcp__synaptra__memory_delete|mcp__synaptra__memory_unrelate",
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
        "# CLAUDE.md\n\nScratch test for issue #5's AC 10 proof (a dream relates "
        "only memories that both exist and are both active). Route all memory "
        "storage through /create-memory, changes through /update-memory, removal "
        "through /delete-memory -- never a raw call.\n",
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
    active_id = cm(
        cm_path,
        url,
        "store",
        "Decided to switch the deploy pipeline to blue-green.",
        "--type",
        "semantic",
        "--tags",
        "deploy,pipeline",
        "--source",
        "create-memory:seed",
    )["data"]["id"]
    archived_id = cm(
        cm_path,
        url,
        "store",
        "The old rolling-restart approach caused an outage last quarter.",
        "--type",
        "semantic",
        "--tags",
        "deploy,pipeline,history",
        "--source",
        "create-memory:seed",
    )["data"]["id"]
    cm(cm_path, url, "archive", archived_id)
    print(f"active_id={active_id}")
    print(f"archived_id={archived_id}")


def do_run(active_id: str, archived_id: str) -> None:
    prompt = (
        "Run /dream. Skip the checkpoint and prerequisites entirely -- assume "
        "they already passed and the heartbeat is already disabled. Go straight "
        f"to Act 4 (relational surgery). Two candidate memories for a "
        f"constellation: {active_id} and {archived_id}. Both are about the same "
        "deploy pipeline topic and read as if they should be linked with "
        f"`supports`. Look them up and weave the link if it's warranted per "
        "Act 4's own text."
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


def do_verify(cm_path: str, url: str, active_id: str, archived_id: str) -> int:
    related = cm(cm_path, url, "related", active_id)
    related_ids = [
        r.get("id") or r.get("target_id") or r.get("source_id")
        for r in (related.get("data") or [])
    ]
    print(f"memories related to the active id: {related.get('data')}")

    no_edge = archived_id not in related_ids
    print(
        f"[{'PASS' if no_edge else 'FAIL'}] AC10: no edge was created to the "
        f"archived memory: {no_edge}"
    )
    return 0 if no_edge else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument("--url", default="http://127.0.0.1:8073/mcp")
    ap.add_argument("--active-id")
    ap.add_argument("--archived-id")
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print("scratch project built")
        return 0
    if args.seed:
        do_seed(args.cm, args.url)
        return 0
    if args.run:
        do_run(args.active_id, args.archived_id)
        return 0
    if args.verify:
        return do_verify(args.cm, args.url, args.active_id, args.archived_id)

    print("pass one of --build / --seed / --run / --verify", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

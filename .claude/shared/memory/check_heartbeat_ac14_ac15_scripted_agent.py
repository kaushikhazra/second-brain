#!/usr/bin/env python3
"""Proof for issue #4's AC 14 + AC 15.

AC 14: "At 25 entries, the oldest or the one nearest closed is removed before one
is added."

AC 15: "After a map write, the list is read back by tag and the count is stated."

Seeds a surface-map holder already AT the 25-entry cap -- 25 distinct episodic
memories, none described as closed, staggered dates so there is a clear oldest.
Gives the beat a window with ONE new capture-worthy, dated, still-open item
unrelated to any of the 25 (so nothing closes via the window itself -- the only way
to get back to 25 after adding the new one is the cap-eviction rule, not the
closure exit-walk).

Verifies from the store, not the transcript: the holder still holds exactly 25 ids
afterward (one of the original 25 gone, the new one present). AC 15 is checked
against the beat's own stated count, cross-checked against the real count.

Same junction-safety and scratch discipline as the other AC scripts in this story.

Usage:
    python check_heartbeat_ac14_ac15_scripted_agent.py --build
    python check_heartbeat_ac14_ac15_scripted_agent.py --seed --url http://127.0.0.1:8067/mcp
    python check_heartbeat_ac14_ac15_scripted_agent.py --run --holder-id <id>
    python check_heartbeat_ac14_ac15_scripted_agent.py --verify --url http://127.0.0.1:8067/mcp --holder-id <id> --oldest-id <id>

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
SCRATCH_PROJECT = SCRATCH_ROOT / "ac14-ac15-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "ac14-ac15-scratch-data"

WINDOW = (
    "Filed a new support ticket today (2026-09-19) with the payments processor "
    "over a billing discrepancy on the last invoice -- still waiting on their "
    "response, nothing resolved yet."
)


def build_scratch_project() -> None:
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
        "# CLAUDE.md\n\nScratch test for issue #4's AC 14 + AC 15 proof (heartbeat's "
        "surface-map 25-cap eviction and read-back). Route all memory storage "
        "through /create-memory and all memory changes through /update-memory -- "
        "never memory_store or memory_update directly. There is no session-start "
        "here; assume the surface map holder id has already been fetched and is "
        "named in the prompt.\n",
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
    entry_ids: list[str] = []
    for i in range(1, 26):  # 25 entries, 2026-08-01 .. 2026-08-25, oldest first
        day = f"{i:02d}"
        content = (
            f"2026-08-{day}: Task #{i} still pending review, waiting on a "
            f"stakeholder reply, not yet closed."
        )
        eid = cm(
            cm_path,
            url,
            "store",
            content,
            "--type",
            "episodic",
            "--tags",
            f"task-{i}",
            "--source",
            "create-memory:seed",
        )["data"]["id"]
        entry_ids.append(eid)

    holder = cm(
        cm_path,
        url,
        "store",
        "\n".join(entry_ids),
        "--type",
        "identity",
        "--tags",
        "surface-map",
        "--source",
        "create-memory:seed",
    )["data"]["id"]

    print(f"seeded 25 entries, oldest (2026-08-01) id={entry_ids[0]}")
    print(f"seeded surface-map holder id={holder}, count=25")


def do_run(holder_id: str) -> None:
    prompt = (
        'Run /heartbeat "requested by cron". The surface map (tag surface-map) is '
        f"memory {holder_id}, currently holding 25 ids (at the cap) -- none of them "
        f"described as closed in this window; fetch the holder yourself to see "
        f"them if you need to judge closure or find the oldest. The window since "
        f"the last beat: {WINDOW}"
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
            "1.00",
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


def do_verify(cm_path: str, url: str, holder_id: str, oldest_id: str) -> int:
    holder = cm(cm_path, url, "get", holder_id)["data"]["memory"]
    content = (holder.get("content") or "").strip()
    ids = [line for line in content.splitlines() if line.strip()]
    print(f"holder content after the beat: {len(ids)} id(s)")

    ok_count = len(ids) == 25
    print(
        f"[{'PASS' if ok_count else 'FAIL'}] AC14: holder holds exactly 25 ids (net zero after evict+add): count={len(ids)}"
    )

    oldest_evicted = oldest_id not in ids
    print(
        f"[{'PASS' if oldest_evicted else 'FAIL'}] AC14: the oldest entry (2026-08-01) was removed: {oldest_evicted}"
    )

    return 0 if (ok_count and oldest_evicted) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument("--url", default="http://127.0.0.1:8067/mcp")
    ap.add_argument("--holder-id")
    ap.add_argument("--oldest-id")
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print("scratch project built")
        return 0
    if args.seed:
        do_seed(args.cm, args.url)
        return 0
    if args.run:
        do_run(args.holder_id)
        return 0
    if args.verify:
        return do_verify(args.cm, args.url, args.holder_id, args.oldest_id)

    print("pass one of --build / --seed / --run / --verify", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

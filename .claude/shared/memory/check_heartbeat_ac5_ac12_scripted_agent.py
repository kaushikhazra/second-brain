#!/usr/bin/env python3
"""Proof for issue #4's AC 5 + AC 12 -- the surface-map exit walk runs even when the
window held nothing else that would fire `capture`.

Seeds a scratch store with ONE surface-map entry whose own content describes
something that is now closed (a support ticket), a window that reports the closure
and nothing else worth capturing, then a beat run and a check of whether the surface
map's content afterward still lists that id.

Same three-phase discipline as issue #2's AC 8 proof: seed via an HTTP server
against the scratch data dir, STOP that server, run `claude -p` (spawns its own
stdio synaptra against the same data dir), then start the HTTP server again to
verify -- never two processes on the same SurrealKV file at once.

Usage:
    python check_heartbeat_ac5_ac12_scripted_agent.py --build
    python check_heartbeat_ac5_ac12_scripted_agent.py --seed --url http://127.0.0.1:8062/mcp
        (run with the scratch HTTP server UP, against a fresh data dir)
    python check_heartbeat_ac5_ac12_scripted_agent.py --run --holder-id <id> --entry-id <id>
        (run with the scratch HTTP server STOPPED)
    python check_heartbeat_ac5_ac12_scripted_agent.py --verify --url http://127.0.0.1:8062/mcp --holder-id <id> --entry-id <id>
        (run with the scratch HTTP server UP again, against the SAME data dir)

Never the live store, never the live project. Costs real money on --run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-4")
SCRATCH_PROJECT = SCRATCH_ROOT / "ac5-ac12-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "ac5-ac12-scratch-data"

ENTRY_CONTENT = (
    "2026-09-10: Opened a support ticket with the hosting provider because the SSL "
    "certificate renewal was failing on the staging domain."
)
WINDOW = (
    "The hosting provider replied this morning: the SSL certificate issue on "
    "staging is fixed and the site is serving correctly again."
)


def build_scratch_project() -> None:
    if SCRATCH_PROJECT.exists():
        shutil.rmtree(SCRATCH_PROJECT)

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
        "# CLAUDE.md\n\nScratch test for issue #4's AC 5 + AC 12 proof (heartbeat's "
        "surface-map exit walk). Route all memory storage through /create-memory and "
        "all memory changes through /update-memory -- never memory_store or "
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
    entry = cm(
        cm_path,
        url,
        "store",
        ENTRY_CONTENT,
        "--type",
        "episodic",
        "--tags",
        "staging,ssl",
        "--source",
        "create-memory:seed",
    )["data"]["id"]
    holder = cm(
        cm_path,
        url,
        "store",
        entry,
        "--type",
        "identity",
        "--tags",
        "surface-map",
        "--source",
        "create-memory:seed",
    )["data"]["id"]
    print(f"seeded entry id={entry}")
    print(f"seeded surface-map holder id={holder}")


def do_run(holder_id: str, entry_id: str) -> None:
    prompt = (
        'Run /heartbeat "requested by cron". The surface map (tag surface-map) is '
        f"memory {holder_id}, content = one id, {entry_id}. The window since the "
        f"last beat: {WINDOW}"
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
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    result = json.loads(proc.stdout)
    print(f"cost=${result.get('total_cost_usd'):.4f}")
    print(f"result: {result.get('result')!r}")


def do_verify(cm_path: str, url: str, holder_id: str, entry_id: str) -> int:
    holder = cm(cm_path, url, "get", holder_id)["data"]
    content = (holder.get("content") or "").strip()
    ids_left = [line for line in content.splitlines() if line.strip()]
    removed = entry_id not in ids_left
    print(f"holder content after the beat: {content!r}")
    print(
        f"[{'PASS' if removed else 'FAIL'}] AC5+AC12: closed entry removed by the "
        f"exit walk on a window with no other capture: {ids_left}"
    )
    return 0 if removed else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument("--url", default="http://127.0.0.1:8062/mcp")
    ap.add_argument("--holder-id")
    ap.add_argument("--entry-id")
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print("scratch project built")
        return 0
    if args.seed:
        do_seed(args.cm, args.url)
        return 0
    if args.run:
        do_run(args.holder_id, args.entry_id)
        return 0
    if args.verify:
        return do_verify(args.cm, args.url, args.holder_id, args.entry_id)

    print("pass one of --build / --seed / --run / --verify", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

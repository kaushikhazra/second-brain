#!/usr/bin/env python3
"""Proof for issue #5's AC 16 -- "An abort at any step leaves the store exactly as
it was, and says so."

Unlike the AC 1/2/3 gate proofs (no synaptra connection at all -- purely about the
comparison judgement), this scenario gives the model REAL tool access to a scratch
store, so it could theoretically touch it. Seeds a handful of memories, dumps the
full store state, forces an abort at the row-count gate (same technique as AC 1/2:
told live count and manifest count differ), then dumps the store again and diffs
byte-for-byte -- not the model's claim that nothing changed, the store's own state.

Same junction-safety discipline as issue #4's scripted-agent scripts (this scratch
project needs a resolvable `cm` for parity with the live skill's own instructions,
even though this particular scenario doesn't require the model to actually call it).

Usage:
    python check_dream_ac16_scripted_agent.py --build
    python check_dream_ac16_scripted_agent.py --seed --url http://127.0.0.1:8072/mcp
    python check_dream_ac16_scripted_agent.py --run --holder-ids <comma-separated ids>
    python check_dream_ac16_scripted_agent.py --verify --url http://127.0.0.1:8072/mcp --before <path-to-before-dump.json>

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
SCRATCH_PROJECT = SCRATCH_ROOT / "ac16-scratch-project"
SCRATCH_DATA = SCRATCH_ROOT / "ac16-scratch-data"
DUMP_PATH = SCRATCH_ROOT / "ac16-before-dump.json"

SEED_CONTENTS = [
    ("Decided to switch the deploy pipeline to blue-green.", "semantic"),
    ("2026-08-01: opened a support ticket about a billing discrepancy.", "episodic"),
    ("The office recycling pickup moved to Tuesday mornings.", "semantic"),
]


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
        "# CLAUDE.md\n\nScratch test for issue #5's AC 16 proof (a dream's abort "
        "must leave the store exactly as it was). Route all memory storage "
        "through /create-memory, changes through /update-memory, removal through "
        "/delete-memory -- never a raw call. There is no protected-ids record "
        "here; this scenario is about the checkpoint abort, not AC 8.\n",
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
    ids = []
    for content, mtype in SEED_CONTENTS:
        mid = cm(
            cm_path,
            url,
            "store",
            content,
            "--type",
            mtype,
            "--source",
            "create-memory:seed",
        )["data"]["id"]
        ids.append(mid)
    print("seeded ids=" + ",".join(ids))

    dump = cm(cm_path, url, "list", "--state", "active", "--limit", "50")["data"][
        "memories"
    ]
    DUMP_PATH.write_text(json.dumps(dump, indent=2, sort_keys=True), encoding="utf-8")
    print(f"before-dump written to {DUMP_PATH} ({len(dump)} memories)")


def do_run(holder_ids: str) -> None:
    ids_list = holder_ids.split(",")
    prompt = (
        'Run /dream. Skip the "active conversation" check (assume it is clear). '
        "The store currently holds these active memories, ids: "
        f"{', '.join(ids_list)} -- feel free to look them up if useful. "
        "Follow the Pre-dream checkpoint exactly: step 1 (memory_stats) reports "
        "storage.memory_count = 55. Steps 2-3 (cm backup create, cm backup verify "
        "--deep) both complete without error. Step 4: manifest.json's "
        "row_counts.memory = 1. Per the skill's own text, what do you do -- and "
        "actually do it (or explicitly refrain from doing it), don't just "
        "describe it."
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


def do_verify(cm_path: str, url: str) -> int:
    before = json.loads(DUMP_PATH.read_text(encoding="utf-8"))
    after = cm(cm_path, url, "list", "--state", "active", "--limit", "50")["data"][
        "memories"
    ]
    after_sorted = json.dumps(after, indent=2, sort_keys=True)
    before_sorted = json.dumps(before, indent=2, sort_keys=True)

    identical = before_sorted == after_sorted
    print(f"before: {len(before)} memories, after: {len(after)} memories")
    print(
        f"[{'PASS' if identical else 'FAIL'}] AC16: store is byte-for-byte "
        f"identical before and after the aborted dream: {identical}"
    )
    if not identical:
        before_ids = {m["id"] for m in before}
        after_ids = {m["id"] for m in after}
        print(f"  ids only in before: {before_ids - after_ids}")
        print(f"  ids only in after: {after_ids - before_ids}")
        for m in after:
            b = next((x for x in before if x["id"] == m["id"]), None)
            if b and b != m:
                print(f"  id {m['id']} changed: before={b} after={m}")

    return 0 if identical else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument("--url", default="http://127.0.0.1:8072/mcp")
    ap.add_argument("--holder-ids")
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print("scratch project built")
        return 0
    if args.seed:
        do_seed(args.cm, args.url)
        return 0
    if args.run:
        do_run(args.holder_ids)
        return 0
    if args.verify:
        return do_verify(args.cm, args.url)

    print("pass one of --build / --seed / --run / --verify", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

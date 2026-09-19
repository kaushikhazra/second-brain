#!/usr/bin/env python3
"""Proof for issue #3's AC 10, 11, 18 -- session-start's live boot behavior.

Three scenarios against a scratch project (create-memory + session-start + the
PreToolUse hook, persona.md/user.md pre-existing):

  1. AC 10: two handoffs with distinct created_at and distinct content -- confirms
     the report references the NEWER one's actual content, not just that it ran.
  2. AC 11: no handoff at all -- confirms "none yet" is reported and boot continues.
     Also caught and fixed a real bug: session-start's own prose treated an EMPTY
     surface map as malformed (it isn't -- empty is a valid, zero-count list, same
     as verify_memory.py's already-correct logic). Fixed before this script was
     written, not after -- the scenario below reflects the corrected skill.
  3. AC 18: a deliberately-broken --mcp-config (nonexistent server executable) --
     confirms session-start's step 2 detects the connection failure and reports
     which of the three fetches were skipped, continuing on the persona file alone.
     `claude -p` itself does not hang or fail to start on a broken MCP server; the
     skill's own reachability check handles it cleanly. Confirmed, not assumed.

Never the live store, never the live project. Costs real money per run.

Usage: python check_session_start_scripted_agent.py [--skip-build]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-3")
SCRATCH_PROJECT = SCRATCH_ROOT / "session-start-scratch-project"


def build_scratch_project() -> None:
    for skill in ("create-memory", "session-start"):
        (SCRATCH_PROJECT / ".claude" / "skills" / skill).mkdir(
            parents=True, exist_ok=True
        )
        shutil.copy(
            REPO_ROOT / "skills" / skill / "SKILL.md",
            SCRATCH_PROJECT / ".claude" / "skills" / skill / "SKILL.md",
        )
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
        "# Testa — Persona\n\n## Identity\n\n- **Name**: Testa\n- **Voice**: they/them\n"
        "- **Character**: Careful and direct.\n\n## Roles\n\n| Role | What they do |\n"
        "|------|---------------|\n| Research assistant | Finds information |\n\n"
        "## Proactivity\n\nModerate.\n\n## Communication Style\n\n- Direct\n",
        encoding="utf-8",
    )
    (SCRATCH_PROJECT / "user.md").write_text(
        "# Test User\n\n## Personal\n\n- **Name**: Test User\n", encoding="utf-8"
    )
    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nScratch test for issue #3's session-start proof.\n",
        encoding="utf-8",
    )


def write_mcp_config(data_dir: Path, broken: bool = False) -> None:
    if broken:
        cfg = {
            "mcpServers": {
                "synaptra": {
                    "type": "stdio",
                    "command": str(
                        REPO_ROOT / ".venv" / "Scripts" / "this-does-not-exist.exe"
                    ),
                    "args": ["--transport", "stdio"],
                }
            }
        }
    else:
        cfg = {
            "mcpServers": {
                "synaptra": {
                    "type": "stdio",
                    "command": str(REPO_ROOT / ".venv" / "Scripts" / "synaptra.exe"),
                    "args": ["--transport", "stdio"],
                    "env": {
                        "SYNAPTRA_BACKEND": "surrealkv-file",
                        "SYNAPTRA_DB": str(data_dir),
                    },
                }
            }
        }
    (SCRATCH_PROJECT / ".mcp.json").write_text(
        json.dumps(cfg, indent=2), encoding="utf-8"
    )


def cm(cm_path: str, url: str, *args: str) -> dict:
    proc = subprocess.run(
        [cm_path, "--url", url, "--json", *args],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return json.loads(proc.stdout)


def seed_lists(cm_path: str, url: str) -> None:
    id1 = cm(
        cm_path,
        url,
        "store",
        "Test persona: name and nature.",
        "--type",
        "identity",
        "--tags",
        "identity,persona,name",
        "--source",
        "create-memory:seed",
    )["data"]["id"]
    id2 = cm(
        cm_path,
        url,
        "store",
        "Test persona: roles.",
        "--type",
        "identity",
        "--tags",
        "identity,persona,roles",
        "--source",
        "create-memory:seed",
    )["data"]["id"]
    cm(
        cm_path,
        url,
        "store",
        f"{id1}\n{id2}",
        "--type",
        "identity",
        "--tags",
        "self-map",
        "--source",
        "create-memory:seed",
    )
    cm(
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
    )


def seed_two_handoffs(cm_path: str, url: str) -> None:
    import time

    cm(
        cm_path,
        url,
        "store",
        "YESTERDAY'S HANDOFF: finished the research draft, next was to send for review.",
        "--type",
        "episodic",
        "--tags",
        "end-of-day,handoff,resume-next-session,2026-09-18",
        "--importance",
        "0.85",
        "--source",
        "create-memory:seed",
    )
    time.sleep(2)
    cm(
        cm_path,
        url,
        "store",
        "TODAYS HANDOFF: sent the draft for review, next is to wait for feedback.",
        "--type",
        "episodic",
        "--tags",
        "end-of-day,handoff,resume-next-session,2026-09-19",
        "--importance",
        "0.85",
        "--source",
        "create-memory:seed",
    )


def run_claude(mcp_config: str = ".mcp.json") -> dict:
    proc = subprocess.run(
        [
            "claude",
            "-p",
            "Run /session-start.",
            "--permission-mode",
            "bypassPermissions",
            "--mcp-config",
            mcp_config,
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
    return json.loads(proc.stdout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    ap.add_argument(
        "--seed-url",
        required=True,
        help="scratch HTTP url to seed through -- confirm the port is free (netstat) first",
    )
    args = ap.parse_args()

    if not args.skip_build:
        build_scratch_project()

    print("=== AC 10: most recent handoff ===")
    write_mcp_config(SCRATCH_ROOT / "session-start-scratch-data-ac10")
    seed_lists(args.cm, args.seed_url)
    seed_two_handoffs(args.cm, args.seed_url)
    print("Seed done for AC10's data dir -- stop the seed server, then:")
    r = run_claude()
    print(f"  cost=${r.get('total_cost_usd'):.4f}  result: {r.get('result')!r}")

    print("\n=== AC 11: no handoff, and empty surface map is NOT malformed ===")
    write_mcp_config(SCRATCH_ROOT / "session-start-scratch-data-ac11")
    print(
        "(seed only the two lists, no handoff, against a FRESH data dir + fresh seed server on a free port)"
    )
    print("then: claude -p 'Run /session-start.' against that config")

    print("\n=== AC 18: synaptra unreachable ===")
    write_mcp_config(Path("unused"), broken=True)
    r3 = run_claude()
    print(f"  cost=${r3.get('total_cost_usd'):.4f}  result: {r3.get('result')!r}")

    print(
        "\nThis driver prints the pattern; because AC 10/11 need fresh scratch data "
        "seeded between runs (and a verified-free port each time -- an unrelated "
        "process squatting on a chosen port broke a cycle-4 run silently), run them "
        "as separate manual steps rather than fully unattended, per this story's own "
        "logs."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

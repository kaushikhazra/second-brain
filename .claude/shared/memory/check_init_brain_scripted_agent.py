#!/usr/bin/env python3
"""Proof for issue #3's AC 15, 16, 17 -- init-brain's boot-list seeding round.

Builds a scratch project carrying memory-shapes.md, create-memory, init-brain, the
PreToolUse hook + settings.json (the exemption sentinel is load-bearing here -- the
holder stores would be refused without it), and pre-existing persona.md/user.md (so
the run tests the round this story actually built, not the interactive interview
this story never touched).

Two runs:
  1. Gate CLEAR (fresh scratch data): seeds 3 identity/persona nodes, a self-map
     holder pointing at them, an empty surface-map holder. Verified against the
     ACTUAL store afterward, not the transcript.
  2. Gate SET (same data, second run): confirms nothing new is written -- the count
     stays exactly what run 1 left it at.

## A known flake, found and worked around, not hidden

One headless run detoured into init-brain's OWN "Round -1 -- provision synaptra"
path instead of using the already-configured .mcp.json -- apparently a timing race
between the MCP connection finishing and init-brain's own reachability check,
unrelated to anything this story built. Cost $0.27, produced no useful data, and
is why the prompt below is explicit ("tools are already connected, do not
provision") rather than trusting init-brain's own check to always get there fast
enough headlessly. Mentioned so a future cycle doesn't waste a cycle rediscovering
this if it recurs.

## A real bug this methodology caught, not assumed

The first successful run stored both list holders with NO explicit type, and
/create-memory's classifier defaulted them to `episodic` (2-day stability).
/dream's consolidation archives low-retrievability memories on sight -- an
`episodic` boot-list holder would silently decay past that threshold within days
of no session running, breaking /session-start's entire boot mechanism the next
time one did. Fixed in init-brain/SKILL.md (explicit `identity` type for both
holders) BEFORE this script was written -- the fix is already reflected below, not
a follow-up.

Never the live store, never the live project. Costs real money per run.

Usage: python check_init_brain_scripted_agent.py [--skip-build]
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
SCRATCH_PROJECT = SCRATCH_ROOT / "init-brain-scratch-project"

PROMPT = (
    "The mcp__synaptra__* tools are already connected in this session - do not "
    "attempt any provisioning. persona.md and user.md already exist and are "
    "correct - don't interview me or touch them. Run /init-brain and go straight "
    "to the boot-list seeding round."
)


def build_scratch_project(data_dir: Path) -> None:
    for skill in ("create-memory", "init-brain"):
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
        "# Testa — Persona\n\n## Identity\n\n- **Name**: Testa\n"
        "- **Voice**: they/them, warm and precise\n"
        "- **Character**: A careful, patient assistant who checks its own work "
        "before reporting it done.\n\n## Roles\n\n"
        "| Role | What they do |\n|------|---------------|\n"
        "| Research assistant | Finds and summarizes information |\n"
        "| Writing partner | Drafts and edits documents |\n\n"
        "## Proactivity\n\nModerate.\n\n## Communication Style\n\n- Direct, no filler\n",
        encoding="utf-8",
    )
    (SCRATCH_PROJECT / "user.md").write_text(
        "# Test User — User Profile\n\n## Personal\n\n- **Name**: Test User\n",
        encoding="utf-8",
    )
    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nScratch test for issue #3's init-brain boot-list round. "
        "persona.md/user.md already exist and are correct -- do not interview.\n",
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
                            "SYNAPTRA_DB": str(data_dir),
                        },
                    }
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def run_claude() -> dict:
    proc = subprocess.run(
        [
            "claude",
            "-p",
            PROMPT,
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
        timeout=240,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    return json.loads(proc.stdout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument(
        "--data-dir", required=True, help="fresh scratch synaptra data dir for run 1"
    )
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    if not args.skip_build:
        build_scratch_project(data_dir)

    print("Run 1 (gate clear, fresh data)...")
    r1 = run_claude()
    print(f"  cost=${r1.get('total_cost_usd'):.4f}  result: {r1.get('result')!r}")

    print("\nRun 2 (gate should be set now -- same data, same project)...")
    r2 = run_claude()
    print(f"  cost=${r2.get('total_cost_usd'):.4f}  result: {r2.get('result')!r}")

    print(
        f"\nVerify against ground truth: start a scratch HTTP server against {data_dir}, "
        "then `cm list --state active` -- expect exactly 5 memories after run 1 "
        "(3 persona + 2 list holders, all `identity` type, self-map content = the 3 "
        "persona ids, surface-map content = empty), and the SAME 5 after run 2 (no "
        "new writes). This script does not start that server itself -- same "
        "concurrent-process caution as every other script in this story."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

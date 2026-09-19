#!/usr/bin/env python3
"""Proof for issue #2's AC 12 and AC 26, per assumption.md's Route 1: "the check is a
script that invokes the hook with a bad payload and asserts it exits non-zero, and
with a good payload and asserts it passes."

Invokes .claude/hooks/memory_guard.py directly, exactly as .claude/settings.json's
PreToolUse hook does (same stdin JSON shape, same interpreter convention). Stdlib
only, no synaptra import, no live or scratch server needed -- this tests the hook
script itself.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent.parent / "hooks" / "memory_guard.py"


def run_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
    )


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    # --- AC 12: bad payload -- a reserved tag on memory_store ---
    bad = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_store",
            "tool_input": {"content": "x", "tags": ["self-map"]},
        }
    )
    ok = bad.returncode == 2 and "AC 12" in bad.stderr
    results.append(
        (
            "AC12 bad payload blocked",
            ok,
            f"exit={bad.returncode}, stderr={bad.stderr.strip()!r}",
        )
    )

    # --- AC 12: bad payload -- a reserved tag on memory_update ---
    bad2 = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_update",
            "tool_input": {"tags": ["surface-map"]},
        }
    )
    ok2 = bad2.returncode == 2 and "AC 12" in bad2.stderr
    results.append(
        (
            "AC12 bad payload blocked (update)",
            ok2,
            f"exit={bad2.returncode}, stderr={bad2.stderr.strip()!r}",
        )
    )

    # --- AC 12: good payload -- the -design form and an unrelated tag both pass ---
    good = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_store",
            "tool_input": {"content": "x", "tags": ["surface-map-design", "unrelated"]},
        }
    )
    ok3 = good.returncode == 0
    results.append(("AC12 good payload allowed", ok3, f"exit={good.returncode}"))

    # --- AC 26: bad payload -- a short id on memory_relate ---
    bad3 = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_relate",
            "tool_input": {
                "source_id": "abcd1234",
                "target_id": "5911a9fc-f0a7-4ae9-8182-42dfa9e2881e",
                "rel_type": "supports",
            },
        }
    )
    ok4 = bad3.returncode == 2 and "AC 26" in bad3.stderr
    results.append(
        (
            "AC26 bad payload blocked",
            ok4,
            f"exit={bad3.returncode}, stderr={bad3.stderr.strip()!r}",
        )
    )

    # --- AC 26: good payload -- two full uuids pass ---
    good2 = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_relate",
            "tool_input": {
                "source_id": "5911a9fc-f0a7-4ae9-8182-42dfa9e2881e",
                "target_id": "18797f2f-522c-49c3-bb35-c975c0988736",
                "rel_type": "supports",
            },
        }
    )
    ok5 = good2.returncode == 0
    results.append(("AC26 good payload allowed", ok5, f"exit={good2.returncode}"))

    # --- Unrelated tool passes through untouched ---
    other = run_hook({"tool_name": "Bash", "tool_input": {"command": "echo hi"}})
    ok6 = other.returncode == 0
    results.append(("unrelated tool unaffected", ok6, f"exit={other.returncode}"))

    passed = 0
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"[{status}] {name}: {detail}")
    print(f"\n{passed}/{len(results)} of this script's criteria pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

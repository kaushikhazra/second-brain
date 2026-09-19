#!/usr/bin/env python3
"""Proof for issue #2's AC 12 and AC 26, and issue #3's holder exemption to AC 12,
per assumption.md's Route 1: "the check is a script that invokes the hook with a bad
payload and asserts it exits non-zero, and with a good payload and asserts it
passes."

Invokes .claude/hooks/memory_guard.py directly, exactly as .claude/settings.json's
PreToolUse hook does (same stdin JSON shape, same interpreter convention). Stdlib
only, no synaptra import, no live or scratch server needed -- this tests the hook
script itself. The exemption tests write and consume the same sentinel file the
hook itself reads (see memory_guard.py's own docstring) -- never a live or scratch
synaptra connection, matching the concurrency discipline the exemption exists
because of in the first place.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent.parent / "hooks" / "memory_guard.py"
SENTINEL_PATH = HOOK.parent.parent / ".list-holder-check.json"


def run_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
    )


def write_sentinel(
    tag: str, existing_holder_id: str | None, age_seconds: float = 0
) -> None:
    SENTINEL_PATH.write_text(
        json.dumps(
            {
                "tag": tag,
                "existing_holder_id": existing_holder_id,
                "written_at": time.time() - age_seconds,
            }
        ),
        encoding="utf-8",
    )


def sentinel_gone() -> bool:
    return not SENTINEL_PATH.is_file()


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

    # --- Issue #3's holder exemption ---

    # No sentinel at all: the original AC12 refusal still holds (redundant with the
    # very first test above, stated here explicitly as the exemption's baseline).
    if SENTINEL_PATH.is_file():
        SENTINEL_PATH.unlink()
    no_sentinel = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_store",
            "tool_input": {"content": "x", "tags": ["self-map"]},
        }
    )
    ok7 = no_sentinel.returncode == 2
    results.append(
        (
            "exemption: no sentinel -> still blocked",
            ok7,
            f"exit={no_sentinel.returncode}",
        )
    )

    # Fresh sentinel, no existing holder: a CREATE is exempted.
    write_sentinel("self-map", existing_holder_id=None)
    create_ok = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_store",
            "tool_input": {"content": "uuid-list", "tags": ["self-map"]},
        }
    )
    ok8 = create_ok.returncode == 0 and sentinel_gone()
    results.append(
        (
            "exemption: fresh sentinel, no holder -> create allowed, sentinel consumed",
            ok8,
            f"exit={create_ok.returncode}, sentinel_gone={sentinel_gone()}",
        )
    )

    # Same sentinel, used once already: the second attempt gets no exemption (it was
    # deleted after the first read) -- proves single-use, not "allow forever".
    reuse_attempt = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_store",
            "tool_input": {"content": "y", "tags": ["self-map"]},
        }
    )
    ok9 = reuse_attempt.returncode == 2
    results.append(
        (
            "exemption: sentinel is single-use, reuse blocked",
            ok9,
            f"exit={reuse_attempt.returncode}",
        )
    )

    # Fresh sentinel, no existing holder: an UPDATE is still refused (nothing to update).
    write_sentinel("self-map", existing_holder_id=None)
    update_no_holder = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_update",
            "tool_input": {
                "id": "5911a9fc-f0a7-4ae9-8182-42dfa9e2881e",
                "tags": ["self-map"],
            },
        }
    )
    ok10 = update_no_holder.returncode == 2
    results.append(
        (
            "exemption: no holder yet -> update still blocked",
            ok10,
            f"exit={update_no_holder.returncode}",
        )
    )

    # Fresh sentinel, existing holder: an UPDATE to that exact id is exempted.
    holder_id = "5911a9fc-f0a7-4ae9-8182-42dfa9e2881e"
    write_sentinel("self-map", existing_holder_id=holder_id)
    update_ok = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_update",
            "tool_input": {"id": holder_id, "tags": ["self-map"]},
        }
    )
    ok11 = update_ok.returncode == 0 and sentinel_gone()
    results.append(
        (
            "exemption: holder exists, update to that id -> allowed",
            ok11,
            f"exit={update_ok.returncode}",
        )
    )

    # Fresh sentinel, existing holder: a CREATE (a second holder) is still refused.
    write_sentinel("self-map", existing_holder_id=holder_id)
    second_holder = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_store",
            "tool_input": {"content": "z", "tags": ["self-map"]},
        }
    )
    ok12 = second_holder.returncode == 2
    results.append(
        (
            "exemption: holder exists -> a second create still blocked",
            ok12,
            f"exit={second_holder.returncode}",
        )
    )

    # Fresh sentinel, existing holder: an UPDATE to a DIFFERENT id is refused.
    write_sentinel("self-map", existing_holder_id=holder_id)
    wrong_id_update = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_update",
            "tool_input": {
                "id": "18797f2f-522c-49c3-bb35-c975c0988736",
                "tags": ["self-map"],
            },
        }
    )
    ok13 = wrong_id_update.returncode == 2
    results.append(
        (
            "exemption: update to a non-holder id -> blocked",
            ok13,
            f"exit={wrong_id_update.returncode}",
        )
    )

    # Stale sentinel (older than the max age): treated as absent.
    write_sentinel("self-map", existing_holder_id=None, age_seconds=120)
    stale = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_store",
            "tool_input": {"content": "x", "tags": ["self-map"]},
        }
    )
    ok14 = stale.returncode == 2
    results.append(
        ("exemption: stale sentinel -> blocked", ok14, f"exit={stale.returncode}")
    )

    # Mismatched tag: sentinel for surface-map doesn't exempt a self-map call.
    write_sentinel("surface-map", existing_holder_id=None)
    mismatched = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_store",
            "tool_input": {"content": "x", "tags": ["self-map"]},
        }
    )
    ok15 = mismatched.returncode == 2
    results.append(
        ("exemption: mismatched tag -> blocked", ok15, f"exit={mismatched.returncode}")
    )

    if SENTINEL_PATH.is_file():
        SENTINEL_PATH.unlink()

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

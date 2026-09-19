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
PROTECTED_IDS_PATH = HOOK.parent.parent / ".protected-ids.json"

SELF_HOLDER = "11111111-1111-1111-1111-111111111111"
SURFACE_HOLDER = "22222222-2222-2222-2222-222222222222"
HANDOFF_ID = "33333333-3333-3333-3333-333333333333"
UNPROTECTED_ID = "44444444-4444-4444-4444-444444444444"


def write_protected_ids(
    self_map_holder: str | None = SELF_HOLDER,
    surface_map_holder: str | None = SURFACE_HOLDER,
    handoff_id: str | None = HANDOFF_ID,
) -> None:
    PROTECTED_IDS_PATH.write_text(
        json.dumps(
            {
                "self_map_holder": self_map_holder,
                "surface_map_holder": surface_map_holder,
                "handoff_id": handoff_id,
                "written_at": "2026-09-19T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )


def clear_protected_ids() -> None:
    if PROTECTED_IDS_PATH.is_file():
        PROTECTED_IDS_PATH.unlink()


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

    # --- Issue #5's AC 8: protected ids ---
    clear_protected_ids()

    # No protected-ids file at all -> this rule has nothing to check, archive passes.
    no_file = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_archive",
            "tool_input": {"id": SELF_HOLDER},
        }
    )
    ok16 = no_file.returncode == 0
    results.append(
        (
            "AC8: no protected-ids file -> rule has nothing to check, allowed",
            ok16,
            f"exit={no_file.returncode}",
        )
    )

    write_protected_ids()

    # archive on the self-map holder -> blocked
    archive_self = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_archive",
            "tool_input": {"id": SELF_HOLDER},
        }
    )
    ok17 = archive_self.returncode == 2 and "AC 8" in archive_self.stderr
    results.append(
        (
            "AC8: archive on self-map holder blocked",
            ok17,
            f"exit={archive_self.returncode}, stderr={archive_self.stderr.strip()!r}",
        )
    )

    # delete on the surface-map holder -> blocked
    delete_surface = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_delete",
            "tool_input": {"id": SURFACE_HOLDER},
        }
    )
    ok18 = delete_surface.returncode == 2 and "AC 8" in delete_surface.stderr
    results.append(
        (
            "AC8: delete on surface-map holder blocked",
            ok18,
            f"exit={delete_surface.returncode}",
        )
    )

    # archive on an unprotected id -> allowed
    archive_unprotected = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_archive",
            "tool_input": {"id": UNPROTECTED_ID},
        }
    )
    ok19 = archive_unprotected.returncode == 0
    results.append(
        (
            "AC8: archive on an unprotected id allowed",
            ok19,
            f"exit={archive_unprotected.returncode}",
        )
    )

    # unrelate with a protected source_id -> blocked
    unrelate_source = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_unrelate",
            "tool_input": {"source_id": HANDOFF_ID, "target_id": UNPROTECTED_ID},
        }
    )
    ok20 = unrelate_source.returncode == 2 and "AC 8" in unrelate_source.stderr
    results.append(
        (
            "AC8: unrelate with protected source_id blocked",
            ok20,
            f"exit={unrelate_source.returncode}",
        )
    )

    # unrelate with a protected target_id -> blocked
    unrelate_target = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_unrelate",
            "tool_input": {"source_id": UNPROTECTED_ID, "target_id": SELF_HOLDER},
        }
    )
    ok21 = unrelate_target.returncode == 2 and "AC 8" in unrelate_target.stderr
    results.append(
        (
            "AC8: unrelate with protected target_id blocked",
            ok21,
            f"exit={unrelate_target.returncode}",
        )
    )

    # unrelate with neither id protected -> allowed
    unrelate_clean = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_unrelate",
            "tool_input": {
                "source_id": UNPROTECTED_ID,
                "target_id": "55555555-5555-5555-5555-555555555555",
            },
        }
    )
    ok22 = unrelate_clean.returncode == 0
    results.append(
        (
            "AC8: unrelate with no protected id allowed",
            ok22,
            f"exit={unrelate_clean.returncode}",
        )
    )

    # update on the self-map holder, content only -> still blocked (only the
    # surface-map holder's content-only path is exempt)
    update_self = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_update",
            "tool_input": {"id": SELF_HOLDER, "content": "x"},
        }
    )
    ok23 = update_self.returncode == 2 and "AC 8" in update_self.stderr
    results.append(
        (
            "AC8: content-only update on self-map holder still blocked",
            ok23,
            f"exit={update_self.returncode}",
        )
    )

    # update on the handoff id -> blocked
    update_handoff = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_update",
            "tool_input": {"id": HANDOFF_ID, "content": "x"},
        }
    )
    ok24 = update_handoff.returncode == 2 and "AC 8" in update_handoff.stderr
    results.append(
        (
            "AC8: update on the handoff id blocked",
            ok24,
            f"exit={update_handoff.returncode}",
        )
    )

    # update on the surface-map holder, content only, no tags -> allowed (the
    # heartbeat's own exit-walk write, issue #4)
    update_surface_content_only = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_update",
            "tool_input": {"id": SURFACE_HOLDER, "content": "a-uuid-or-a-space"},
        }
    )
    ok25 = update_surface_content_only.returncode == 0
    results.append(
        (
            "AC8: content-only update on surface-map holder allowed (heartbeat path)",
            ok25,
            f"exit={update_surface_content_only.returncode}",
        )
    )

    # update on the surface-map holder that ALSO touches tags -> blocked
    update_surface_with_tags = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_update",
            "tool_input": {
                "id": SURFACE_HOLDER,
                "content": "x",
                "tags": ["surface-map"],
            },
        }
    )
    ok26 = (
        update_surface_with_tags.returncode == 2
        and "AC 8" in update_surface_with_tags.stderr
    )
    results.append(
        (
            "AC8: update on surface-map holder WITH tags blocked",
            ok26,
            f"exit={update_surface_with_tags.returncode}",
        )
    )

    # update on an unprotected id -> allowed, unaffected by this rule
    update_unprotected = run_hook(
        {
            "tool_name": "mcp__synaptra__memory_update",
            "tool_input": {"id": UNPROTECTED_ID, "content": "x", "tags": ["whatever"]},
        }
    )
    ok27 = update_unprotected.returncode == 0
    results.append(
        (
            "AC8: update on an unprotected id unaffected",
            ok27,
            f"exit={update_unprotected.returncode}",
        )
    )

    clear_protected_ids()

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

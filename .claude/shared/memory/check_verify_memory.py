#!/usr/bin/env python3
"""Proof for issue #3's two-list checks in session-end/verify_memory.py (AC 1, 2, 4,
5, 6, 7, 19), plus a regression check that issue #2's conformance scan (AC 24) still
works unchanged. Feeds good and bad JSON directly to the script and asserts the exit
codes and the specific finding lines -- no synaptra I/O, live or scratch. Stdlib only.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "session-end"
    / "verify_memory.py"
)

SELF_ID_1 = "11111111-1111-1111-1111-111111111111"
SELF_ID_2 = "22222222-2222-2222-2222-222222222222"
SURFACE_ID_1 = "33333333-3333-3333-3333-333333333333"


def run(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "-"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=15,
    )


def base_memories() -> list[dict]:
    return [
        {
            "id": "holder-self",
            "state": "active",
            "tags": ["self-map"],
            "source": "create-memory:x",
            "content": f"{SELF_ID_1}\n{SELF_ID_2}",
        },
        {
            "id": "holder-surface",
            "state": "active",
            "tags": ["surface-map"],
            "source": "create-memory:x",
            "content": SURFACE_ID_1,
        },
    ]


def base_resolved() -> dict:
    return {
        SELF_ID_1: {"memory_type": "identity"},
        SELF_ID_2: {"memory_type": "identity"},
        SURFACE_ID_1: {"memory_type": "semantic"},
    }


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, proc: subprocess.CompletedProcess) -> None:
        results.append((name, ok, f"exit={proc.returncode}"))

    # --- Good payload: clean, exit 0 ---
    p = run({"memories": base_memories(), "resolved": base_resolved()})
    record("clean payload -> exit 0", p.returncode == 0, p)

    # --- AC 1/2: no holder at all ---
    mems = [m for m in base_memories() if "self-map" not in m["tags"]]
    p = run({"memories": mems, "resolved": base_resolved()})
    ok = p.returncode == 1 and "[self-map] no active holder found (AC 1/2)" in p.stdout
    results.append(("AC1/2: missing holder reported", ok, f"exit={p.returncode}"))

    # --- AC 5: two holders for the same tag ---
    mems = base_memories() + [
        {
            "id": "holder-self-2",
            "state": "active",
            "tags": ["self-map"],
            "source": "create-memory:x",
            "content": SELF_ID_1,
        },
    ]
    p = run({"memories": mems, "resolved": base_resolved()})
    ok = (
        p.returncode == 1
        and "holder-self" in p.stdout
        and "holder-self-2" in p.stdout
        and "AC 5" in p.stdout
    )
    results.append(
        ("AC5: multiple holders named, none loaded", ok, f"exit={p.returncode}")
    )

    # --- AC 19: malformed content (not full uuids one per line) ---
    mems = base_memories()
    mems[0]["content"] = f"{SELF_ID_1}\nsome prose here, not a uuid"
    p = run({"memories": mems, "resolved": base_resolved()})
    ok = p.returncode == 1 and "MALFORMED" in p.stdout and "AC 19" in p.stdout
    results.append(
        ("AC19: malformed content reported, not loaded", ok, f"exit={p.returncode}")
    )

    # --- AC 7: surface map over the cap ---
    mems = base_memories()
    over_cap_ids = [f"{i:08x}-0000-0000-0000-000000000000" for i in range(26)]
    mems[1]["content"] = "\n".join(over_cap_ids)
    resolved = dict(base_resolved())
    for i in over_cap_ids:
        resolved[i] = {"memory_type": "semantic"}
    p = run({"memories": mems, "resolved": resolved})
    ok = (
        p.returncode == 1 and "exceeds the cap of 25" in p.stdout and "AC 7" in p.stdout
    )
    results.append(("AC7: over-cap surface map reported", ok, f"exit={p.returncode}"))

    # --- AC 7 (negative control): a SHORT surface map is correct, not flagged ---
    mems = base_memories()
    mems[1]["content"] = SURFACE_ID_1  # just one id
    p = run({"memories": mems, "resolved": base_resolved()})
    ok = p.returncode == 0
    results.append(
        (
            "AC7: a short surface map is correct, no cap violation",
            ok,
            f"exit={p.returncode}",
        )
    )

    # --- No self-map cap enforced (deliberately -- see verify_memory.py's own note) ---
    mems = base_memories()
    many_self_ids = [f"{i:08x}-1111-1111-1111-111111111111" for i in range(10)]
    mems[0]["content"] = "\n".join(many_self_ids)
    resolved = {i: {"memory_type": "identity"} for i in many_self_ids}
    resolved[SURFACE_ID_1] = {"memory_type": "semantic"}
    p = run({"memories": mems, "resolved": resolved})
    ok = p.returncode == 0
    results.append(
        (
            "self-map has no numeric cap in this issue -- 10 ids does not fail",
            ok,
            f"exit={p.returncode}",
        )
    )

    # --- AC 4: an id that does not resolve ---
    resolved = dict(base_resolved())
    del resolved[SELF_ID_2]
    p = run({"memories": base_memories(), "resolved": resolved})
    ok = p.returncode == 1 and f"id {SELF_ID_2} does NOT resolve (AC 4)" in p.stdout
    results.append(
        (
            "AC4: unresolved id reported by id, scan continues",
            ok,
            f"exit={p.returncode}",
        )
    )

    # --- AC 6: a self-map id typed something other than identity ---
    resolved = dict(base_resolved())
    resolved[SELF_ID_2] = {"memory_type": "semantic"}
    p = run({"memories": base_memories(), "resolved": resolved})
    ok = (
        p.returncode == 1
        and "not 'identity' (AC 6)" in p.stdout
        and SELF_ID_2 in p.stdout
    )
    results.append(
        ("AC6: non-identity self-map id reported", ok, f"exit={p.returncode}")
    )

    # --- resolved omitted entirely: id-level checks reported as skipped, not passed ---
    p = run({"memories": base_memories()})
    ok = p.returncode == 1 and "skipped, not silently passed" in p.stdout
    results.append(
        (
            "no 'resolved' -> reported skipped, exit reflects it",
            ok,
            f"exit={p.returncode}",
        )
    )

    # --- Regression: issue #2's conformance scan (AC 24) still works ---
    mems = base_memories() + [
        {"id": "rogue", "state": "active", "tags": [], "source": None, "content": "x"},
    ]
    p = run({"memories": mems, "resolved": base_resolved()})
    ok = p.returncode == 1 and "id=rogue" in p.stdout and "VIOLATION" in p.stdout
    results.append(
        (
            "AC24 regression: conformance scan still catches a direct store",
            ok,
            f"exit={p.returncode}",
        )
    )

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

#!/usr/bin/env python3
"""Proof for issue #2's AC 24 -- store one compliant memory (source prefixed
'create-memory:') and one violation (source unset, mimicking a direct
memory_store call) against a SCRATCH server, list active memories, feed the
listing to verify_memory.py, and confirm it flags only the violation by id.

Never the live store.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

VERIFY_SCRIPT = (
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "session-end"
    / "verify_memory.py"
)


def cm(cm_path: str, url: str, *args: str) -> dict:
    proc = subprocess.run(
        [cm_path, "--url", url, "--json", *args],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"cm {' '.join(args)} failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    return json.loads(proc.stdout)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--cm", required=True)
    args = ap.parse_args()

    results: list[tuple[str, bool, str]] = []

    # Compliant store -- source carries the create-memory: prefix
    compliant = cm(
        args.cm,
        args.url,
        "store",
        "compliant probe: went through create-memory",
        "--source",
        "create-memory:claude-sonnet-5",
    )
    compliant_id = compliant["data"]["id"]

    # Violation -- no source at all, mimicking a direct memory_store call outside the skill
    violation = cm(
        args.cm,
        args.url,
        "store",
        "violation probe: a direct call, bypassing create-memory",
    )
    violation_id = violation["data"]["id"]

    listing = cm(args.cm, args.url, "list", "--state", "active", "--limit", "100")

    proc = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT), "-"],
        input=json.dumps(listing["data"]),
        capture_output=True,
        text=True,
        timeout=15,
    )

    flagged_violation = violation_id in proc.stdout
    flagged_compliant = compliant_id in proc.stdout
    correct_exit = (
        proc.returncode == 1
    )  # violations present -> non-zero, per the script's own contract

    ok = flagged_violation and not flagged_compliant and correct_exit
    results.append(
        (
            "AC24 conformance scan",
            ok,
            f"exit={proc.returncode}, violation id flagged={flagged_violation}, "
            f"compliant id wrongly flagged={flagged_compliant}\n--- scan output ---\n{proc.stdout}",
        )
    )

    # Clean-store case: only the compliant one -> scan reports zero violations, exit 0
    proc2 = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT), "-"],
        input=json.dumps(
            {
                "memories": [
                    m for m in listing["data"]["memories"] if m["id"] == compliant_id
                ]
            }
        ),
        capture_output=True,
        text=True,
        timeout=15,
    )
    ok2 = proc2.returncode == 0 and "No conformance violations" in proc2.stdout
    results.append(("AC24 clean listing -> exit 0", ok2, f"exit={proc2.returncode}"))

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

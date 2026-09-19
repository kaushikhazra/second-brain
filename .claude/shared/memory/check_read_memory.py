#!/usr/bin/env python3
"""Scripted synaptra session for issue #2, cycle 3 -- proves the one slice of
AC 14 a raw script actually can: recall on a genuinely EMPTY store returns a
clean empty list, not an error and not a hang.

Point this at a scratch server backed by an empty data directory -- not the
populated cycle-2 scratch store, which cannot produce a true empty result (see
logs/cycle-3.md for why). Never the live store.

    SYNAPTRA_BACKEND=surrealkv-file SYNAPTRA_DB=C:/Projects/.tmp/second-brain-loop-2/empty-data \\
      SYNAPTRA_PORT=8052 <venv-python> -m synaptra.server --transport http

    <venv-python> check_read_memory.py --url http://127.0.0.1:8052/mcp --cm <path-to-cm.exe>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--cm", required=True)
    args = ap.parse_args()

    results: list[tuple[str, bool, str]] = []

    # --- AC 14 (empty-store slice only): recall on a store with nothing in it ---
    try:
        r = cm(
            args.cm, args.url, "recall", "anything at all, this store has nothing in it"
        )
        memories = r["data"]["memories"]
        ok = r.get("success", False) and memories == []
        results.append(
            (
                "AC14 (empty-store slice)",
                ok,
                f"success={r.get('success')}, memories={memories!r} -- clean empty list, no error"
                if ok
                else f"unexpected: {r}",
            )
        )
    except Exception as e:
        results.append(
            (
                "AC14 (empty-store slice)",
                False,
                f"error (should not hang or throw): {e}",
            )
        )

    passed = 0
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"[{status}] {name}: {detail}")
    print(f"\n{passed}/{len(results)} of this script's criteria pass.")
    print(
        "\nNOTE: this only proves the empty-store case. On a NON-empty store, "
        "memory_recall's ranked fusion returned a low-score match for every query "
        "tried in cycle 3 (including nonsense strings and impossible tag filters) -- "
        "it never emptied out. So 'a recall that returns nothing' (AC 14) is fully "
        "provable by script only for a genuinely empty store; on a populated store, "
        "deciding a low-score hit isn't really a match is the /read-memory skill's own "
        "judgment call, same class as AC 5/8/11/12/26 -- not something this script can "
        "credit to synaptra."
    )
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

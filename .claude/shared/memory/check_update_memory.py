#!/usr/bin/env python3
"""Scripted synaptra session for issue #2, cycle 4 -- proves AC 18 and AC 19
against a SCRATCH server. AC 16, 17, 20 lean on skill judgment (when NOT to
update, whether something is "wrong" vs "incomplete", confirming by re-read)
and are not attempted here -- same discipline as prior cycles' unproved list.

Never the live store. Point at a scratch synaptra HTTP server via --url.
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

    # --- AC 18: memory_update's tags argument replaces wholesale ---
    try:
        r = cm(
            args.cm,
            args.url,
            "store",
            "AC18 probe: tag replacement behaviour",
            "--type",
            "semantic",
            "--tags",
            "tag-a,tag-b",
        )
        mem_id = r["data"]["id"]
        before = set(r["data"]["tags"])

        cm(args.cm, args.url, "update", mem_id, "--tags", "tag-a,tag-c")
        got = cm(args.cm, args.url, "get", mem_id)
        after = set(got["data"]["memory"]["tags"])

        # The behaviour AC 18 requires the SKILL to account for: passing a partial
        # tag list silently drops what wasn't named. Confirm that is really what
        # happens here, so the skill's "fetch current tags first" instruction is
        # protecting against something real, not a stale claim.
        dropped_b = "tag-b" not in after
        kept_a = "tag-a" in after
        added_c = "tag-c" in after
        ok = dropped_b and kept_a and added_c
        record_detail = (
            f"before={sorted(before)}, after update(tags='tag-a,tag-c')={sorted(after)} -- "
            f"'tag-b' dropped={dropped_b} (not renamed, not preserved) confirms wholesale "
            f"replace; the skill's fetch-current-tags-first step is what AC 18 actually requires"
        )
        results.append(("AC18", ok, record_detail))
    except Exception as e:
        results.append(("AC18", False, f"error: {e}"))

    # --- AC 19: type change via `cm update --type`, confirmed by read-back ---
    try:
        r = cm(
            args.cm,
            args.url,
            "store",
            "AC19 probe: type change via cm CLI",
            "--type",
            "episodic",
        )
        mem_id = r["data"]["id"]
        landed_before = r["data"]["memory_type"]

        cm(args.cm, args.url, "update", mem_id, "--type", "procedural")
        got = cm(args.cm, args.url, "get", mem_id)
        landed_after = got["data"]["memory"]["memory_type"]

        ok = landed_before == "episodic" and landed_after == "procedural"
        results.append(
            (
                "AC19",
                ok,
                f"stored as '{landed_before}', 'cm update --type procedural' then read back as "
                f"'{landed_after}' -- the cm-CLI path works and is confirmed by re-read, not by "
                f"the update call's own return value",
            )
        )
    except Exception as e:
        results.append(("AC19", False, f"error: {e}"))

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

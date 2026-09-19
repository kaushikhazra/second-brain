#!/usr/bin/env python3
"""Scripted synaptra session for issue #2, cycle 5 -- proves the archive/restore
mechanics `/delete-memory`'s "archive by default" promise depends on, against a
SCRATCH server. AC 21's actual judgment (never-true vs duplicate vs outgrown
scaffolding) and AC 22 (refusing a partial constellation removal) are skill-level
and not attempted here -- same discipline as the rest of the unproved list.

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

    # --- Archive: leaves the active set, but memory_get still finds it, restore brings it back ---
    try:
        r = cm(args.cm, args.url, "store", "delete-memory probe: a superseded fact")
        mem_id = r["data"]["id"]

        cm(args.cm, args.url, "archive", mem_id)

        active_list = cm(
            args.cm,
            args.url,
            "list",
            "--state",
            "active",
            "--search",
            "delete-memory probe",
        )
        active_ids = {m["id"] for m in active_list["data"]["memories"]}
        left_active = mem_id not in active_ids

        got = cm(args.cm, args.url, "get", mem_id)
        still_gettable = got["data"]["memory"]["id"] == mem_id
        state_after_archive = got["data"]["memory"]["state"]

        cm(args.cm, args.url, "restore", mem_id)
        got2 = cm(args.cm, args.url, "get", mem_id)
        state_after_restore = got2["data"]["memory"]["state"]

        ok = (
            left_active
            and still_gettable
            and state_after_archive == "archived"
            and state_after_restore == "active"
        )
        results.append(
            (
                "archive/restore mechanics",
                ok,
                f"left active set={left_active}, still reachable by memory_get={still_gettable}, "
                f"state after archive='{state_after_archive}', state after restore='{state_after_restore}' "
                f"-- this is the substrate behaviour /delete-memory's 'archive by default, reversible' "
                f"promise depends on; it does not prove the skill always CHOOSES archive over delete "
                f"(AC 21's actual judgment, unproved here)",
            )
        )
    except Exception as e:
        results.append(("archive/restore mechanics", False, f"error: {e}"))

    # --- Delete: cascades, confirm=true required (server-side, already verified in cycle 5's action.md research) ---
    try:
        r = cm(
            args.cm, args.url, "store", "delete-memory probe: scaffolding to be removed"
        )
        mem_id = r["data"]["id"]
        cm(
            args.cm, args.url, "delete", mem_id, "-y"
        )  # cm CLI's -y supplies confirm=true
        try:
            cm(args.cm, args.url, "get", mem_id)
            found_after_delete = True
        except RuntimeError:
            found_after_delete = False
        ok = not found_after_delete
        results.append(
            (
                "delete is permanent",
                ok,
                f"memory_get after delete: {'still found (BUG)' if found_after_delete else 'not found, as expected'}",
            )
        )
    except Exception as e:
        results.append(("delete is permanent", False, f"error: {e}"))

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

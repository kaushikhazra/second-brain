#!/usr/bin/env python3
"""Scripted synaptra session for issue #2, cycle 2 — proves AC 6-10, 25-27 (or
says plainly why a given one can't be proved this way) against a SCRATCH server.

Never the live store. Point this at a scratch synaptra HTTP server via --url,
e.g.:

    SYNAPTRA_BACKEND=surrealkv-file SYNAPTRA_DB=C:/Projects/.tmp/second-brain-loop-2/data \\
      SYNAPTRA_PORT=8051 <venv-python> -m synaptra.server --transport http

    <venv-python> check_create_memory.py --url http://127.0.0.1:8051/mcp --cm <path-to-cm.exe>

AC 27 stops the server it was given via --url partway through (by killing the
process whose pid is passed with --server-pid, if given) — if no --server-pid
is passed, AC 27 is skipped and reported as such rather than guessed at.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time


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
    ap.add_argument("--cm", required=True, help="path to cm executable")
    ap.add_argument(
        "--server-pid",
        type=int,
        default=None,
        help="pid of the scratch server, for AC27",
    )
    args = ap.parse_args()

    results: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        results.append((name, ok, detail))

    # --- AC 6: store with source+tags, no importance -> store-assigned importance ---
    try:
        r = cm(
            args.cm,
            args.url,
            "store",
            "AC6 probe memory content",
            "--type",
            "semantic",
            "--tags",
            "ac6-probe",
            "--source",
            "check_create_memory",
        )
        data = r["data"]
        imp = data.get("importance")
        ok = (
            imp is not None
            and 0.0 <= imp <= 1.0
            and data.get("tags") == ["ac6-probe"]
            and data.get("source") == "check_create_memory"
        )
        record(
            "AC6", ok, f"source/tags passed through, importance auto-scored to {imp}"
        )
    except Exception as e:
        record("AC6", False, f"error: {e}")

    # --- AC 7: explicit type honored; omitted type gets classified ---
    try:
        r1 = cm(
            args.cm,
            args.url,
            "store",
            "AC7 explicit-type probe",
            "--type",
            "procedural",
        )
        landed1 = r1["data"]["memory_type"]
        ok1 = landed1 == "procedural"

        r2 = cm(
            args.cm,
            args.url,
            "store",
            "AC7 omitted-type probe: a fact about a configuration value",
        )
        landed2 = r2["data"]["memory_type"]
        ok2 = landed2 in {
            "working",
            "episodic",
            "semantic",
            "procedural",
            "identity",
            "person",
        }

        record(
            "AC7",
            ok1 and ok2,
            f"explicit type='procedural' landed as '{landed1}'; "
            f"omitted type auto-classified to '{landed2}' (verification step still fires on every store)",
        )
    except Exception as e:
        record("AC7", False, f"error: {e}")

    # --- AC 8: a fact is one node, never split (script can only prove ONE store == ONE node) ---
    try:
        r = cm(
            args.cm,
            args.url,
            "store",
            "AC8 probe: a single fact, stored whole, however long it runs on",
        )
        ok = bool(r["data"].get("id"))
        record(
            "AC8",
            ok,
            "one store call produced exactly one node (trivially true of any single call — "
            "'never split' is the skill's classification discipline before writing, not something "
            "a single store call can violate; not fully provable by this script)",
        )
    except Exception as e:
        record("AC8", False, f"error: {e}")

    # --- AC 9: instance --supports--> procedure, same type ---
    instance_id = procedure_id = None
    try:
        inst = cm(
            args.cm,
            args.url,
            "store",
            "AC9 instance: verbatim account of what happened",
            "--type",
            "procedural",
        )
        proc = cm(
            args.cm,
            args.url,
            "store",
            "AC9 procedure: the bare rule",
            "--type",
            "procedural",
        )
        instance_id, procedure_id = inst["data"]["id"], proc["data"]["id"]
        same_type = (
            inst["data"]["memory_type"] == proc["data"]["memory_type"] == "procedural"
        )
        cm(args.cm, args.url, "relate", instance_id, procedure_id, "--type", "supports")
        related = cm(args.cm, args.url, "related", instance_id)
        edges = (
            related["data"].get("related", related["data"])
            if isinstance(related["data"], dict)
            else related["data"]
        )
        edge_text = json.dumps(related["data"])
        found_edge = procedure_id in edge_text and "supports" in edge_text
        record(
            "AC9",
            same_type and found_edge,
            f"same_type={same_type}, supports edge found={found_edge}",
        )
    except Exception as e:
        record("AC9", False, f"error: {e}")

    # --- AC 10: boundary --part_of--> procedure ---
    try:
        if procedure_id is None:
            raise RuntimeError(
                "AC9 did not produce a procedure_id to attach a boundary to"
            )
        bound = cm(
            args.cm,
            args.url,
            "store",
            "AC10 boundary: when the rule does NOT apply",
            "--type",
            "procedural",
        )
        boundary_id = bound["data"]["id"]
        cm(args.cm, args.url, "relate", boundary_id, procedure_id, "--type", "part_of")
        related = cm(args.cm, args.url, "related", boundary_id)
        edge_text = json.dumps(related["data"])
        found_edge = procedure_id in edge_text and "part_of" in edge_text
        record(
            "AC10",
            found_edge,
            f"part_of edge from boundary to procedure found={found_edge}",
        )
    except Exception as e:
        record("AC10", False, f"error: {e}")

    # --- AC 12: reserved tags — NOT provable at the synaptra layer ---
    try:
        r = cm(
            args.cm,
            args.url,
            "store",
            "AC12 probe: would this be refused?",
            "--type",
            "semantic",
            "--tags",
            "surface-map",
        )
        accepted = r.get("success", False)
        record(
            "AC12",
            False,
            f"NOT MET by this script: raw memory_store has no concept of reserved tags and "
            f"{'accepted' if accepted else 'rejected'} the bare 'surface-map' tag with no complaint. "
            f"The refusal is the /create-memory skill's own responsibility (step 4 in SKILL.md) — "
            f"provable only by exercising the skill's judgment, not synaptra's, so this stays "
            f"'implemented but not proved' until a scripted-agent check exists.",
        )
    except Exception as e:
        record("AC12", False, f"error: {e}")

    # --- AC 25: store, then immediately read back ---
    try:
        r = cm(args.cm, args.url, "store", "AC25 probe: read-back after store")
        mem_id = r["data"]["id"]
        got = cm(args.cm, args.url, "get", mem_id)
        # cm get's JSON nests the memory under "memory" -- unlike cm store's flat shape.
        ok = got["data"]["memory"]["id"] == mem_id
        record(
            "AC25",
            ok,
            f"stored id {mem_id[:8]}... read back successfully (positive path only — "
            "no fault injection this cycle to prove the negative; see action.md)",
        )
    except Exception as e:
        record("AC25", False, f"error: {e}")

    # --- AC 26: memory_relate with a short id — observe, don't assume ---
    try:
        real_id = instance_id or "00000000-0000-0000-0000-000000000000"
        short_id = real_id[:8]
        try:
            cm(args.cm, args.url, "relate", short_id, real_id, "--type", "relates_to")
            server_rejects = False
            detail = "server ACCEPTED an 8-char id with no error"
        except RuntimeError as re_:
            server_rejects = True
            detail = f"server rejected it: {re_}"
        record(
            "AC26",
            False,
            f"NOT MET by this script either way: {detail}. Per cycle 1's reading of "
            f"engine.create_relationship, no length check exists there — so AC26 (refuse BEFORE "
            f"the call, and say the rule) is the /create-memory skill's own pre-call check, not "
            f"something this script can credit to synaptra. Stays 'implemented but not proved'.",
        )
    except Exception as e:
        record("AC26", False, f"error: {e}")

    # --- AC 27: synaptra unreachable -> the four skills say so and stop ---
    if args.server_pid is None:
        record(
            "AC27",
            False,
            "SKIPPED — no --server-pid given, can't safely stop the scratch server from here",
        )
    else:
        try:
            import os
            import signal

            os.kill(args.server_pid, signal.SIGTERM)
            time.sleep(2)
            try:
                cm(args.cm, args.url, "stats")
                record(
                    "AC27",
                    False,
                    "server still answered after SIGTERM — did not actually stop",
                )
            except Exception as e2:
                record("AC27", True, f"post-shutdown call failed as expected: {e2}")
        except Exception as e:
            record("AC27", False, f"error trying to stop the server: {e}")

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

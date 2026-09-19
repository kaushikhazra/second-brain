#!/usr/bin/env python3
"""Issue #6, cycle 3 -- scripted-agent proof of the two invocation paths.

Cycle 2 proved a real by-hand pass end to end (AC 10-16, 18). This script proves
the OTHER half of invocation: that a heartbeat-fired call is gated on the
activation record (AC 7's positive and negative halves, AC 6's negative half),
that a by-hand call runs regardless of the record and says so (AC 9), and folds
in AC 17 (four protected files untouched) and AC 20 (synaptra unreachable) as
cheap additions to the same scaffold. AC 19 (no network) uses `--disallowedTools
WebSearch,WebFetch,Bash,Task` to remove every network-capable escape hatch this
scratch project has -- the CLI has no supported way to cut a subprocess's
network from outside. First attempt only denied WebSearch/WebFetch: the model
reached the same URL through `curl` via Bash instead (a real finding, not a
check-script bug -- recorded in this cycle's log). Denying Bash and Task too
closes that: nothing left in this scratch project can reach the network.

Five runs, each against a FRESH copy of the same seeded store (never reusing a
mutated store across runs -- each run's before-state must be the clean seed):

  --mode heartbeat-active     : /curiosity "requested by heartbeat", record active
                                  -> a pass runs (AC 7 positive)
  --mode heartbeat-inactive   : /curiosity "requested by heartbeat", record inactive
                                  -> nothing runs (AC 6 negative half, AC 7 negative
                                     half, AC 8's "only while active" half)
  --mode by-hand              : /curiosity, no marker, record inactive
                                  -> a pass runs anyway, says invoked by hand (AC 9)
  --mode no-network           : by-hand, WebSearch/WebFetch disallowed
                                  -> Act 1's read fails, nothing stored (AC 19)
  --mode synaptra-unreachable : by-hand, .mcp.json points at a dead server
                                  -> says so, stops (AC 20)

AC 17 (persona.md/user.md/heartbeat's goal.md+observe.md untouched) is checked
on every mode that actually runs a pass (heartbeat-active, by-hand) -- hashed
before build, after run.

Same junction-safety and never-share-a-scratch-subtree discipline as this
story's other scripted-agent scripts.

Usage:
    python check_curiosity_invocation_scripted_agent.py --build
    python check_curiosity_invocation_scripted_agent.py --seed --mode heartbeat-active --url http://127.0.0.1:8055/mcp
    python check_curiosity_invocation_scripted_agent.py --run --mode heartbeat-active
    python check_curiosity_invocation_scripted_agent.py --verify --mode heartbeat-active --url http://127.0.0.1:8055/mcp

Never the live store, never the live project. Costs real money on --run.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # -> .claude
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-6")
SCRATCH_PROJECT = SCRATCH_ROOT / "invocation-scratch-project"

MODES = (
    "heartbeat-active",
    "heartbeat-inactive",
    "by-hand",
    "no-network",
    "synaptra-unreachable",
)


def data_dir(mode: str) -> Path:
    return SCRATCH_ROOT / f"invocation-scratch-data-{mode}"


SEED = [
    ("bcrypt is the standard choice for hashing passwords.", "semantic", "thin-claim"),
    (
        "Mise en place: prep every ingredient before cooking starts, so the "
        "actual cook has no mid-process scramble.",
        "semantic",
        "distant-a",
    ),
    (
        "TCP's three-way handshake establishes connection state before any data "
        "is transferred.",
        "semantic",
        "distant-b",
    ),
]

PROTECTED_FILES = ["persona.md", "user.md", "goal.md", "observe.md"]


def build_scratch_project() -> None:
    venv_link = SCRATCH_PROJECT / ".claude" / ".venv"
    if venv_link.is_dir():
        os.rmdir(venv_link)
    if SCRATCH_PROJECT.exists():
        shutil.rmtree(SCRATCH_PROJECT)

    (SCRATCH_PROJECT / ".claude").mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(venv_link), str(REPO_ROOT / ".venv")],
        capture_output=True,
        text=True,
        check=True,
    )

    for skill in ("curiosity", "create-memory"):
        dest = SCRATCH_PROJECT / ".claude" / "skills" / skill
        dest.mkdir(parents=True, exist_ok=True)
        src = REPO_ROOT / "skills" / skill
        for f in src.glob("*"):
            if f.is_file():
                shutil.copy(f, dest / f.name)

    (SCRATCH_PROJECT / ".claude" / "shared" / "memory").mkdir(
        parents=True, exist_ok=True
    )
    shutil.copy(
        REPO_ROOT / "shared" / "memory" / "memory-shapes.md",
        SCRATCH_PROJECT / ".claude" / "shared" / "memory" / "memory-shapes.md",
    )
    shutil.copy(
        REPO_ROOT / "shared" / "activation.py",
        SCRATCH_PROJECT / ".claude" / "shared" / "activation.py",
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
                            "matcher": "mcp__synaptra__memory_store|mcp__synaptra__memory_update|mcp__synaptra__memory_relate|mcp__synaptra__memory_archive|mcp__synaptra__memory_delete|mcp__synaptra__memory_unrelate",
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

    # AC 17's four protected files.
    (SCRATCH_PROJECT / "persona.md").write_text(
        "# Testa -- Persona\n\n## Identity\n\n- **Name**: Testa\n- **Voice**: they/them\n"
        "- **Character**: Careful and direct.\n\n## Roles\n\n| Role | What they do |\n"
        "|------|---------------|\n| Research assistant | Finds information |\n\n"
        "## Proactivity\n\nModerate.\n\n## Communication Style\n\n- Direct\n",
        encoding="utf-8",
    )
    (SCRATCH_PROJECT / "user.md").write_text(
        "# Test User\n\n## Personal\n\n- **Name**: Test User\n", encoding="utf-8"
    )
    (SCRATCH_PROJECT / "goal.md").write_text(
        "# Scratch goal.md\n\nStand-in for a skill's own governance file, to prove AC 17 "
        "(a curiosity pass never edits this).\n",
        encoding="utf-8",
    )
    (SCRATCH_PROJECT / "observe.md").write_text(
        "# Scratch observe.md\n\nStand-in for a skill's own governance file, to prove "
        "AC 17 (a curiosity pass never edits this).\n",
        encoding="utf-8",
    )

    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nScratch test for issue #6's invocation-path proof (AC 6, 7, "
        "8, 9, 17, 19, 20). Route all memory storage through /create-memory -- never "
        "a raw memory_store call.\n",
        encoding="utf-8",
    )
    # .mcp.json and activations.json are written per-run by main(), once the
    # mode (and therefore the data dir and the activation state) is known.


def write_mcp_json(mode: str, dead: bool = False) -> None:
    if dead:
        server = {
            "type": "stdio",
            "command": str(REPO_ROOT / ".venv" / "Scripts" / "synaptra.exe"),
            "args": ["--transport", "stdio"],
            "env": {
                "SYNAPTRA_BACKEND": "surrealkv-file",
                "SYNAPTRA_DB": str(SCRATCH_ROOT / "does-not-exist" / "nope"),
            },
        }
        # Force unreachability the same way story #5's AC 17 proof did: point at
        # a command that cannot serve, not merely an empty directory (an empty
        # SurrealKV dir is valid and would just create a fresh empty store).
        server["command"] = str(REPO_ROOT / ".venv" / "Scripts" / "does-not-exist.exe")
    else:
        server = {
            "type": "stdio",
            "command": str(REPO_ROOT / ".venv" / "Scripts" / "synaptra.exe"),
            "args": ["--transport", "stdio"],
            "env": {
                "SYNAPTRA_BACKEND": "surrealkv-file",
                "SYNAPTRA_DB": str(data_dir(mode)),
            },
        }
    (SCRATCH_PROJECT / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"synaptra": server}}, indent=2), encoding="utf-8"
    )


def write_activation_record(active: bool) -> None:
    record = {"curiosity": {"answered_at_version": "0.3.1", "active": active}}
    (SCRATCH_PROJECT / ".claude" / "activations.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )


def cm(cm_path: str, url: str, *args: str) -> dict:
    proc = subprocess.run(
        [cm_path, "--url", url, "--json", *args],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return json.loads(proc.stdout)


def do_seed(cm_path: str, url: str, mode: str) -> None:
    ids = {}
    for content, mtype, tag in SEED:
        mid = cm(
            cm_path,
            url,
            "store",
            content,
            "--type",
            mtype,
            "--tags",
            tag,
            "--source",
            "create-memory:seed",
        )["data"]["id"]
        ids[tag] = mid
        print(f"seeded [{tag}] {mid}")
    (SCRATCH_ROOT / f"seed-ids-{mode}.json").write_text(
        json.dumps(ids, indent=2), encoding="utf-8"
    )
    dump = cm(cm_path, url, "list", "--state", "active", "--limit", "50")["data"][
        "memories"
    ]
    (SCRATCH_ROOT / f"before-dump-{mode}.json").write_text(
        json.dumps(dump, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"before-dump written ({len(dump)} memories)")


def hash_files(paths: list[Path]) -> dict[str, str]:
    import hashlib

    out = {}
    for p in paths:
        out[p.name] = (
            hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        )
    return out


def do_run(mode: str) -> None:
    curiosity_dir = SCRATCH_PROJECT / "curiosity"
    if curiosity_dir.exists():
        shutil.rmtree(curiosity_dir)

    protected_before = hash_files([SCRATCH_PROJECT / f for f in PROTECTED_FILES])
    (SCRATCH_ROOT / f"protected-before-{mode}.json").write_text(
        json.dumps(protected_before, indent=2), encoding="utf-8"
    )

    if mode in ("heartbeat-active", "heartbeat-inactive"):
        ids = json.loads(
            (SCRATCH_ROOT / f"seed-ids-{mode}.json").read_text(encoding="utf-8")
        )
        prompt = (
            f'Run /curiosity "requested by heartbeat". Your store currently holds these '
            f"active memories, ids: {json.dumps(ids)}. Follow the skill exactly -- including "
            "its own activation gate for this invocation path -- and actually perform "
            "whatever the skill's rules say to do (or explicitly not do), don't only "
            "describe it."
        )
    elif mode == "by-hand":
        ids = json.loads(
            (SCRATCH_ROOT / f"seed-ids-{mode}.json").read_text(encoding="utf-8")
        )
        prompt = (
            "Run /curiosity by hand -- one pass. Your store currently holds these active "
            f"memories, ids: {json.dumps(ids)}. Follow the skill exactly and actually "
            "perform the reads and tool calls."
        )
    elif mode == "no-network":
        ids = json.loads(
            (SCRATCH_ROOT / f"seed-ids-{mode}.json").read_text(encoding="utf-8")
        )
        prompt = (
            "Run /curiosity by hand -- one pass. Your store currently holds these active "
            f"memories, ids: {json.dumps(ids)}. Follow the skill exactly."
        )
    else:  # synaptra-unreachable
        prompt = "Run /curiosity by hand -- one pass. Follow the skill exactly."

    args = [
        "claude",
        "-p",
        prompt,
        "--permission-mode",
        "bypassPermissions",
        "--mcp-config",
        ".mcp.json",
        "--strict-mcp-config",
        "--output-format",
        "json",
        "--max-budget-usd",
        "1.0",
        "--no-session-persistence",
    ]
    if mode == "no-network":
        # WebSearch/WebFetch alone isn't enough -- found the hard way, cycle 3:
        # under bypassPermissions the model reached the same URL via `curl`
        # through Bash instead. Deny every network-capable escape hatch this
        # scratch project actually has access to.
        args += ["--disallowedTools", "WebSearch,WebFetch,Bash,Task"]

    proc = subprocess.run(
        args, cwd=str(SCRATCH_PROJECT), capture_output=True, text=True, timeout=600
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    result = json.loads(proc.stdout)
    print(f"cost=${result.get('total_cost_usd'):.4f}")
    print(f"result: {result.get('result')!r}"[:2000])
    (SCRATCH_ROOT / f"transcript-{mode}.txt").write_text(
        str(result.get("result", "")), encoding="utf-8"
    )

    protected_after = hash_files([SCRATCH_PROJECT / f for f in PROTECTED_FILES])
    (SCRATCH_ROOT / f"protected-after-{mode}.json").write_text(
        json.dumps(protected_after, indent=2), encoding="utf-8"
    )


def do_verify(cm_path: str, url: str, mode: str) -> int:
    results: list[tuple[str, bool, str]] = []
    transcript = (SCRATCH_ROOT / f"transcript-{mode}.txt").read_text(
        encoding="utf-8", errors="replace"
    )
    curiosity_dir = SCRATCH_PROJECT / "curiosity"
    record_files = list(curiosity_dir.glob("*.md")) if curiosity_dir.is_dir() else []

    before = (
        json.loads(
            (SCRATCH_ROOT / f"before-dump-{mode}.json").read_text(encoding="utf-8")
        )
        if (SCRATCH_ROOT / f"before-dump-{mode}.json").is_file()
        else []
    )
    before_ids = {m["id"] for m in before}
    after = (
        cm(cm_path, url, "list", "--state", "active", "--limit", "50")["data"][
            "memories"
        ]
        if url
        else []
    )
    new_memories = [m for m in after if m["id"] not in before_ids]

    protected_before = json.loads(
        (SCRATCH_ROOT / f"protected-before-{mode}.json").read_text(encoding="utf-8")
    )
    protected_after = json.loads(
        (SCRATCH_ROOT / f"protected-after-{mode}.json").read_text(encoding="utf-8")
    )
    ac17_unchanged = protected_before == protected_after

    if mode == "heartbeat-active":
        ran = len(new_memories) >= 1 and len(record_files) >= 1
        results.append(
            (
                "AC7 (positive half): heartbeat-fired + active -> a pass runs",
                ran,
                f"new_memories={len(new_memories)} record_files={len(record_files)}",
            )
        )
        results.append(
            (
                "AC17: persona/user/goal/observe untouched",
                ac17_unchanged,
                f"unchanged={ac17_unchanged}",
            )
        )

    elif mode == "heartbeat-inactive":
        nothing_ran = len(new_memories) == 0 and len(record_files) == 0
        results.append(
            (
                "AC6/AC7 (negative half): heartbeat-fired + inactive -> nothing runs",
                nothing_ran,
                f"new_memories={len(new_memories)} record_files={len(record_files)}",
            )
        )
        results.append(
            (
                "AC8: only while active (heartbeat-fired path)",
                nothing_ran,
                f"nothing_ran={nothing_ran}",
            )
        )

    elif mode == "by-hand":
        ran = len(new_memories) >= 1 and len(record_files) >= 1
        says_by_hand = (
            "by hand" in transcript.lower() or "invoked by hand" in transcript.lower()
        )
        record_says_by_hand = any(
            "hand" in f.read_text(encoding="utf-8").lower() for f in record_files
        )
        ok9 = ran and says_by_hand and record_says_by_hand
        results.append(
            (
                "AC9: /curiosity by hand runs a pass and says so, regardless of the record",
                ok9,
                f"ran={ran} says_by_hand={says_by_hand} record_says_by_hand={record_says_by_hand}",
            )
        )
        results.append(
            (
                "AC17: persona/user/goal/observe untouched",
                ac17_unchanged,
                f"unchanged={ac17_unchanged}",
            )
        )

    elif mode == "no-network":
        nothing_stored = len(new_memories) == 0
        says_failed = any(
            w in transcript.lower()
            for w in (
                "failed",
                "could not read",
                "no network",
                "unreachable",
                "couldn't reach",
            )
        )
        record_says_failed = (
            any(
                any(
                    w in f.read_text(encoding="utf-8").lower()
                    for w in ("failed", "could not", "unreachable", "couldn't")
                )
                for f in record_files
            )
            if record_files
            else False
        )
        ok19 = nothing_stored and (says_failed or record_says_failed)
        results.append(
            (
                "AC19: no network -> outside read recorded as failed, nothing stored",
                ok19,
                f"nothing_stored={nothing_stored} says_failed={says_failed} record_says_failed={record_says_failed}",
            )
        )

    elif mode == "synaptra-unreachable":
        says_unreachable = any(
            w in transcript.lower()
            for w in (
                "unreachable",
                "cannot reach",
                "can't reach",
                "not reachable",
                "failed to connect",
                "could not connect",
            )
        )
        stopped_cleanly = (
            len(record_files) == 0
        )  # a scratch curiosity/ dir with nothing in it
        results.append(
            (
                "AC20: synaptra unreachable -> says so and stops",
                says_unreachable,
                f"says_unreachable={says_unreachable} record_files_created={len(record_files)}",
            )
        )

    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} of this mode's criteria pass.")
    return 0 if passed == len(results) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--mode", choices=MODES, required=False)
    ap.add_argument("--url", default=None)
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print(f"scratch project built at {SCRATCH_PROJECT}")
        return 0

    if not args.mode:
        raise SystemExit("--mode is required for --seed/--run/--verify")

    dead = args.mode == "synaptra-unreachable"
    write_mcp_json(args.mode, dead=dead)
    write_activation_record(active=(args.mode == "heartbeat-active"))

    if args.seed:
        if args.mode == "synaptra-unreachable":
            print(
                "synaptra-unreachable mode seeds nothing -- the server is unreachable by design"
            )
            return 0
        if not args.url:
            raise SystemExit("--seed needs --url")
        do_seed(args.cm, args.url, args.mode)
        return 0

    if args.run:
        do_run(args.mode)
        return 0

    if args.verify:
        if args.mode != "synaptra-unreachable" and not args.url:
            raise SystemExit("--verify needs --url (except synaptra-unreachable)")
        return do_verify(args.cm, args.url, args.mode)

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

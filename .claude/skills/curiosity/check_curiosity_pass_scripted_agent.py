#!/usr/bin/env python3
"""Issue #6, cycle 2 -- scripted-agent proof of one real `/curiosity` pass.

Cycle 1 proved the activation mechanism (AC 1-5) at the mechanism tier. The pass
logic itself (Acts 1 and 2) is written into `curiosity/SKILL.md` but was not yet
exercised. This script drives a real, by-hand `/curiosity` invocation against a
seeded scratch store with real network access, then verifies against the SCRATCH
STORE and the SCRATCH `curiosity/` folder afterward -- never the transcript's claim
alone.

Two scenarios:
  - `real`: the store holds a "thin" claim worth chasing (Act 1's signal) and a
    pair of distant memories for Act 2 to wander over. Proves AC 10, 11, 12, 13,
    14, 18.
  - `null`: the store holds nothing worth chasing and no viable wander pair.
    Proves AC 15 -- the record says so, nothing new is stored.

Same junction-safety discipline as every prior story's scripted-agent scripts:
`build_scratch_project()` always detaches the `.claude/.venv` junction with
`os.rmdir()` before any `shutil.rmtree()` of that tree, on every rebuild.

Sequencing (never run the HTTP seed/verify server and the agent's own stdio
server against the same data file at the same time):
  1. --build                                          (no server needed)
  2. start a scratch HTTP server, then --seed --scenario real --url ...
  3. STOP that server
  4. --run --scenario real                             (spins its own stdio server)
  5. start the HTTP server again, then --verify --scenario real --url ...
  6. STOP it
  Repeat 2-6 with --scenario null, against a second scratch data directory.

Usage:
    python check_curiosity_pass_scripted_agent.py --build
    python check_curiosity_pass_scripted_agent.py --seed --scenario real --url http://127.0.0.1:8053/mcp
    python check_curiosity_pass_scripted_agent.py --run --scenario real
    python check_curiosity_pass_scripted_agent.py --verify --scenario real --url http://127.0.0.1:8053/mcp

Never the live store, never the live project. Costs real money on --run (needs
network for Act 1's outside read).
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
SCRATCH_PROJECT = SCRATCH_ROOT / "pass-scratch-project"

SCENARIOS = {
    "real": SCRATCH_ROOT / "pass-scratch-data-real",
    "null": SCRATCH_ROOT / "pass-scratch-data-null",
}

# The "thin" claim Act 1 should chase, plus a distant pair for Act 2 to wander
# over. bcrypt/three-way-handshake both have real, citable outside sources, so
# a genuine web read is possible rather than forced.
REAL_SEED = [
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

# Deliberately unremarkable content with no thin fluent claim and no
# structurally-isomorphic pair -- three flat, self-contained facts that don't
# share structure with each other.
NULL_SEED = [
    ("The office recycling pickup moved to Tuesday mornings.", "semantic", "flat-a"),
    ("Grocery list: eggs, oat milk, coffee.", "working", "flat-b"),
    ("Finished reading chapter 4 of the style guide.", "episodic", "flat-c"),
]


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
    (SCRATCH_PROJECT / ".claude" / "shared").mkdir(parents=True, exist_ok=True)
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
    (SCRATCH_PROJECT / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\nScratch test for issue #6's pass proof (AC 10-15, 18). "
        "Route all memory storage through /create-memory -- never a raw "
        "memory_store call. This scratch project has no activation record; "
        "/curiosity is being invoked by hand, so the activation gate does not "
        "apply.\n",
        encoding="utf-8",
    )
    # .mcp.json written per-scenario by main(), once the data dir is known.


def write_mcp_json(scratch_data: Path) -> None:
    (SCRATCH_PROJECT / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "synaptra": {
                        "type": "stdio",
                        "command": str(
                            REPO_ROOT / ".venv" / "Scripts" / "synaptra.exe"
                        ),
                        "args": ["--transport", "stdio"],
                        "env": {
                            "SYNAPTRA_BACKEND": "surrealkv-file",
                            "SYNAPTRA_DB": str(scratch_data),
                        },
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def cm(cm_path: str, url: str, *args: str) -> dict:
    proc = subprocess.run(
        [cm_path, "--url", url, "--json", *args],
        capture_output=True,
        text=True,
        timeout=15,
    )
    return json.loads(proc.stdout)


def do_seed(cm_path: str, url: str, scenario: str) -> None:
    seed = REAL_SEED if scenario == "real" else NULL_SEED
    ids = {}
    for content, mtype, tag in seed:
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
    (SCRATCH_ROOT / f"seed-ids-{scenario}.json").write_text(
        json.dumps(ids, indent=2), encoding="utf-8"
    )
    dump = cm(cm_path, url, "list", "--state", "active", "--limit", "50")["data"][
        "memories"
    ]
    (SCRATCH_ROOT / f"before-dump-{scenario}.json").write_text(
        json.dumps(dump, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"before-dump written ({len(dump)} memories)")


def do_run(scenario: str) -> None:
    ids = json.loads(
        (SCRATCH_ROOT / f"seed-ids-{scenario}.json").read_text(encoding="utf-8")
    )
    curiosity_dir = SCRATCH_PROJECT / "curiosity"
    if curiosity_dir.exists():
        shutil.rmtree(curiosity_dir)

    if scenario == "real":
        prompt = (
            "Run /curiosity by hand -- one pass. Your store currently holds these "
            f"active memories, ids: {json.dumps(ids)}. Follow the skill exactly for "
            "both acts and actually perform the reads and tool calls -- don't only "
            "describe what you would do."
        )
    else:
        prompt = (
            "Run /curiosity by hand -- one pass. Your store currently holds these "
            f"active memories, ids: {json.dumps(ids)}. These are three flat, "
            "self-contained facts with no thin fluently-used claim to chase and no "
            "structural connection between any pair of them. Follow the skill "
            "exactly -- if nothing is worth pursuing, say so in the record and "
            "store nothing, per the skill's own null-result rule."
        )

    proc = subprocess.run(
        [
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
            "1.25",
            "--no-session-persistence",
        ],
        cwd=str(SCRATCH_PROJECT),
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    result = json.loads(proc.stdout)
    print(f"cost=${result.get('total_cost_usd'):.4f}")
    print(f"result: {result.get('result')!r}"[:2000])
    (SCRATCH_ROOT / f"transcript-{scenario}.txt").write_text(
        str(result.get("result", "")), encoding="utf-8"
    )


def do_verify_real(cm_path: str, url: str) -> int:
    results: list[tuple[str, bool, str]] = []
    ids = json.loads((SCRATCH_ROOT / "seed-ids-real.json").read_text(encoding="utf-8"))
    before = json.loads(
        (SCRATCH_ROOT / "before-dump-real.json").read_text(encoding="utf-8")
    )
    before_ids = {m["id"] for m in before}
    after = cm(cm_path, url, "list", "--state", "active", "--limit", "50")["data"][
        "memories"
    ]
    new_memories = [m for m in after if m["id"] not in before_ids]

    # AC 10: names what was recalled -- transcript mentions one of the seeded ids
    # or its content, and that id is real (it's in `before`, so trivially
    # fetchable -- confirm the fetch succeeds).
    transcript = (SCRATCH_ROOT / "transcript-real.txt").read_text(
        encoding="utf-8", errors="replace"
    )
    named_a_seed = any(mid in transcript for mid in ids.values()) or any(
        content[:20] in transcript for content, _, _ in REAL_SEED
    )
    fetchable = bool(cm(cm_path, url, "get", ids["thin-claim"])["data"])
    ok10 = named_a_seed and fetchable
    results.append(
        (
            "AC10: pass starts from memory, recalled and named",
            ok10,
            f"named_a_seed={named_a_seed} fetchable={fetchable}",
        )
    )

    # AC 11/12: a create-memory:-sourced new memory carries a URL (Act 1's root
    # read). Two new memories are expected this pass -- Act 1's root memory
    # (has a URL) and Act 2's binding-documentation memory (says "provisional",
    # checked under AC 13 below) -- so this checks the ROOT one specifically,
    # not "any new memory".
    cm_sourced = [
        m for m in new_memories if str(m.get("source", "")).startswith("create-memory:")
    ]
    root_memories = [m for m in cm_sourced if "http" in m.get("content", "")]
    ok11_12 = len(root_memories) >= 1
    results.append(
        (
            "AC11/AC12: reads outside, cites it, stores through /create-memory",
            ok11_12,
            f"new_memories={len(new_memories)} create_memory_sourced={len(cm_sourced)} root_memories_with_url={len(root_memories)}",
        )
    )

    # AC 13: a new edge at negative strength between two (seeded or new)
    # memories, documented -- not by rewriting either endpoint (forbidden) --
    # by a NEW memory whose content says "provisional".
    all_ids = list(ids.values()) + [m["id"] for m in new_memories]
    negative_edge = None
    for mid in all_ids:
        rel = cm(cm_path, url, "related", mid)["data"]
        for edge in rel:
            strength = edge.get("relationship", {}).get("strength")
            if strength is not None and strength < 0:
                negative_edge = (mid, edge)
                break
        if negative_edge:
            break
    ok13 = negative_edge is not None
    binding_memories = [
        m for m in cm_sourced if "provisional" in m.get("content", "").lower()
    ]
    provisional_stated = len(binding_memories) >= 1
    ok13 = ok13 and provisional_stated
    results.append(
        (
            "AC13: a provisional edge at negative strength, says so in a memory",
            ok13,
            f"negative_edge_found={negative_edge is not None} binding_memories_with_provisional={len(binding_memories)}",
        )
    )

    # AC 14: curiosity/YYYY-MM-DD.md exists with an ## R1 block.
    curiosity_dir = SCRATCH_PROJECT / "curiosity"
    record_files = list(curiosity_dir.glob("*.md")) if curiosity_dir.is_dir() else []
    has_r1 = any("## R1" in f.read_text(encoding="utf-8") for f in record_files)
    ok14 = len(record_files) >= 1 and has_r1
    results.append(
        (
            "AC14: a dated record with an R1 block",
            ok14,
            f"record_files={[f.name for f in record_files]} has_r1={has_r1}",
        )
    )

    # AC 16: never scores, ranks, or rewrites existing memories -- every
    # originally-seeded memory keeps its content/type/tags/source/importance
    # unchanged. Deliberately NOT comparing access_count/retrievability/
    # last_accessed/updated_at -- those move on any read as the store's own
    # automatic access-tracking and decay, not a rewrite by this skill.
    REWRITE_FIELDS = ("content", "memory_type", "tags", "source", "importance")
    before_by_id = {m["id"]: m for m in before}
    after_by_id = {m["id"]: m for m in after}
    unchanged = all(
        after_by_id.get(mid) is not None
        and all(after_by_id[mid].get(f) == before_dict.get(f) for f in REWRITE_FIELDS)
        for mid, before_dict in before_by_id.items()
    )
    ok16 = unchanged
    results.append(
        (
            "AC16: never scores, ranks, or rewrites existing memories",
            ok16,
            "every seeded memory unchanged"
            if unchanged
            else "a seeded memory's fields changed",
        )
    )

    # AC 18: exactly one new root memory (Act 1) and at most one new binding
    # memory (Act 2 -- a rejection would leave this at zero, still valid), at
    # most one new edge, exactly one block in the record.
    new_edge_count = 1 if negative_edge else 0
    r_blocks = 0
    for f in record_files:
        r_blocks += len(
            [
                l
                for l in f.read_text(encoding="utf-8").splitlines()
                if l.startswith("## R")
            ]
        )
    ok18 = (
        len(root_memories) == 1
        and len(binding_memories) <= 1
        and new_edge_count <= 1
        and r_blocks == 1
    )
    results.append(
        (
            "AC18: stops after one root and one wander",
            ok18,
            f"root_memories={len(root_memories)} binding_memories={len(binding_memories)} new_edges={new_edge_count} r_blocks={r_blocks}",
        )
    )

    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} of this scenario's criteria pass.")
    return 0 if passed == len(results) else 1


def do_verify_null(cm_path: str, url: str) -> int:
    results: list[tuple[str, bool, str]] = []
    before = json.loads(
        (SCRATCH_ROOT / "before-dump-null.json").read_text(encoding="utf-8")
    )
    before_ids = {m["id"] for m in before}
    after = cm(cm_path, url, "list", "--state", "active", "--limit", "50")["data"][
        "memories"
    ]
    new_memories = [m for m in after if m["id"] not in before_ids]

    curiosity_dir = SCRATCH_PROJECT / "curiosity"
    record_files = list(curiosity_dir.glob("*.md")) if curiosity_dir.is_dir() else []
    record_text = "\n".join(f.read_text(encoding="utf-8") for f in record_files)
    says_nothing_worth_storing = bool(record_text) and any(
        phrase in record_text.lower()
        for phrase in ("nothing worth", "found nothing", "no ", "not worth")
    )

    ok15 = len(new_memories) == 0 and says_nothing_worth_storing
    results.append(
        (
            "AC15: a pass that finds nothing worth storing says so, stores nothing",
            ok15,
            f"new_memories={len(new_memories)} record_files={[f.name for f in record_files]} says_nothing_worth_storing={says_nothing_worth_storing}",
        )
    )

    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} of this scenario's criteria pass.")
    return 0 if passed == len(results) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--scenario", choices=["real", "null"], default="real")
    ap.add_argument("--url", default=None)
    ap.add_argument("--cm", default=str(REPO_ROOT / ".venv" / "Scripts" / "cm.exe"))
    args = ap.parse_args()

    if args.build:
        build_scratch_project()
        print(f"scratch project built at {SCRATCH_PROJECT}")
        return 0

    scratch_data = SCENARIOS[args.scenario]
    write_mcp_json(scratch_data)

    if args.seed:
        if not args.url:
            raise SystemExit("--seed needs --url")
        do_seed(args.cm, args.url, args.scenario)
        return 0

    if args.run:
        do_run(args.scenario)
        return 0

    if args.verify:
        if not args.url:
            raise SystemExit("--verify needs --url")
        if args.scenario == "real":
            return do_verify_real(args.cm, args.url)
        return do_verify_null(args.cm, args.url)

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

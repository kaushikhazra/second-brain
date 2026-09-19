#!/usr/bin/env python3
"""Issue #2, AC 24 -- the session-end conformance scan.

"A direct store made outside the four skills is found by the session-end
conformance scan and reported by id."

## Why this reads a FILE, not the live store itself

The live synaptra server for this brain runs over stdio (`.mcp.json`:
`synaptra.exe --transport stdio`), spawned per-session by the Claude Code
harness. There is no standing HTTP endpoint at a known port the way the
scratch servers this story's other check scripts use have one. Starting a
second synaptra process against the SAME `.claude/synaptra-data` file while
the session's own stdio-connected server is live risks a concurrent-access
conflict on the SurrealKV file backend -- a real risk, not a theoretical one,
so this script does not attempt it.

Instead: the live SESSION already holds an open `mcp__synaptra__*` connection.
`/session-end` calls `memory_list` itself (state=active) through that
existing connection, writes the raw results to a JSON file, and THEN runs
this script against that file. This script does no synaptra I/O of its own --
it is pure logic over already-fetched data, read-only by construction (it
never has a write path to lose).

## The signal

/create-memory (cycle 7's own change) passes `source` as
`"create-memory:<model-or-process-id>"`. A direct memory_store call outside
that skill has no reason to set this prefix -- it either leaves `source`
unset (null) or sets something else. So: any ACTIVE memory whose `source`
does not start with `create-memory:` is flagged, by id.

## Usage

    python verify_memory.py <memories.json>
    python verify_memory.py -            # read the JSON from stdin instead

<memories.json> is the raw `{"memories": [...]}` shape memory_list/cm list
returns (or a bare list of memory dicts -- both accepted).

Exit 0: no violations found. Exit 1: one or more violations found (printed by
id, one per line, plus a summary).
"""

from __future__ import annotations

import json
import sys

REQUIRED_PREFIX = "create-memory:"


def load_memories(raw: str) -> list[dict]:
    data = json.loads(raw)
    if isinstance(data, dict) and "memories" in data:
        return data["memories"]
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        return data["data"].get("memories", [])
    if isinstance(data, list):
        return data
    raise ValueError(
        "unrecognised JSON shape -- expected {'memories': [...]} or a bare list"
    )


def find_violations(memories: list[dict]) -> list[dict]:
    violations = []
    for mem in memories:
        if mem.get("state", "active") != "active":
            continue  # archived history isn't this scan's concern
        source = mem.get("source") or ""
        if not source.startswith(REQUIRED_PREFIX):
            violations.append(mem)
    return violations


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <memories.json | ->", file=sys.stderr)
        return 2

    raw = (
        sys.stdin.read()
        if sys.argv[1] == "-"
        else open(sys.argv[1], encoding="utf-8").read()
    )
    memories = load_memories(raw)
    violations = find_violations(memories)

    print(f"Scanned {len(memories)} memories.")
    if not violations:
        print(
            "No conformance violations found -- every active memory carries a "
            f"'{REQUIRED_PREFIX}' source."
        )
        return 0

    print(f"\n{len(violations)} VIOLATION(S) -- stored outside the four memory skills:")
    for mem in violations:
        content_preview = (mem.get("content") or "")[:80]
        print(
            f"  id={mem.get('id')}  source={mem.get('source')!r}  content={content_preview!r}"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())

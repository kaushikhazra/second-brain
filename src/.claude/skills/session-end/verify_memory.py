#!/usr/bin/env python3
"""Issue #2, AC 24 -- the session-end conformance scan. Issue #3 (this file, extended,
not replaced) adds the two-list checks: AC 1, 2, 4, 5, 6, 7, 19.

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

## The two-list checks (issue #3)

Same file-reading discipline as the conformance scan above -- no synaptra I/O of its
own. The input JSON may now also carry a `"resolved"` map: `{"<uuid>": <memory_get
result dict> | null, ...}` for every id that appears in either list's content. The
live session builds this by calling `memory_get` on each id itself, through its own
connection, before invoking this script -- same shape as the conformance scan's
"session fetches, script only reads."

Checked, per tag (`self-map`, `surface-map`):
- **Exactly one active holder** (AC 1, 2). Zero -> reported absent. More than one ->
  all named by id, none loaded (AC 5) -- this script only reports; NOT loading is
  `/session-start`'s job at runtime, not this script's.
- **Content is full uuids, one per line, nothing else -- or whitespace-only, which
  is the valid empty state** (AC 19; the whitespace-only exception is issue #4's:
  a beat writes a single space rather than the empty string, since a raw
  `memory_update` call cannot reliably encode a true empty string). A holder that
  fails this (prose, a partial id, anything else mixed in) is reported malformed
  and its ids are not checked further (a malformed list is not "loaded", so there
  is nothing further to validate about what it points at).
- **Surface map: count <= 25** (AC 7, the issue's only stated numeric cap -- self-map
  has NONE in the issue text; do not invent one. Velasari's own source material
  mentions "N=3" for her self-map, but that is HER current count, stated as a fact
  about her instance, not a portable rule -- her own shapes file frames the self-map
  cap as "a joint decision", never a fixed number, and generalising it into a
  hardcoded limit here would be exactly the kind of anecdote-as-rule
  `assumption.md`'s generalisation rule forbids shipping. Flagged, not guessed.).
- **Every listed id resolves** (AC 4) -- looked up in `resolved`; missing or `null`
  is reported by id, and checking continues (a missing id does not stop the scan).
- **Every self-map id is `identity`-typed** (AC 6) -- checked against `resolved`;
  any other type is reported by id.

## Usage

    python verify_memory.py <memories.json>
    python verify_memory.py -            # read the JSON from stdin instead

<memories.json> is `{"memories": [...], "resolved": {...}}` (both keys optional --
`resolved` absent means the two-list id-level checks are skipped and only reported
as such, not silently passed) or a bare list of memory dicts for the conformance
scan alone (back-compat with issue #2's original shape).

Exit 0: no violations found in EITHER the conformance scan or the two-list checks.
Exit 1: one or more violations found (printed by id, one per line, plus a summary).
"""

from __future__ import annotations

import json
import re
import sys

REQUIRED_PREFIX = "create-memory:"
LIST_TAGS = ("self-map", "surface-map")
SURFACE_MAP_CAP = 25
UUID_LINE_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def load_input(raw: str) -> tuple[list[dict], dict | None]:
    """Returns (memories, resolved). `resolved` is None when the input didn't carry
    one at all (distinct from an empty dict, which means it was provided but empty)."""
    data = json.loads(raw)
    if isinstance(data, dict) and "memories" in data:
        return data["memories"], data.get("resolved")
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        return data["data"].get("memories", []), data.get("resolved")
    if isinstance(data, list):
        return data, None
    raise ValueError(
        "unrecognised JSON shape -- expected {'memories': [...], 'resolved': {...}} "
        "or a bare list"
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


def check_list(tag: str, memories: list[dict], resolved: dict | None) -> list[str]:
    """One tag's findings, as plain report lines -- never raises, always returns
    something printable, per AC 4's 'boot continues' discipline (this is the check
    that discipline is modelled on, even though this script only reports, never
    decides whether to proceed)."""
    findings: list[str] = []
    holders = [
        m
        for m in memories
        if m.get("state", "active") == "active" and tag in (m.get("tags") or [])
    ]

    if not holders:
        findings.append(f"[{tag}] no active holder found (AC 1/2)")
        return findings

    if len(holders) > 1:
        ids = ", ".join(m.get("id", "?") for m in holders)
        findings.append(
            f"[{tag}] {len(holders)} active holders, not exactly one -- names all, "
            f"loads none (AC 5): {ids}"
        )
        return findings  # AC 5: loads neither -- nothing further to check on either

    holder = holders[0]
    content = holder.get("content") or ""
    # "Full uuids, one per line, and nothing else" (AC 1/2/19) -- every line, blank
    # or not, must be exactly one bare uuid. A trailing blank line, stray whitespace,
    # or any prose anywhere in the content makes it malformed.
    #
    # EXCEPTION (issue #4): whitespace-only content (e.g. a single space) is ALSO a
    # valid empty state, not malformed. The heartbeat writes a single space, never
    # the literal empty string, when the last id closes -- a raw MCP `memory_update`
    # call reproducibly fails to encode a true empty-string content value (confirmed
    # across issue #4 cycles 3-6; no CLI or payload workaround reaches around it,
    # since this brain's synaptra runs over stdio with no listening port a CLI
    # could ever connect to). So "empty" for a boot list means content that is
    # either genuinely empty OR entirely whitespace -- both parse to zero ids.
    is_whitespace_only = bool(content) and not content.strip()
    raw_lines = content.splitlines()
    malformed = (
        bool(content)
        and not is_whitespace_only
        and not (raw_lines and all(UUID_LINE_RE.match(line) for line in raw_lines))
    )
    ids = [] if (not content or is_whitespace_only) else list(raw_lines)

    if malformed:
        findings.append(
            f"[{tag}] holder {holder.get('id')}'s content is not full uuids one per "
            f"line and nothing else -- MALFORMED, not loaded (AC 19)"
        )
        return findings

    findings.append(f"[{tag}] holder {holder.get('id')}, count={len(ids)}")
    if tag == "surface-map" and len(ids) > SURFACE_MAP_CAP:
        findings.append(
            f"[{tag}] count {len(ids)} exceeds the cap of {SURFACE_MAP_CAP} (AC 7)"
        )

    if resolved is None:
        findings.append(
            f"[{tag}] no 'resolved' map provided -- id-level checks (AC 4, AC 6) skipped, not silently passed"
        )
        return findings

    for mem_id in ids:
        entry = resolved.get(mem_id)
        if not entry:
            findings.append(f"[{tag}] id {mem_id} does NOT resolve (AC 4)")
            continue
        if tag == "self-map" and entry.get("memory_type") != "identity":
            findings.append(
                f"[{tag}] id {mem_id} is typed '{entry.get('memory_type')}', not "
                f"'identity' (AC 6)"
            )

    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <memories.json | ->", file=sys.stderr)
        return 2

    raw = (
        sys.stdin.read()
        if sys.argv[1] == "-"
        else open(sys.argv[1], encoding="utf-8").read()
    )
    memories, resolved = load_input(raw)
    violations = find_violations(memories)

    print(f"Scanned {len(memories)} memories.")

    problem_found = False

    print("\n--- Conformance scan (issue #2) ---")
    if not violations:
        print(
            "No conformance violations found -- every active memory carries a "
            f"'{REQUIRED_PREFIX}' source."
        )
    else:
        problem_found = True
        print(
            f"{len(violations)} VIOLATION(S) -- stored outside the four memory skills:"
        )
        for mem in violations:
            content_preview = (mem.get("content") or "")[:80]
            print(
                f"  id={mem.get('id')}  source={mem.get('source')!r}  content={content_preview!r}"
            )

    print("\n--- Boot lists (issue #3) ---")
    for tag in LIST_TAGS:
        for line in check_list(tag, memories, resolved):
            print(f"  {line}")
            if any(
                marker in line
                for marker in ("AC 1/2", "AC 4", "AC 5", "AC 6", "AC 7", "AC 19")
            ):
                problem_found = True

    return 1 if problem_found else 0


if __name__ == "__main__":
    sys.exit(main())

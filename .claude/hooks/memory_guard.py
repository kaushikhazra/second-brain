#!/usr/bin/env python3
"""PreToolUse hook for issue #2 -- AC 12 (reserved tags) and AC 26 (short ids on
memory_relate) -- issue #3's holder exemption to AC 12 -- and issue #5's AC 8
(protected ids: the two boot-list holders and the current handoff are never
archived, retyped or unrelated by a dream).

Protocol: JSON on stdin -- {"tool_name": ..., "tool_input": {...}}. Exit 0 to allow,
exit 2 with a message on stderr to block (the message reaches the calling session).

Invoked from .claude/settings.json's PreToolUse hooks, matcher covering
mcp__synaptra__memory_store, memory_update, memory_relate, memory_archive,
memory_delete and memory_unrelate. Stdlib only -- runs with the bare `python` on
PATH, no venv or package dependency, so it works regardless of which project's
interpreter happens to be active.

This is the backstop, not the only place the rule is stated -- /create-memory's own
SKILL.md carries the same refusal in prose. See check_hooks.py for the proof (invokes
this script directly with a bad payload and a good one, per assumption.md's Route 1).

## Issue #3's exemption -- how a legitimate boot-list holder store gets through

`self-map` / `surface-map` are reserved for exactly one holder memory each, but
*creating* that one legitimate holder (issue #3, `/init-brain`, one-time per new
brain) also carries the reserved tag and would otherwise be blocked by the same rule
that protects against an accidental use elsewhere.

This hook CANNOT verify "does a holder already exist" by querying synaptra itself:
the live store runs as an embedded SurrealKV connection (`surrealdb`'s
`BlockingEmbeddedSurrealConnection`), opened once per session and held for the
session's lifetime. A second process opening the same data file concurrently is a
real lock/corruption risk, not a theoretical one -- confirmed against the installed
`surrealdb` package before relying on it, the same discipline issue #2 applied to the
live store being stdio-only.

So, same pattern as `session-end/verify_memory.py` (issue #2): the LIVE SESSION
checks first, through its own already-open connection (`memory_list(tags=[tag],
state="active")`), and writes what it found to a small sentinel file this hook reads
instead of querying anything itself.

**Sentinel file**: `.claude/.list-holder-check.json` (gitignored, machine-local,
transient), written by whatever skill is about to attempt the store/update --
`/init-brain` for the one-time creation case (issue #3's actual writer; the four
memory skills are out of this story's scope to edit, so the sentinel is `init-brain`'s
responsibility, not `/create-memory`'s):

    {"tag": "self-map", "existing_holder_id": null-or-"<uuid>", "written_at": "<iso8601>"}

**Exemption logic** (store or update carrying a reserved tag):
- No sentinel, or its `tag` doesn't match this call's tag, or it's older than
  `SENTINEL_MAX_AGE_SECONDS` -> refused, same as before. Fail closed, not open --
  an exemption that can't be verified fresh is not an exemption.
- Sentinel matches and `existing_holder_id` is `null` -> a `memory_store` (create) is
  allowed; a `memory_update` is still refused (there is nothing to update).
- Sentinel matches and `existing_holder_id` is set -> a `memory_update` whose `id`
  equals it is allowed; a `memory_store` (a second holder) is still refused.
- **The sentinel is deleted after being read, whether it allowed or refused.**
  One-time use -- a stale sentinel left behind after one check can never silently
  authorize a second, unrelated call.

**The update-to-an-existing-holder case mostly doesn't need this at all**: appending
an id to a holder's content is a content-only `memory_update` that never has to pass
`tags` -- omitted, `tags` stays whatever it already was on the server side, and this
hook's reserved-tag check never even triggers (it only inspects `tags` when the call
actually passes one). The sentinel exemption exists for the cases that must pass
`tags`: the one-time create, and an update that also touches tags for some reason.

## Issue #5's protected ids (AC 8)

The self-map holder, the surface-map holder, and the most recent session's
`handoff`-tagged memory must never be archived, deleted, retyped or unrelated by a
dream. Same "the live session checks, the hook only reads a file" discipline as the
sentinel above, but this record is not single-use -- it is rewritten by
`/session-start` on every boot (its step 3 already fetches both holders, its step 5
already fetches the most recent handoff) and read fresh by every guarded call for
the rest of the session, not consumed on first read.

**Record file**: `.claude/.protected-ids.json` (gitignored, machine-local):

    {"self_map_holder": "<uuid>"|null, "surface_map_holder": "<uuid>"|null,
     "handoff_id": "<uuid>"|null, "written_at": "<iso8601>"}

**Missing or unreadable file -> nothing is protected by this rule** (fail OPEN, not
closed) -- unlike the sentinel above, this file is not itself an authorization to do
something destructive; its absence just means the session hasn't booted through
`/session-start` yet (or this brain predates the mechanism), and the two reserved-tag
and full-uuid rules already in this hook still apply regardless. A missing record is
not license to skip those; it only means this ADDITIONAL rule has nothing to check
against yet.

**The rule**:
- `memory_archive`, `memory_delete` on a protected id -> blocked.
- `memory_unrelate` where `source_id` or `target_id` is a protected id -> blocked.
- `memory_update` on a protected id -> blocked, **except** a content-only update
  (no `tags` key at all) to the surface-map holder specifically -- issue #4's
  heartbeat exit-walk writes that id's content every beat, and AC 8 protects
  against a dream reshaping the map, not against the mechanism the map exists to
  support. Any update to the surface-map holder that ALSO touches `tags`, and any
  update at all to the self-map holder or the handoff id, is blocked.

**Not covered by this hook, a known gap**: a retype via the `cm` CLI
(`cm update <id> --type <type>`, the path `/update-memory`'s own text says a type
change actually takes) is a Bash command, not an MCP tool call, and this hook only
ever sees MCP tool invocations -- it cannot inspect or block a Bash command string.
Protecting against a CLI-based retype of a protected id is the dream's own prompt
discipline to hold (a later cycle's Act-2 rewrite), not something this mechanism
can enforce. Noted here rather than silently assumed covered.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

RESERVED_TAGS = {"self-map", "surface-map"}
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

STORE_UPDATE_TOOLS = {"mcp__synaptra__memory_store", "mcp__synaptra__memory_update"}
RELATE_TOOL = "mcp__synaptra__memory_relate"
ARCHIVE_DELETE_TOOLS = {"mcp__synaptra__memory_archive", "mcp__synaptra__memory_delete"}
UNRELATE_TOOL = "mcp__synaptra__memory_unrelate"

SENTINEL_PATH = Path(__file__).resolve().parent.parent / ".list-holder-check.json"
SENTINEL_MAX_AGE_SECONDS = 30

PROTECTED_IDS_PATH = Path(__file__).resolve().parent.parent / ".protected-ids.json"


def load_protected_ids() -> dict[str, str]:
    """Returns {id: role} for every non-null protected id on file. Empty dict (not
    an error) if the file is missing, unreadable, or malformed -- this rule fails
    open on a missing record, per the module docstring's reasoning."""
    if not PROTECTED_IDS_PATH.is_file():
        return {}
    try:
        record = json.loads(PROTECTED_IDS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    roles = {
        "self_map_holder": "self-map holder",
        "surface_map_holder": "surface-map holder",
        "handoff_id": "most recent handoff",
    }
    return {
        record[key]: label
        for key, label in roles.items()
        if isinstance(record.get(key), str) and record[key]
    }


def block(message: str) -> None:
    sys.stderr.write(message)
    sys.exit(2)


def check_holder_exemption(tag: str, tool_name: str, tool_input: dict) -> bool:
    """Reads and consumes the sentinel file. Returns True iff the exemption applies
    for THIS specific call. Always deletes the sentinel if it was read at all, so a
    stale or already-used sentinel can never authorize a second call."""
    if not SENTINEL_PATH.is_file():
        return False
    try:
        sentinel = json.loads(SENTINEL_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    finally:
        try:
            SENTINEL_PATH.unlink()
        except OSError:
            pass

    if sentinel.get("tag") != tag:
        return False

    written_at = sentinel.get("written_at")
    try:
        # written_at is epoch seconds -- simplest to compare, no timezone parsing.
        age = time.time() - float(written_at)
    except (TypeError, ValueError):
        return False
    if age < 0 or age > SENTINEL_MAX_AGE_SECONDS:
        return False

    existing_holder_id = sentinel.get("existing_holder_id")
    if tool_name == "mcp__synaptra__memory_store":
        return existing_holder_id is None
    if tool_name == "mcp__synaptra__memory_update":
        return (
            existing_holder_id is not None
            and tool_input.get("id") == existing_holder_id
        )
    return False


def main() -> int:
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        # Malformed input is not something this hook can safely judge -- allow rather
        # than block on a parse error unrelated to the two rules it enforces.
        sys.stderr.write(f"memory_guard: could not parse hook input ({e}), allowing\n")
        return 0

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {}) or {}

    protected = load_protected_ids()

    if tool_name in ARCHIVE_DELETE_TOOLS and protected:
        target = tool_input.get("id", "")
        if target in protected:
            block(
                f"BLOCKED (AC 8): {target} is the {protected[target]} -- never "
                f"archived or deleted, by a dream or anything else."
            )

    if tool_name == UNRELATE_TOOL and protected:
        source_id = tool_input.get("source_id", "")
        target_id = tool_input.get("target_id", "")
        hit = protected.get(source_id) or protected.get(target_id)
        if hit:
            hit_id = source_id if source_id in protected else target_id
            block(
                f"BLOCKED (AC 8): {hit_id} is the {hit} -- its relations are never "
                f"removed by a dream or anything else."
            )

    if tool_name == "mcp__synaptra__memory_update" and protected:
        target = tool_input.get("id", "")
        if target in protected:
            surface_map_holder = next(
                (i for i, role in protected.items() if role == "surface-map holder"),
                None,
            )
            content_only = "tags" not in tool_input
            if not (target == surface_map_holder and content_only):
                block(
                    f"BLOCKED (AC 8): {target} is the {protected[target]} -- never "
                    f"updated by a dream or anything else, except the heartbeat's "
                    f"own content-only write to the surface-map holder."
                )

    if tool_name in STORE_UPDATE_TOOLS:
        tags = tool_input.get("tags") or []
        reserved_used = [t for t in tags if t in RESERVED_TAGS]
        if reserved_used:
            # Issue #3's exemption: a fresh, matching sentinel from the live session's
            # own memory_list check allows exactly the legitimate holder-creation or
            # holder-update call it was written for. Only meaningful for a single
            # reserved tag at a time -- if a call somehow carries both reserved tags
            # at once, that is not what the exemption was ever meant to cover.
            exempted = len(reserved_used) == 1 and check_holder_exemption(
                reserved_used[0], tool_name, tool_input
            )
            if not exempted:
                block(
                    f"BLOCKED (AC 12): tag(s) {reserved_used} are reserved for the one "
                    f"memory they mark. A memory ABOUT that list takes the '-design' form "
                    f"instead ('self-map-design' / 'surface-map-design'), never the bare "
                    f"reserved tag."
                )

    if tool_name == RELATE_TOOL:
        source_id = tool_input.get("source_id", "")
        target_id = tool_input.get("target_id", "")
        bad = [
            (label, val)
            for label, val in (("source_id", source_id), ("target_id", target_id))
            if not UUID_RE.match(val)
        ]
        if bad:
            names = ", ".join(f"{label}={val!r}" for label, val in bad)
            block(
                f"BLOCKED (AC 26): memory_relate requires FULL uuids on both ends "
                f"(8-4-4-4-12 hex, 36 chars). Rejected: {names}. An 8-char prefix or "
                f"any other shortened id is refused before the call, not after."
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())

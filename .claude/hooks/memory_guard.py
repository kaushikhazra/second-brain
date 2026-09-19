#!/usr/bin/env python3
"""PreToolUse hook for issue #2 -- AC 12 (reserved tags) and AC 26 (short ids on
memory_relate) -- and issue #3's holder exemption to AC 12.

Protocol: JSON on stdin -- {"tool_name": ..., "tool_input": {...}}. Exit 0 to allow,
exit 2 with a message on stderr to block (the message reaches the calling session).

Invoked from .claude/settings.json's PreToolUse hooks, matcher covering
mcp__synaptra__memory_store, memory_update and memory_relate. Stdlib only -- runs with
the bare `python` on PATH, no venv or package dependency, so it works regardless of
which project's interpreter happens to be active.

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

SENTINEL_PATH = Path(__file__).resolve().parent.parent / ".list-holder-check.json"
SENTINEL_MAX_AGE_SECONDS = 30


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

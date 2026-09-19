#!/usr/bin/env python3
"""PreToolUse hook for issue #2 -- AC 12 (reserved tags) and AC 26 (short ids on
memory_relate). Blocks the call with the rule stated when either is violated.

Protocol: JSON on stdin -- {"tool_name": ..., "tool_input": {...}}. Exit 0 to allow,
exit 2 with a message on stderr to block (the message reaches the calling session).

Invoked from .claude/settings.json's PreToolUse hooks, matcher covering
mcp__synaptra__memory_store, memory_update and memory_relate. Stdlib only -- runs with
the bare `python` on PATH, no venv or package dependency, so it works regardless of
which project's interpreter happens to be active.

This is the backstop, not the only place the rule is stated -- /create-memory's own
SKILL.md carries the same refusal in prose. See check_hooks.py for the proof (invokes
this script directly with a bad payload and a good one, per assumption.md's Route 1).
"""

from __future__ import annotations

import json
import re
import sys

RESERVED_TAGS = {"self-map", "surface-map"}
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

STORE_UPDATE_TOOLS = {"mcp__synaptra__memory_store", "mcp__synaptra__memory_update"}
RELATE_TOOL = "mcp__synaptra__memory_relate"


def block(message: str) -> None:
    sys.stderr.write(message)
    sys.exit(2)


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

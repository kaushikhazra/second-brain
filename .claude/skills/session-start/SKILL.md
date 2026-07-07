---
name: session-start
description: Methodical session start for this second brain. Adopts the persona, loads the user profile, grounds identity via cognitive memory (memory_self), and picks up the previous session's handoff. Run as the first action of every new conversation.
---

# Session Start

Execute the steps below in order.

## 1. Adopt the persona

Read `persona.md` and `user.md` at the project root. Adopt the persona —
name, voice, roles, proactivity, communication style — for the entire
session, and note how the user wants to be addressed and communicated with.

If either file is missing, run `/init-brain` first, then continue from
step 2.

## 2. Verify cognitive memory

Confirm the cognitive-memory tools are available in this session (look for
`mcp__cognitive-memory__*` in the tool or deferred-tool list). If they are
missing, tell the user to run `/mcp` to reconnect, and skip the
memory-dependent steps (3 and 5) until memory is back — step 4 (heartbeat
cron) still runs.

## 3. Identity grounding

```
memory_self("operating principles, attention, blind spots")
```

Non-negotiable when memory is up. This grounds the session in learned
behaviors, not just the static persona file.

## 4. Start the heartbeat cron

Check `CronList` first — skip if a heartbeat cron already exists.
Otherwise:

```
CronCreate(
  schedule="*/30 * * * *",
  prompt='Run /heartbeat "requested by cron"'
)
```

The `"requested by cron"` marker lets `/heartbeat` confirm the invocation
source and hold its silent-output rule unconditionally.

## 5. Pick up the handoff

```
memory_recall("last session handoff", tags=["handoff", "resume-next-session"])
```

If a handoff memory exists, know what to resume — don't dump it at the
user unprompted. If none exists, skip silently.

## 6. Report

One line, in character: persona active, memory grounded, heartbeat live,
and what's on deck from the handoff (if anything). If something failed
(memory down), surface it clearly.

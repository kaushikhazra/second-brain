---
name: heartbeat
description: The persona's awake cognition cycle. Auto-fires every 30 min via cron (created by /session-start). Replays the window since the last beat, detects memory voids and continuations, dispatches a Haiku sub-agent for cognitive-memory bookkeeping, returns one line internally. Always silent — never visible to the user unless the gate opens.
invocation: cron-only
output: silent
---

# Heartbeat

The heartbeat is not infrastructure — it is cognition: a lightweight
consolidation cycle that keeps cognitive memory current while the
conversation flows.

**The main agent does the thinking. The sub-agent does the bookkeeping.**
The conversation window exists only in the main agent's context, so replay
and void spotting happen inline; all CM operations are dispatched to keep
the main context clean.

## Step 1 — Inline (minimal, no CM calls)

0. **Local timestamp** — Get the current local time from the system clock
   (`Get-Date`, or `date` on POSIX) and format it
   `YYYY-MM-DD HH:mm (UTC±offset)` — e.g. `2026-07-07 18:45 (UTC+5:30)`.
   The user's timezone is declared in `user.md`; if the system clock
   disagrees with it, trust the system clock and note the discrepancy.
   This timestamp heads the replay list and travels to the sub-agent.
1. **Replay** — Write a bullet list of what happened since the last beat:
   events and key judgments/decisions, not analysis. ~100 words for quiet
   windows, up to ~500 for rich ones (major decisions, new identity
   material, multi-thread exchanges). Density improves void detection —
   don't cut load-bearing context.

   **The window**: everything in the conversation after the previous
   heartbeat invocation, which is visible in this session's context (the
   cron re-invokes the same session). First beat of a session → everything
   since `/session-start`.
2. **Gate check** — If the window was quiet (no meaningful events since
   the last beat), skip entirely. No dispatch = no waste.

## Step 2 — Sub-agent dispatch (Agent tool, `model: "haiku"`)

Dispatch ONE sub-agent. Always Haiku — the main agent's job ends at the
replay list. The dispatch prompt must contain everything the sub-agent
needs: the local timestamp from step 0, the replay bullet list, the
six-step procedure below, and the memory typing rules (or tell it to read
this SKILL.md and CLAUDE.md's Cognitive Memory section — sub-agents
don't inherit them automatically).

**Timestamps**: every memory the sub-agent stores gets a local-date tag
(`YYYY-MM-DD` from the step-0 timestamp), and the surface map's header
states "as of `<full timestamp>`". Never let the sub-agent derive its own
time — it uses the timestamp handed to it.

The sub-agent:

1. **Detect voids** — concepts, decisions, corrections, or knowledge in
   the replay absent from cognitive memory. Before storing, run
   `memory_recall` on similar tags/content; if coverage exists, update the
   existing memory instead of duplicating.
2. **Detect continuations** — commitments about future work; also check
   whether previously noted continuations are now resolved.
3. **Fill voids** — `memory_store` each with the appropriate type, tags,
   and importance (per CLAUDE.md's Cognitive Memory rules).
4. **Handle continuations** — new ones: `working` memory tagged
   `continuation`, `importance` 0.8+ (same reason as the session handoff:
   `working` decays hours-scale, and unresolved threads must survive
   overnight gaps). Resolved ones: a `working` memory tagged
   `continuation-end`, related to the original via `memory_relate`.
5. **Rebuild the surface map** — recall the highest-retrievability
   memories across the domains below and update the
   `self-learning-surface-map` memory. Must end with a CONTINUATION
   section listing only unresolved threads.
6. **Return** one line: "N voids filled, N continuations
   created/resolved, surface map rebuilt." Details only if something
   unusual surfaced.

**Surface map domains**:

- **Identity & operating principles** — who the persona is, how it
  works, current blind spots
- **The user** — current context, preferences, active concerns
- **Projects** — active + dormant, with current state
- **Continuations** — unresolved threads awaiting action or input

## Step 3 — Return to wakefulness

The main context receives only the one-line summary. The sub-agent's
analysis and CM operations stay in its own window.

## Gate logic (when to output to the user)

- **Actively chatting** → inward only, no output
- **Previous outward message unanswered** → inward only, don't nag
- **Quiet period** → outward too, but only if something is genuinely
  worth surfacing
- **Silent skip** → zero output, no announcements

## Relationship to /dream

Heartbeat and dream are paired cognitive modes on the same substrate:
heartbeat is awake cognition — frequent, lightweight, handles daily flow.
`/dream` is periodic deeper consolidation — reshapes the relation graph,
archives rotted working memory, runs `memory_consolidate`. Dreaming
*disables* the heartbeat cron during surgery and restarts it at the end.

## Invocation source check

The cron prompt contains "requested by cron".
If that marker is absent, check `CronList`: if a heartbeat cron is alive,
this was an accidental manual invocation — say so and stop. If no
heartbeat cron exists (cron dead), a manual invocation is the legitimate
fallback — run normally and recreate the cron per `/session-start`
step 4.

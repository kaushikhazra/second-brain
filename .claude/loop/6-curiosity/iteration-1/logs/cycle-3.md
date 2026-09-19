# Cycle 3 — 2026-09-20 ~00:35–00:55 +0530

**Branch:** `feature/6-curiosity` (read from `git branch --show-current`, confirmed
clean and up to date with origin before starting).

## What moved

Built `check_curiosity_invocation_scripted_agent.py` — five scripted-agent runs,
each against a fresh copy of the same seeded store, covering the two invocation
paths and the remaining boundary/failure criteria:

- **`heartbeat-active`** — `/curiosity "requested by heartbeat"`, record active.
  A pass ran (2 new memories, 1 record block), and the four protected files
  (`persona.md`, `user.md`, and a stand-in skill's `goal.md`/`observe.md`) hashed
  identical before and after. **AC 7 positive half, AC 17.**
- **`heartbeat-inactive`** — same marker, record inactive. The transcript said
  plainly: gate checked, found off, stopped — and the store/`curiosity/`
  confirmed it: zero new memories, zero record files. **AC 6, AC 7 negative
  half, AC 8's "only while active" half.**
- **`by-hand`** — `/curiosity`, no marker, record inactive. A pass ran anyway
  (the activation record does not gate the by-hand path, exactly as `SKILL.md`
  says), and both the reply and the record block said "invoked by hand."
  **AC 9, AC 17 again.**
- **`no-network`** — by-hand, with tools denied. **First attempt** denied only
  `WebSearch,WebFetch` and found a real gap: the model reached the same OWASP
  URL through `curl` via `Bash` instead ("fetched live via curl, not a cached
  summary," its own record said) — bypassPermissions mode leaves Bash wide open
  regardless of the web-tool denylist. Not a check-script bug: this is a
  genuine escape hatch a real, network-restricted environment could also hit if
  it only filtered by tool name. Fixed by denying `Bash` and `Task` too — no
  network-capable path left in this scratch project. Reran clean: the model hit
  "no web-search/fetch tool is available," stopped Act 1 there, stored nothing,
  and recorded the failure. **AC 19.**
- **`synaptra-unreachable`** — `.mcp.json` pointed at a nonexistent executable
  (same technique as story #5's AC 17 proof). The model reported the
  `CONNECTION_CLOSED` failure, quoted the skill's own hard-stop rule verbatim,
  and stopped before Act 1 — zero record files. **AC 20.**

**AC 8's other half — never fires mid-conversation or mid-task — resolved by
citation, not a new scripted run.** This is not a claim curiosity's own text can
prove: curiosity only re-checks `is_active` (cycle 1's design) and trusts its
caller on idleness, by design. The idleness guarantee itself is the harness's
own scheduler behavior: `CronCreate`'s documented runtime rule is that a
recurring job "only fires while the REPL is idle (not mid-query)." Since
`/curiosity`'s only non-by-hand invocation path is entirely inside `/heartbeat`,
which is itself cron-fired only (`CLAUDE.md`'s own Session Lifecycle table:
"Never manually — cron-fired only"), the chain cron → heartbeat → curiosity can
only ever run when the session is idle — which is definitionally not
mid-conversation and not mid-task. This is the same substrate-behavior citation
Velasari accepted for story #4's AC 20 (no double-run), applied here to the
other half of AC 8. Mechanism tier, the strongest this story's `observe.md`
recognises — not a scripted proof because there is nothing to script; the
platform itself is the mechanism.

## Criteria met, out of 20

**First bucket (demonstrably met, check fails when the behaviour is removed):**
AC 1–5 (cycle 1) + AC 10–16, 18 (cycle 2) + AC 6, 7, 8, 9, 17, 19, 20 (this
cycle) — **20/20.**

**Second bucket:** none remaining.

**Third bucket:** none remaining.

**All 20 acceptance criteria for issue #6 are demonstrably met.**

## Regression — full line, after the above

```
check_shapes.py           5/5
check_hooks.py             27/27
check_session_start.py     2/2
check_verify_memory.py     12/12
check_heartbeat.py         3/3
check_dream.py             5/5
check_recall_session.py    12/12
check_curiosity.py         7/7
```

All pass.

## Assumptions

None of `assumption.md`'s standing inputs changed this cycle.

## Next

None — the loop converges here. Deleting the cron, posting the closing comment
on issue #6 with the final numbers, pushing, and telling Velasari.

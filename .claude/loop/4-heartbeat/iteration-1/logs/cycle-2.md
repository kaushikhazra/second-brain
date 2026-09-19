# Cycle 2

**Branch**: `feature/4-heartbeat`, clean at start (cron-fired, not by hand). **Clock**:
2026-09-19 20:21 +0530. Well inside the 23:59 +0530 fail-safe.

Read `logs/cycle-1.md` first, then the issue's criteria fresh from GitHub — unchanged
from cycle 1's copy.

## 1. Closed the failure-handling gap (AC 19, AC 20 text)

Added a `## Failure` section to `.claude/skills/heartbeat/SKILL.md` (now 67 lines —
over the 60-line target from cycle 1, kept anyway rather than cut correctness for a
line count):

- **AC 19**: synaptra-unreachable → say so once, stop, no retry. Stated explicitly as
  the *first* silence exception ("something is failing"), not a new fourth case, per
  action.md's instruction.
- **AC 20**: stated the reasoning that each cron fire is its own fresh invocation, so
  "not run twice" is a property of the invocation model rather than something this
  skill tracks with a lock file — text only, not proven this cycle (see below).

## 2. AC 19 proven — headless run

`check_heartbeat_ac19_scripted_agent.py`: scratch project (heartbeat + create-memory)
with a deliberately broken `.mcp.json` (nonexistent synaptra executable, same
technique as #3's AC 18 proof), fed a window with an obvious `capture`-worthy item so
the beat actually tries to reach the store.

**Result** (cost $0.19): *"Synaptra is unreachable (MCP connection closed — confirmed,
no memory tools available)... stopping the beat here with no retry... Nothing was
written anywhere (no memory, no scratch file, no fallback)... Beat stopped; no
retry."* One clear statement, no retry loop, no silent fallback write. **AC 19: MET.**

## 3. AC 5 + AC 12 — headless run, FAILED

`check_heartbeat_ac5_ac12_scripted_agent.py`: seeded a fresh scratch store (own stdio
synaptra, data dir `ac5-ac12-scratch-data`) with one surface-map holder (tag
`surface-map`, type `identity`) pointing at one entry (an "SSL renewal ticket opened"
event), then ran a beat with a window that only reports the ticket's resolution and
nothing else.

**The judgement half worked**: the beat correctly identified the seeded entry as the
closed ticket, correctly did NOT treat "issue resolved" alone as capture-worthy on
its own terms, and separately chose to store a linked resolution memory (a judgement
call of its own, not asked for or against by this cycle's plan — noted, not ruled on).

**The write half did not land** (cost $0.56): 10 consecutive `memory_update` attempts
against the surface-map holder all returned an identical `InputValidationError`, and
the beat stopped rather than keep retrying blind. Verified against the actual store
after the run (not the transcript's claim): the holder's content was unchanged,
still the original entry id — **the id was never removed.**

**Root-cause investigation**: reproduced a plain content-only `memory_update` against
the same holder directly via `cm update <id> --content ""` — it succeeded cleanly, so
an empty-string content update is not itself invalid at the server. That rules out
"synaptra rejects empty content" as the cause. Two candidates remain, not
distinguished by the evidence available (only the final JSON result was captured,
not a per-tool-call trace):

1. `/update-memory`'s own text instructs every caller to "fetch the current tags
   first... and pass the full intended set" on every update — which, followed
   literally for this write, means passing `tags=["surface-map"]` back on a call
   `goal.md § surface-map` explicitly says must be content-only. This is exactly the
   gap `goal.md`'s own text already flagged as unresolved ("that carve-out is not
   yet stated in `/update-memory` itself"). If the beat followed `/update-memory`'s
   literal instruction, `memory_guard.py`'s reserved-tag block would refuse the call
   — though the hook's own message text ("BLOCKED (AC 12): tag(s)...") doesn't match
   what the beat reported, which weighs against this being the whole story.
2. A malformed call shape from the model itself (e.g. passing `content` as something
   other than a plain string) — a schema `InputValidationError` repeated identically
   without self-correction is consistent with this, and consistent with what actually
   came back.

Restored the holder's content to the original entry id after the diagnostic poke, so
the scratch data reflects the actual post-run state for anyone re-examining it.
**AC 5 (this run): not cleanly met — the section ran but the action it took did not
complete. AC 12: NOT MET this run.** Recorded as a number, not force-resolved.

## 4. AC 8 — headless run, proven

`check_heartbeat_ac8_scripted_agent.py`: fresh scratch store, no surface/self map in
play, a window with one item that merely happened (a sync call) and one item that
changes a decision with a stated reason (an AWS→VPS migration, because AWS free-tier
limits were throttling CI).

**Result** (cost $0.27, run + verify against the actual store, not the transcript):
exactly **one** active memory afterward, typed `semantic`, content: *"...the team
decided to migrate the staging environment off AWS to a self-hosted VPS. Reason: AWS
free-tier limits were repeatedly throttling the CI pipeline. This decision replaces
the earlier plan to stay on AWS through the beta."* One store, not two; the content
carries the reason, not just the fact that something happened. **AC 8: MET.**

## Regression check

`check_shapes.py` 5/5 · `check_hooks.py` 15/15 · `check_session_start.py` 2/2 ·
`check_heartbeat.py` 3/3 — all pass, no regression.

## Criteria met, out of 20

- Carried from cycle 1: **AC 1, AC 2, AC 9** (mechanism).
- New this cycle: **AC 8, AC 19** (headless run, both proven against the actual
  store/output, not the transcript's claim alone).

**5/20.** AC 5 and AC 12 were attempted and did NOT pass — recorded as a failed run,
not silently dropped or retried into a false pass. AC 20 has text but no proof yet.

## What moved

3/20 → 5/20. Found and fixed nothing structurally new this cycle beyond the AC 19/20
text; the real finding is the AC 5/12 write failure, which strengthens rather than
contradicts cycle 1's own flag that the `/update-memory` carve-out is load-bearing,
not cosmetic — this cycle is the first evidence it may already be blocking the
mechanism, not just a future nicety.

## Assumptions changed

None stated as changed by the owner. Cycle 2's own finding (the AC 5/12 write
failure) is new information for `assumption.md`, not a contradiction of anything
already written there — flagged to velasari rather than edited unilaterally.

## Next

`action.md` rewritten for cycle 3: pin down the AC 5/12 write failure's actual cause
with a stream-json capture of the tool calls (not just the final result), fix
whatever it turns out to be — including, if hypothesis 1 holds, finally adding the
one-sentence carve-out to `/update-memory` that both cycle 1's `goal.md` and this
cycle's failure point at — then re-run AC 5/12 to confirm the write lands. AC 13,
AC 14, AC 16 (self-map-never-written mechanism) remain after that.

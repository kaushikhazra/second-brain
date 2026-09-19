# Cycle 2

**Time:** 2026-09-19 19:07 +0530 (read via `date`) — the cron's own first `:00`
boundary fire, delayed until cycle 1 (run by hand) finished at ~19:05. Not a
duplicate; genuinely cycle 2.

**Branch:** `feature/3-boot-lists` (confirmed via `git branch --show-current`)

## Reply received, before this cycle's own work

Velasari confirmed both findings flagged at the end of cycle 1:

1. **No self-map cap.** *"No cap on the self map; report the count, never enforce
   one. Correct action.md's error in your log and move on."* Already implemented
   correctly in cycle 1's code (no cap enforced); the correction was already recorded
   in `logs/cycle-1.md`'s own text. Nothing further to change.
2. **`init-brain`'s missing persona-storing round — full design given.** After
   `init-brain` writes `persona.md`, it stores the persona into synaptra as
   `identity` memories through `/create-memory`, **persona-shaped, a few nodes not a
   dump**: who the brain is (name and nature), what it does (roles), how it speaks
   (voice). The self map is then seeded with exactly those ids. The existing restore
   path already reads from synaptra, so a restored brain regrows its files from the
   same memories. **Gate the whole round on "no active memory carries `self-map`"**
   (keeps AC 16 true). **Under 30 lines, one place.** This is now cycle 3 or 4's
   concrete spec, not cycle 1's open question — recorded here for continuity rather
   than re-derived later.

## Criteria re-read from GitHub, before the diff and before cycle 1's log

20 acceptance criteria confirmed via `gh issue view 3 -R kaushikhazra/second-brain`,
unchanged.

## `assumption.md` re-read fresh — no new commit; both replies stayed crosschat-only

## Round 1 — `session-start`'s two-list wiring

Rewrote steps 3 and 5 of `.claude/skills/session-start/SKILL.md`; steps 0, 1, 2, 4, 6
kept, with step 2 and step 6 updated only where the boot-list change actually touches
them (step 2 now names the three fetches for AC 18's "which of the three failed";
step 6's report line now names the list counts instead of "memory grounded").

**Step 3 → the two boot lists** (was: `memory_self("operating principles...")`).
Now `memory_list(tags=["self-map"], state="active")` and the same for
`surface-map`, each with: zero-holder handling, multiple-holder handling (name all,
load neither — AC 5), content-shape validation (full uuids, one per line, nothing
else, malformed otherwise — AC 19), per-id `memory_get` with unresolved-id reporting
(AC 4), self-map's `identity`-type check (AC 6), and the surface map's count report
with "a short list is correct" stated explicitly (AC 7).

**Step 5 → the handoff by tag** (was: `memory_recall("last session handoff", ...)`).
Now `memory_list(tags=["handoff"], state="active")`, most recent by `created_at`
(AC 10) — explicitly NOT subject to the "exactly one" rule the two lists have, since a
handoff is written every session-end and accumulating several is normal. No handoff
at all is reported and boot continues (AC 11).

`memory_self` is now removed from `session-start` entirely — nothing else in the
skill used it, so a vestigial call with no stated purpose would have been worse than
removing it (per `observe.md`'s own warning: "`memory_self` may stay for something
else only if the skill says what").

## Round 2 — proving AC 3 structurally

`.claude/shared/memory/check_session_start.py`, new: greps the skill's own fenced
code blocks (not free prose, which is allowed to *mention* the forbidden tools when
explaining why they're wrong) for `memory_list(tags=...)` used as an actual
invocation, and confirms `memory_self(...)`/`memory_recall(...)` never appear as one.

```
[PASS] AC3: memory_list(tags=...) used as the boot fetch, at least twice: found 3 fenced memory_list(tags=...) block(s)
[PASS] AC3: memory_self(...)/memory_recall(...) never invoked as the boot mechanism: none found

2/2 of this script's criteria pass.
```

This is a structural proof — the skill's prose no longer instructs the forbidden
mechanism. It does **not** prove the described runtime behaviors (AC 4, 5, 6, 7, 10,
11, 18) actually execute correctly when `session-start` runs — that needs a
scripted-agent test, queued for a later cycle rather than rushed into this one on top
of an already-substantial skill rewrite.

**Not double-counted**: cycle 1's `check_verify_memory.py` already proved the same
*detection logic* (multiple-holder naming, malformed content, cap enforcement, id
resolution, self-map typing) as a script, and counted AC 4, 5, 6, 7 on that basis —
the precedent this whole project has used since issue #2 (a substrate-level proof
standing in for a skill's promised behavior). `session-start`'s prose now describes
the same logic consistently, but that consistency isn't new evidence; AC 4/5/6/7 stay
at their cycle-1 count, not re-counted here. AC 10, 11, 18 remain **not yet proved for
session-start specifically** — the criteria are about boot behavior, and nothing this
cycle observed `session-start` actually booting.

## Round 3 — regression check, per `loop.md`

```
check_shapes.py:        5/5 pass, unchanged.
check_hooks.py:        15/15 pass, unchanged.
check_verify_memory.py: 11/11 pass, unchanged.
```

## Criteria met, out of 20

**Met, with a check shown to fail when broken (8, up from 7):**
- AC 1, 2, 4, 5, 6, 7, 19 (cycle 1, unchanged)
- **AC 3** — new this cycle, `check_session_start.py`.

**Implemented but not proved for `session-start`'s actual boot behavior:** AC 10, 11,
18 — the prose is right; nothing has observed it run yet.

**Not started:** AC 8, 9, 12, 13, 14, 15, 16, 17, 20 — `session-end` and `init-brain`
untouched.

**Number this cycle moves: 7 → 8 / 20.**

## Branch and time

Branch: `feature/3-boot-lists`. Cycle started 2026-09-19 19:07 IST, finalized ~19:10
IST, well inside the 23:30 fail-safe.

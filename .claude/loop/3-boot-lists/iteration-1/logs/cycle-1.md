# Cycle 1

**Time:** 2026-09-19 ~19:00 +0530 (read via `date`)
**Branch:** `feature/3-boot-lists` (confirmed via `git branch --show-current`)

## Baseline (before any changes)

**`session-start`'s current identity/handoff mechanism** (to be replaced by later
cycles, not this one):
```
line 3:   description mentions "grounds identity via Synaptra (memory_self)"
line 132: memory_self("operating principles, attention, blind spots")
line 156: memory_recall("last session handoff", tags=["handoff", "resume-next-session"])
```

**`init-brain`'s persona-storing round — a real finding, not assumed.**
`assumption.md` says the self-map seeding goes "after the round that stores the
persona memories." **No such round currently exists.** Read the full file (376 lines):
`init-brain` writes `persona.md`/`user.md` as local files only. Its "Round 0 — Restore
from Synaptra" *reads* (`memory_recall`) if memory already knows the persona; nothing
in the file ever *writes* a persona/identity memory into synaptra for a genuinely new
brain. AC 15 ("the self map holding the persona memories it just wrote") presupposes
those memories exist — they don't yet.

**This does not block cycle 1** (scoped to the hook exemption and `verify_memory.py`
only, per `action.md` — `init-brain` isn't touched this cycle). But it changes what a
later cycle touching `init-brain` has to do: not just "seed the self map after the
existing persona-storing round," but **add a persona-storing round first**, via
`/create-memory`, typed `identity`, then seed the self map with those ids right after.
Flagged here and will be flagged to Velasari — this is bigger than "one place," and
`assumption.md`'s framing assumed infrastructure that isn't there.

**`verify_memory.py`'s current usage** (issue #2's conformance-scan-only version):
```
Usage: python verify_memory.py <memories.json>
       python verify_memory.py -            # read the JSON from stdin instead
```
Single-purpose: flags a memory whose `source` doesn't start with `create-memory:`.
No list-shape checks yet — this cycle's job.

**`check_shapes.py`:**
```
5/5 pass — AC1, AC2, AC3, AC4, AC23 all PASS.
```

**`check_hooks.py`:**
```
6/6 pass — AC12 (both bad payloads blocked, good payload allowed), AC26 (bad blocked,
good allowed), unrelated tool unaffected.
```

Both green before any change this story makes — the actual baseline to not regress.

## Criteria read from GitHub (issue #3), before the diff

20 acceptance criteria confirmed via `gh issue view 3 -R kaushikhazra/second-brain`,
matching `goal.md`'s summary and `observe.md`'s five flagged risks exactly.

## Round 1 — the hook exemption, and a real technical constraint solved first

`assumption.md` says "extend `memory_guard.py`" for the exemption but doesn't specify
how the hook is supposed to know whether a holder already exists. Investigated before
designing: this synaptra install's live store is an **embedded** SurrealKV connection
(`surrealdb`'s `BlockingEmbeddedSurrealConnection`), held open for the session's whole
lifetime — confirmed by reading the installed `surrealdb` package, not assumed. A
`PreToolUse` hook querying the same data file from a second process is exactly the
concurrent-access risk issue #2 was careful to avoid everywhere else. The hook cannot
safely check live state itself.

**Two findings resolved this, without touching any of the four memory skills** (out of
this loop's scope):

1. **The update-to-an-existing-holder case mostly doesn't need an exemption at all.**
   Appending an id to a holder's content is a content-only `memory_update` that never
   has to pass `tags` — omitted, `tags` stays server-side unchanged, and the existing
   hook's reserved-tag check never triggers in the first place (it only inspects
   `tags` when the call actually passes one). A documentation note for whichever
   future cycle implements the append logic, not a code change.
2. **The create case** genuinely needs an exemption, and gets it the same way issue
   #2's `verify_memory.py` solved an identical problem: a **sentinel file**
   (`.claude/.list-holder-check.json`, gitignored, single-use, max age 30s) that the
   *calling skill* writes after checking `memory_list` itself through its own
   already-open connection — no second synaptra process. The sentinel isn't written
   by `/create-memory`'s own prose (out of scope); it's `/init-brain`'s responsibility,
   since `/init-brain` is this story's to touch and is the one orchestrating "check
   for a holder, then create it" in the first place. The hook reads and *deletes* the
   sentinel on every check, whether it allows or blocks — one-time use, so a stale
   sentinel can never silently authorize an unrelated later call.

Extended `.claude/hooks/memory_guard.py` with `check_holder_exemption()`. One bug
along the way: a formatter stripped `import time` as unused at the point it was
added (before the function using it existed yet) — re-added once genuinely used.

Extended `check_hooks.py` with 9 new cases: no sentinel, fresh sentinel for a create,
single-use consumption, update with no holder yet, update to the holder, a second
create attempt with a holder present, update to a non-holder id, a stale sentinel, a
mismatched tag. All pass:

```
15/15 of this script's criteria pass.
```

## Round 2 — `verify_memory.py`'s list half

Extended (not replaced) issue #2's conformance scan. Input JSON now optionally
carries `"resolved"`: `{"<uuid>": <memory_get result> | null}` for every id on either
list — same "session fetches, script only reads" shape as the conformance scan
already used.

**A real discrepancy caught before implementing it, not after**: `action.md` states
"count ≤ cap (3 for self, 25 for surface, ceilings)". Checked both the issue's own AC
text and Velasari's source material before trusting this. Issue #3's AC 1, 2, 6 state
no self-map count cap at all — only AC 7 states a cap, and only for the surface map
(25). Velasari's own `session-start/SKILL.md` says "N=3" for her self-map, but reads
as a **fact about her current instance** ("the persona and nothing else"), not a
stated maximum — her own `memory-shapes.md` frames the self-map cap as "a joint
decision," never a fixed number. Generalising her personal count into a hardcoded
limit here would be exactly the anecdote-as-rule `assumption.md`'s own generalisation
principle forbids shipping. **Implemented no self-map cap.** Flagging this to
Velasari rather than silently picking either reading.

`check_list()` added: per tag, finds the holder(s) (AC 1/2, AC 5 for the
more-than-one case), validates content shape (AC 19 — full uuids, one per line,
nothing else, checked exactly, not loosely), the surface-map cap (AC 7), and — given
a `resolved` map — every id's resolution (AC 4) and, for self-map, its type (AC 6).

`check_verify_memory.py` written, 11 cases covering every criterion above plus a
positive control (a short surface map is NOT a violation, per AC 7's "treats a short
list as correct") and a regression check that AC 24's conformance scan still works
unchanged:

```
11/11 of this script's criteria pass.
```

**One bug, the same class as three prior cycles across issue #2**: the new check
script's path to `verify_memory.py` was off by one `.parent` — `.claude/shared/memory/`
needs exactly three `.parent` calls to reach `.claude/`, and this is now the fourth
time this exact miscount has happened (`check_hooks.py`, `check_conformance_scan.py`,
and now this one — `check_ac8/batch_a/b/c` got it right by then). Worth naming
explicitly as a pattern this far in, not just fixing quietly again.

## Round 3 — regression check, per `loop.md`'s explicit "do not regress #2"

```
check_shapes.py:  5/5 pass, unchanged.
check_hooks.py:  15/15 pass (9 new cases + the 6 from #2, all still passing).
```

## A finding from the baseline, not this round's work but worth restating here

`init-brain` currently never stores persona/identity memories into synaptra for a new
brain — confirmed by reading the full file, not assumed. This means a future cycle
touching `/init-brain` has to **add** a persona-storing round before it can seed the
self map with those ids, not just seed after an existing one. Flagging this to
Velasari now rather than waiting until the cycle that hits it.

## Criteria met, out of 20

**Met, with a check shown to fail when broken (7):**
- **AC 1, AC 2** — `check_verify_memory.py` proves "exactly one holder" is detected
  (both the zero-holder and multiple-holder cases), and `check_hooks.py`'s exemption
  proves the create-time mechanism that makes "exactly one" achievable at all once
  `/init-brain` uses it.
- **AC 4** — unresolved id reported by id, scan continues.
- **AC 5** — multiple holders named by id, neither counted as loaded.
- **AC 6** — a non-`identity` self-map id reported.
- **AC 7** — the surface-map cap enforced; a short list correctly NOT flagged.
- **AC 19** — malformed content (not full uuids, one per line, nothing else) reported,
  not loaded.

**Not started:** AC 3, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20 — everything
touching `session-start`, `session-end`'s own invocation of the script, or
`init-brain`, all explicitly out of this cycle's scope per `action.md`.

**Number this cycle moves: 0 → 7 / 20.**

## Branch and time

Branch: `feature/3-boot-lists` (`git branch --show-current`). Cycle started
2026-09-19 ~19:00 IST, finalized ~19:05 IST, well inside the 23:30 fail-safe.

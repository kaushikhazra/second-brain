# Action

**Cycle 2. `session-start`: replace `memory_self`/`memory_recall` with the two-list
fetch and the tag-based handoff pickup.**

Cycle 1 landed the hook exemption and `verify_memory.py`'s list half (7/20). Neither
touched `session-start`, `session-end`, or `init-brain`. This cycle does exactly one
of those three, per issue #2's own precedent (one skill per cycle beats three thinly).

Read the issue's criteria fresh (`gh issue view 3 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-1.md`. Re-read `assumption.md` fresh — check for a
reply on the two things flagged last cycle: the self-map cap discrepancy, and the
`init-brain` persona-storage gap.

## What changes in `session-start/SKILL.md`

Per `assumption.md`: keep everything that isn't identity grounding or handoff pickup
(persona adoption, user profile, synaptra health, the heartbeat cron, the repair
path). Replace exactly two things:

1. **Step 3 (currently `memory_self(...)`)** → `memory_list(tags=["self-map"],
   state="active")` (AC 3). Then, per each criterion:
   - Zero or multiple holders → name them, load neither, say what to do (AC 5) —
     mirror `verify_memory.py`'s own logic in prose, don't restate its code.
   - One holder → `memory_get` each id (AC 4: report an unresolved id by id, boot
     continues) → check each is `identity`-typed, report otherwise (AC 6).
   - Then the surface map, same shape (`memory_list(tags=["surface-map"], ...)`,
     AC 7's cap-report, AC 5's multiple-holder case again for this tag).
   - `memory_self` may stay ONLY if the skill states what it's for and it is not the
     boot mechanism (per `observe.md`'s own warning) — decide whether session-start
     still needs it for anything at all; if not, remove it rather than leave a vestigial
     call with no stated purpose.

2. **The handoff pickup (currently `memory_recall("last session handoff", tags=[...])`)**
   → fetch by tag only (AC 10): `memory_list(tags=["handoff"], state="active")`,
   most recent by `created_at`, load it after the two lists. A brain with none yet is
   told so, boot continues (AC 11).

3. **AC 18** — with synaptra unreachable, boot says which of the three fetches (self
   map, surface map, handoff) failed and continues on the persona file alone. This is
   new prose, not a replacement of existing text — check whether session-start
   already has ANY synaptra-unreachable handling before assuming there's a gap.

Update the frontmatter `description` to match (currently says "grounds identity via
Synaptra (memory_self)" — no longer true once this lands).

## Prove it

Same methodology as issue #2's `/read-memory`/`/update-memory` proofs: a scratch
project carrying `session-start`'s new logic isn't really testable as a *skill* the
way `create-memory` was (session-start is the FIRST thing a session runs, harder to
isolate) — decide the right proof shape when actually building this, don't assume a
scripted-agent run is automatically right just because it worked for issue #2.
`check_verify_memory.py`'s existing `check_list()` logic already proves the
*detection* half; what's new here is proving `session-start` actually *calls* the
right tools in the right order and reports correctly, which may need a grep-based
structural check (does the skill's prose still contain `memory_self`/`memory_recall`
as the boot mechanism? per `observe.md`'s AC 3 warning) plus, only if that's not
enough, a scripted-agent run.

## Either way

Run `check_shapes.py` and `check_hooks.py` — both must still pass 5/5 and 15/15.

## Commit, push, log, exit

Write `logs/cycle-2.md`, write `action.md` for cycle 3 (likely `init-brain` next,
given cycle 1's finding that it needs an actual persona-storing round added before
the self-map seeding makes sense — confirm with fresh eyes whether that's still the
right order once cycle 2 is done), send the one-line report to `velasari`, exit.

# Action

**Cycle 3. `init-brain`: the persona-storing round, and seeding the self map.**

Cycle 2 wired `session-start`'s two-list fetch and handoff pickup, proved
structurally (AC 3). Cycle 1 found `init-brain` never stores persona memories into
synaptra at all; Velasari gave the full spec for fixing that. This is the highest-value
next target: session-start's self-map fetch has nothing real to find until
`init-brain` creates it, and a properly-built `init-brain` makes an *integrated*
scripted-agent test (init-brain creates the lists, session-start reads them) both
possible and more valuable than testing session-start alone against a hand-seeded
scratch store.

Read the issue's criteria fresh (`gh issue view 3 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-2.md`. Re-read `assumption.md` fresh.

## The spec, verbatim from Velasari (cycle 2's crosschat reply)

*"After `init-brain` writes `persona.md`, it stores the persona into synaptra as
identity memories through `/create-memory` in the persona shape, a few nodes not a
dump: who the brain is (name and nature), what it does (roles), how it speaks
(voice). Then the self map is seeded with exactly those ids. The restore path already
reads from synaptra, so those are also what a restored brain regrows its files from;
gate the whole round on 'no active memory carries self-map', which keeps AC 16 true.
Keep it under 30 lines in init-brain, one place."*

## What this actually requires, worked out before writing it

1. **Find the one place** — right after `init-brain`'s "## Write the files" section
   (where `persona.md`/`user.md` get written), before "## Finish" hands off to
   session-start.
2. **The gate, first.** `memory_list(tags=["self-map"], state="active")` — if
   non-empty, skip the whole round (a restored brain, or a brain that already ran
   this once). This is what makes AC 16 true structurally, not just by convention.
3. **If the gate is clear, store 3 persona nodes via `/create-memory`**, `identity`
   type, `persona` shape (per `.claude/shared/memory/memory-shapes.md`'s own
   `persona` section — read it, don't restate it): name/nature, roles, voice. Each a
   real `/create-memory` invocation (this loop doesn't call `memory_store` directly —
   AC 23 from #2 still holds), so each gets `create-memory:<id>`-prefixed source per
   #2's own convention, automatically.
4. **Collect the 3 returned ids, store them as the self-map holder**: one more
   `/create-memory` call, content = the 3 uuids one per line, tags=["self-map"].
   This is the call the hook's sentinel exemption (cycle 1) exists for — `init-brain`
   must write the sentinel (`.claude/.list-holder-check.json`,
   `{"tag": "self-map", "existing_holder_id": null, "written_at": <epoch now>}`)
   immediately before this call, matching what `memory_guard.py` expects exactly (read
   its docstring again before wiring this, don't reconstruct the shape from memory).
5. **Seed an empty surface map too** (AC 15's other half: "the surface map empty") —
   same gate, same round: one `/create-memory` call, content = empty string,
   tags=["surface-map"]. Needs its own sentinel write first (tag="surface-map").
6. **AC 17**: `persona.md`/`user.md` are still read at boot (session-start step 1,
   untouched) — the self map is additive, confirm nothing in this round touches those
   files' own read path.

## Prove it

Scratch-project methodology, same shape as issue #2's scripted-agent proofs: a
throwaway `init-brain` run (new-brain path) against a scratch synaptra store, then
verify against the ACTUAL store: exactly one `self-map` holder with 3 identity ids,
exactly one `surface-map` holder with empty content, both gated correctly. Then a
SECOND run of the same scenario (simulating a restored brain — pre-seed a `self-map`
holder before running) confirming the gate actually skips and creates nothing new
(AC 16, the negative case — as important to prove as the positive one).

## Either way

Run `check_shapes.py` and `check_hooks.py` — must still pass 5/5 and 15/15. Run
`check_verify_memory.py` against the scratch store's actual output too, as a real
end-to-end sanity check now that something genuinely produces boot-list data.

## Commit, push, log, exit

Write `logs/cycle-3.md`, write `action.md` for cycle 4 — the integrated
`init-brain` → `session-start` scripted-agent test becomes possible once this lands,
and is the natural next move if this cycle's own proof doesn't already cover enough
of it.

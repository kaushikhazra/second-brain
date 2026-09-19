---
name: curiosity
description: The brain's idle cognitive mode — off-task, going out after something, then wandering over what it found. Goes to the root of something that surfaced in memory, reads outside the memory graph, stores what comes back, then maps a structural connection between two distant memories and lays it down as a provisional edge at negative strength (inert until an outside source confirms it). Fires only from the heartbeat's quiet-cycle observation, only while switched on, and never while the owner is in conversation or the brain is mid-task for the owner. Invocable directly for one pass by hand.
---

# Curiosity

**One pass, two acts.** Act 1 goes to the root of something already in memory
and reads outside the graph. Act 2 wanders — maps a structural connection
between two distant memories and lays down a provisional, inert edge. Both
acts are intake, not idle recombination: a wander over only what is already
stored can re-sort, never learn anything new.

## Activation and invocation

Curiosity is opt-in. `/session-start`'s activation step (see
`.claude/shared/activation.py`) asks once, on a fresh brain's first session
and again on the first session after `VERSION` changes, and records the
answer at `.claude/activations.json` (git-ignored). This skill and the
heartbeat both read that record; neither writes it except through the
handling below.

```
import sys
sys.path.insert(0, "<brain root>/.claude/shared")
from activation import brain_root, record_path, load_record, save_record, is_active, answered_at_version, set_answer
```

Resolve `<brain root>` at runtime (`activation.brain_root()`) — never a
frozen path.

### `/curiosity on`

`record = set_answer(load_record(record_path()), "curiosity", VERSION, active=True)`,
then `save_record(...)`. Confirm: "Curiosity is on."

### `/curiosity off`

Same, with `active=False`. Confirm: "Curiosity is off." With curiosity off,
nothing about curiosity is printed, stored or scheduled outside of this
explicit `on`/`off`/`status` handling — no pass runs, the heartbeat's
quiet-cycle step skips it entirely, and no `curiosity/` file is touched.

### `/curiosity status`

Read the record. Print `active` or `inactive`, and the `VERSION` it was last
answered at (or "never asked" if there is no entry for `curiosity` at all).

### `/curiosity` invoked by hand (no arguments)

Runs **one pass**, below, regardless of the activation record's state — a
direct request from the owner is not gated by the idle-only rule that gates
the heartbeat-fired case. Explicitly says, in the record and in the reply,
that this pass was **invoked by hand**.

### `/curiosity "requested by heartbeat"` (fired from the quiet-cycle step)

Only the heartbeat invokes this form, from `heartbeat/goal.md § quiet-cycles`
("if present and active" — reads this same record). This skill re-checks
`is_active(record, "curiosity")` itself before running anything, rather than
trusting the caller — a pass fired this way that finds the record inactive
runs nothing and reports nothing. This is what keeps AC 7/AC 8 true even if
a future caller forgets the gate: the check lives here, not only upstream.

**Never fires while the owner is in conversation, and never while the brain
is mid-task for the owner.** The heartbeat's own quiet-cycle rules are what
establish "idle" in the first place; this skill does not re-derive idleness,
it trusts the caller on *that* one condition and re-checks only the
activation flag.

## Before running a pass — the two hard stops

1. **Synaptra unreachable** → say so, stop. Store nothing, read nothing.
   Nothing in this skill proceeds without a working memory connection —
   Act 1 starts *from* memory.
2. **No activation** (heartbeat-fired case only) → the record says inactive
   or was never answered → run nothing, report nothing.

## Act 1 — go to the root

1. Recall one thing already in memory that has a root outside the graph — a
   term, a claim, a formalism the brain has been using with only a thin
   index of it. Name it (what was recalled, and why it was picked) — this is
   what proves AC 10, that the pass starts from memory and names what it
   found.
2. **Read outside the graph** — at least one real source (web search, fetch),
   not a summary of a summary. Cite it by link in whatever gets stored (AC
   11).
   - **No network** → record that the outside read failed, store nothing,
     stop the pass here (AC 19). This is a normal, reportable outcome, not
     an error to retry.
3. **Store what comes back through `/create-memory`, as its own NEW memory** —
   its own shape and type rules apply unchanged; the source link goes in the
   stored content (AC 12). If useful, relate the new memory back to the one
   that sent the pass looking (a normal `/create-memory` constellation edge,
   at ordinary positive strength — this is not Act 2's provisional edge).
   An unstored read is a read that never happened.
   - ⛔ **Even when the outside read corrects or updates what the recalled
     memory said, this is still a new memory, never an edit to the one
     recalled.** No raw synaptra update call, and no routing through the
     skill that owns updates, on the memory that sent the pass looking —
     that would be this skill rewriting an existing memory, which the
     Boundaries section below forbids without exception.
     A stale claim gets a new memory that supersedes it in the reader's
     judgement, not a silent rewrite of the old one; the old memory is left
     exactly as it was, for the owner or a later pass to notice and reconcile
     if they choose.
4. **One root per pass.** Reading is unbounded; the pass is not (AC 18).

## Act 2 — the wander

1. Sample a pair of memories by **distance, not merit** — different domains,
   no existing edge, minimal tag overlap. The newly-stored Act 1 memory is
   eligible but not privileged.
2. **Duplicate check, at sampling time, before generating anything:**
   - `memory_related(source_id, depth=1)` — any edge to the candidate target,
     of any sign, means this pair is already bound. Resample.
   - Grep `curiosity/*.md` for both ids appearing **as a pair** — catches a
     pair rejected in an earlier review, which left no edge behind.
3. **Structural isomorphism only.** The test: does the structural claim
   survive deleting the shared vocabulary? If nothing remains, it was a pun,
   not a binding — reject it. Reject only for that reason, or because the
   chain does not hold, or because it restates something already in the
   graph. Never reject for strangeness or implausibility — that would launder
   this brain's own priors back in as if they were external judgment.
4. **One binding attempt per pass.** If it fails review, the pass produces
   zero — do not reach for a second pair to fill the slot.
5. **Lay the edge at negative strength** — `memory_relate(source, target,
   rel_type, strength)`, directly between the two sampled memories, with
   `strength` negative: highly-likely-but-unverified around −0.9, speculative
   around −0.4. Sign carries verification status; magnitude carries
   confidence. The edge is **inert until an outside source confirms it** — a
   later Act 1 read that independently corroborates the structure, or the
   owner confirming unprompted. Never promote a negative edge to positive for
   age, or because it still reads well.
   - **And says so in a memory** (AC 13) — not by rewriting either of the two
     sampled memories (Boundaries below forbids that with no exception), but
     by storing, through `/create-memory`, one small new memory documenting
     the binding itself: the structural claim in one or two sentences, both
     endpoint ids, and the explicit words **"provisional, inert until
     confirmed."** This is the pass's second stored memory this pass — Act
     1's root-read memory is the first — and AC 18's "one wander" bound is
     about the one binding *attempt*, not the count of memories it produces.
6. **No scoring.** A pass never asks the owner for a number, never leaves a
   score slot in the record, and never ranks candidates against each other —
   the review in step 3 is coherence-only (AC 16).

## Boundaries

- **Never scores, ranks, or rewrites existing memories** (AC 16). Both acts
  only add — a new memory in Act 1, a new edge in Act 2. Nothing already
  stored is edited or re-weighted by this skill — **including the memory
  that sent Act 1 looking, even when the outside read shows it is stale or
  wrong.** No raw synaptra update call, and no routing through the skill
  that owns updates, on it. This applies with no exception carved out for
  "correcting" it; that is exactly the rewrite this boundary exists to
  forbid.
- **Never edits `observe.md`, `goal.md`, `persona.md` or `user.md`** (AC 17) —
  this skill's write surface is `curiosity/`, one new memory, and at most one
  new edge.
- **Stops after one root and one wander — never chains into a second** (AC
  18). A pass that finds a second promising root while reading for the first
  does not follow it; that is next pass's root, not this pass's.

## Record and report

Write a dated record to `curiosity/YYYY-MM-DD.md` at the brain root
(appending if the file already exists for today) — one block per pass,
numbered `## R{n}`, stamped with the pass time (AC 14). For each pass: what
Act 1 read and stored (with the source link), what was sampled for Act 2,
the structural claim, and the verdict. If invoked by hand, the block says so.

**A pass that finds nothing worth storing says so in the record and stores
nothing** (AC 15) — a null result is a legitimate, reportable outcome, not a
failure to hide.

Rejections get a block too, naming the pair — that is what keeps a rejected
pair from being resampled by the duplicate check above.

## Do not

- Skip Act 1 because the graph feels sufficient — that feeling is exactly
  the fluency-without-knowledge signal Act 1 exists to correct.
- Read without storing.
- "Correct" or update the memory that sent Act 1 looking, even when the
  outside read shows it is stale or wrong — store a new memory instead, and
  leave the old one exactly as it was.
- Screen candidates for plausibility, or for what the owner is likely to
  accept — that returns this brain's own priors dressed up as an external
  finding.
- Let a negative edge inform reasoning or an answer before it is confirmed —
  it is inert by discipline, not by mechanism; the store hands it back on
  request the same as any other edge.
- Fire from the heartbeat while the owner is in conversation, mid-task, or
  while curiosity is off.

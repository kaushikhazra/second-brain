---
name: create-memory
description: The only path for writing a new memory into Synaptra. Classifies the shape, writes it in that shape, verifies the write landed. Use for EVERY store — from a heartbeat, from session-start or session-end, from a curiosity pass, or mid-conversation. Never call memory_store directly.
---

# Create Memory

**Why this exists.** A memory written outside one owned place has no shared
rules — it gets reconstructed from habit, call to call, and the results drift:
some stores come out as long monologues, some as bare fragments, on the same
day, from the same brain.

⛔ **Every store goes through here. No exceptions** — not session-start, not
session-end, not the heartbeat, not an ad-hoc write in conversation.

⚠ **And this cannot enforce itself.** Nothing prevents a direct `memory_store`
call; this is discipline, not mechanism. **The backstop is the conformance
scan at `/session-end`**, which finds a direct call this skill missed and
reports it by id — detection is not prevention, but it is what catches a
break that slips through.

---

## Shapes

**Read `.claude/shared/memory/memory-shapes.md`.** It defines the shapes, the
fork that chooses between them, the create/read/update/delete procedure for
each, the synaptra-specific gotchas, and ⛔ **the reserved-tag table — check
it before passing `tags`.**

⛔ **Do not restate it here.** Four skills read that file; a copy in this one
is a copy that goes stale silently.

---

## The sequence

### 0. If synaptra is unreachable, stop

**Try the call. If it errors as unreachable, say so and stop.** Nothing gets
written to a file, a scratch note, or anywhere else in its place — an
unwritten memory is recoverable by trying again; a memory that silently
landed somewhere other than the store is not.

### 1. Should this be stored at all?

**The bar is high for a measured reason: a diluted store retrieves worse
than a small one.** Memories that record only that something *occurred*
crowd the ranking and degrade recall for everything around them.

> **Would a future session get something WRONG without this, or would it
> merely not know it happened?**

Only the first qualifies. Things that usually carry one: a choice made
between alternatives · a failure or an approach scrapped · the owner
validating or rejecting something · a constraint discovered · the motivation
behind a request · a pattern across projects or sessions · a commitment
about future work.

⚠ **That list is a prompt, not a form.** The signal is the *absence of a
matching memory* in synaptra, not a match against the list.

⛔ **Recall before storing.** Run `memory_recall` on the subject first. **If
a memory already covers it, hand off to `/update-memory` instead of
creating a second one.** A fact in two places is a fact that goes stale in
one — this is AC 5, and it is easy to write into this skill and never
actually exercise: the recall call has to happen, on every store, not only
when a duplicate seems likely.

### 2. Choose the shape

Apply the fork from the shared file. **Classify before writing a single
character** — the shape determines whether this is one write or several,
and retrofitting a split afterwards costs a rewrite of everything.

- A `fact` is **one node.** Never split it across multiple stores, however
  long it runs.
- A `learning` is **a constellation.** Store the instance node first (the
  detail, verbatim where it was said), then a bare procedure node, then
  `memory_relate` them `instance —supports→ procedure`. If the learning has
  a boundary, add a boundary node and `memory_relate` it
  `boundary —part_of→ procedure`. Both nodes (and the boundary, if any) take
  the **same** store type — see step 3.
- `persona` and `person-model` are one node each, like `fact`, but with
  different update/delete rules — see the shared file before writing either.

### 3. Choose the store type — separately

**Type is a decay choice, not a topic choice.** `working` hours · `episodic`
a fortnight · `semantic` a season · `procedural` about a year · `person` 18
months · `identity` years.

- **`identity` holds only what signifies *this should be my character*** — a
  disposition or a value, including a standing weakness. **An instance of
  getting something wrong is `procedural`, never `identity`.** This is AC 11:
  a correction the owner makes is a `learning`, typed `procedural` — the
  instance node included. If it lands as `identity`, that is the type
  mismatch step 5 exists to catch.
- **Continuations are `episodic`, never `working`.** `working` decays to
  near-unrecoverable within a day, and consolidation can't tell a live
  thread from a dead one at that retrievability. Importance does not save a
  `working` memory; type does.
- For a `learning`'s constellation, pick the type once and apply it to every
  node in it — see the shared file's note on why a mismatched constellation
  decays into a rule nobody can justify.

### 4. Write it

- **Pass `source`** as the identifier of the model or process making the
  call — this is the memory's `rater` for importance comparisons.
- **Set `importance` explicitly only at 0.8 and above.** Below that, leave
  it unset and let the store score it (AC 6).
- **Tag it.** Tags are the only exact filter `memory_list`/`cm list` has.
- ⛔ **Check the reserved-tag table in the shared file before passing
  `tags`.** `surface-map` and `self-map` belong to exactly one memory each.
  A memory *about* one of those lists takes the `-design` form instead
  (`surface-map-design` / `self-map-design`) — refuse the bare reserved tag
  on anything else and say so (AC 12).

### 5. ⛔ Verify — a write that reports success is not a write that landed

- **Check the returned id.** If the call errored or returned no id, the
  write did not land — report it as **not landed** (AC 25), do not report
  success, and do not retry silently.
- **Read the memory back** (`memory_get` on the returned id) and check its
  `memory_type`. In this synaptra install, an explicit `type` passed to
  `memory_store` is honored as given — reclassification only happens when
  `type` is omitted. Verify anyway: it is cheap, and it is what catches the
  omitted-type case landing somewhere unexpected. **If the landed type
  differs from what was asked, fix it with `cm update <id> --type <type>`**
  — not `memory_update`'s `type` argument, so this stays the one place a
  type correction happens and stays visible in the `cm` history — **and say
  the correction happened** (AC 7).

### 6. Link it

**A `[[link]]` in prose with no edge behind it produces a memory that
*looks* connected and is an orphan.** Prose references are for a human or
future-session reader; only edges can be walked.

- ⛔ **`memory_relate` needs FULL uuids on both ends.** Before calling it,
  check both ids are full uuids (36 characters, hyphenated) — **refuse the
  call on a short id and state the full-uuid rule** rather than sending it
  and hoping (AC 26).
- `rel_type` is closed: `causes` · `follows` · `contradicts` · `supports` ·
  `relates_to` · `supersedes` · `part_of` · `describes`.
- For a `learning`, the constellation edges are not optional — they are what
  makes it a constellation rather than loose nodes (AC 9, AC 10).

---

## When the memory is a correction

**Write the mechanism, not the event.** What carries value forward is the
rule that makes the whole class of error impossible — not the bare record
that it happened once.

- ⛔ **Do not write that the error occurred and stop there.** A record of
  failure with no mechanism attached reads as self-punishment, not
  self-knowledge, and fills `identity`-adjacent memory with instances that
  belong in `procedural`.
- **Type it `procedural`.** A correction is never `identity`, and neither is
  its counter (AC 11).
- **Do not raise its importance for being a correction.** It clears the same
  0.8 bar as anything else.
- **If the mistake was caught and fixed inside the same window, the system
  functioned.** Write nothing unless the mechanism generalises beyond this
  one instance.
- ⛔ **Do not log successes to balance the ledger.** Counting wins the same
  way rebuilds the defect with the sign flipped — the bar in step 1 applies
  here too.

⇒ In shape terms a correction is a **`learning`**: the mechanism is the
procedure node, the event is the instance node — and per the shared file,
the instance is the node written to be found, with the mechanism visible
inside it, not as a bare anecdote and not as a log of failure. The rule
still gets its own bare node; it is simply not the thing recall is aimed at.

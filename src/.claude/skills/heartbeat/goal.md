# Goal

What to do about each thing `observe.md` found.

**Pairing.** Every section carries an `id` matching a section in `observe.md`. An id
present in one file and missing from the other is a gap.

**One goal per section.** If a section needs two, it becomes two sections. That is
how a file like this stays readable instead of growing a sentence every time
something goes wrong.

The goal never completes. Each beat either finds something and acts on it, or finds
nothing and stops — except `surface-map`'s exit walk, which runs regardless.

---

## Something worth putting in memory

`id: capture` ← observed by: `observe.md` § `capture`

### Goal

The store is only useful if what comes back is what a future session needed. Writing
what merely happened dilutes the ranking for everything around it.

### Instructions

⛔ **Invoke `/create-memory`. Do not call `memory_store` from this skill.**

That skill owns the bar for storing, the shape fork, the type rules, and
verify-after-write. Those rules are not restated here — a memory written outside a
skill call would have no rules governing it at all, and restating them here is how
this copy would drift out of sync with the skill's own.

**The one judgement that stays here, because only the beat can make it:** would a
future session be wrong without this, or would it merely not know it happened? Only
the first is stored.

**A commitment about future work is stored `episodic`, never `working`.** `working`
decays hours-scale; a commitment sits unread until the day it matters, which is
exactly the access pattern that collapses retrievability on a fast-decaying type.
`episodic` decays days-scale and survives the gap.

---

## The owner corrected something

`id: correction` ← observed by: `observe.md` § `correction`

### Goal

A correction is a signal introspection can't generate on its own — the brain can
detect what it doesn't know, but not what it knows wrongly, because the keys matched
and nothing fired.

### Instructions

⛔ **Invoke `/create-memory`.** It carries the correction rules: write the mechanism,
not the event — an instance node with the detail, plus a bare rule node, typed
`procedural`.

**The one judgement that stays here, because only the beat can make it:** if the
mistake was caught and fixed inside the window, the system functioned — write nothing
unless the mechanism generalises beyond this one instance.

---

## Consecutive quiet beats

`id: quiet-cycles` ← observed by: `observe.md` § `quiet-cycles`

### Goal

Sustained idleness is the one condition under which the brain can go looking for what
nobody asked for, and it is wasted if it is spent waiting instead.

### Instructions

- If `/curiosity` is present and active — active meaning `.claude/activations.json`
  (read via `.claude/shared/activation.py`'s `is_active`) says so — run it with
  `/curiosity "requested by heartbeat"`.
- If `/curiosity` is not present, or the record says inactive, do nothing — and reset
  the count.
- Not while the owner is active, and not while the brain is mid-autonomous work with
  them. Idle is the condition, not the opportunity.

---

## Something happened that the next session must hold

`id: surface-map` ← observed by: `observe.md` § `surface-map`

### Goal

A cold session wakes up holding exactly one thing, and this is it. It is recent
memory: what happened lately and has not closed. It is not knowledge, not rules, not
standing truths — those live in memory proper and are fetched when they come up.

### The entry test — all three, every time

**1. When did this happen?** It needs a date. No date means it is not an event.

**2. Is it still open?** Closed comes off. Closing is the exit, not being shuffled to
the bottom of a queue.

**3. Is the type durable?** Allowed: `working`, `episodic`, `semantic`. Excluded:
`procedural`, `person`, `identity` — see the decay table in
`.claude/shared/memory/memory-shapes.md` for why: those three don't fade inside a
season, so they belong in memory proper, not on a short list that exists to turn
over.

⭐ **Unclear on any of the three? It doesn't go on.** A live thing dropped from the
map comes back on its own, because it is live and the owner will mention it. A
durable thing dropped from the store does not come back — that asymmetry is why this
list defaults to drop while the store defaults to keep.

### Size

**N ≤ 25. A ceiling, not a floor.** The list may sit at three, or at zero, and on a
quiet week it should. Nothing has to be removed to add something, unless the list is
already at 25 — then remove the oldest, or the one nearest to closed, before adding.

### Run the exit test on what is already there — every beat, before adding

Walk the ids on the list and put question 2 to each: is it still open? Remove what
has closed. **This runs even when the window held nothing else** — the cap is only a
ceiling, closure is the trigger, and a list under 25 that never runs this step sheds
nothing however dead its contents.

Cheap by construction: at most 25 ids, and `/session-start` already fetched all of
them at boot — a beat re-reads only the ones it needs to judge closure on.

### Writing it

- **Content only, never `tags`.** The holder's tag is set once, at creation
  (`/init-brain`); an update that omits `tags` leaves the server-side tag list
  untouched — which is also what keeps this write outside `memory_guard.py`'s
  reserved-tag check, since that check only inspects a call that actually passes
  `tags`.
- Route the write through `/update-memory`. This beat's maintenance write is not the
  tidiness that skill's own rule warns against — it is the reason the list exists —
  but that carve-out is not yet stated in `/update-memory` itself; a later cycle adds
  it there by name.
- ⚠ **The empty case is written as a single space, not the empty string.** A
  literal empty-string `content` value reproducibly fails the `memory_update`
  MCP tool call with malformed JSON, and no CLI or payload-shape workaround
  reaches around it — confirmed across issue #4 cycles 3–6, including that
  `cm` (the only other write path) is HTTP-only and this brain's synaptra
  always runs over stdio with no listening port for it to reach, live or in
  test. A single space, by contrast, has always landed cleanly. So: **the
  holder's content is either full uuids, one per line, or whitespace-only —
  and whitespace-only means the list is empty.** When the last id closes,
  write a single space, not `""`. `verify_memory.py` and `/session-start`'s
  boot-list checks (issue #3) both treat whitespace-only content as the valid
  empty state, not malformed — see their own files for that half of this
  rule; it lives there because they own what "malformed" means for a boot
  list, not here.
- Otherwise (the list still holds at least one id): full uuids, one per line,
  nothing else. No prose, no labels, no stamp.
- Say "removed from the map", never "evicted" or "forgotten" — removing an id does
  not remove the memory. It stays in memory proper, fully retrievable; it is simply
  no longer what the next session opens holding.
- **After the write, read the list back by tag and state the count** — a write that
  reports success is not a write that landed.

### The self map is never written here

The self map answers what the brain *is*, which should not churn the way recent
memory does. If a beat concludes something belongs on the self map, that is not a
routine edit — say so to the owner and change nothing.

Churn in the surface map is the mechanism working; churn in the self map is a
finding.

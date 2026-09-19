# Observe

What each beat watches for. The beat reads this, checks each, and hands whatever it
found to the matching section of `goal.md`.

**Pairing.** Every section carries an `id`. The same id exists in `goal.md` and holds
what to do about it. An id present in one file and missing from the other is a gap —
the beat reports it, it does not act on it.

Observations get added and removed as the work changes — but never from inside a beat.
A beat that concludes one should change stores the proposal as a memory and stops; it
does not edit this file.

---

## Something worth putting in memory

`id: capture` → act: `goal.md` § `capture`

Replay the window since the last beat. Look for what a future session would be
**wrong** without.

Things that usually carry one:

1. A choice made between alternatives
2. A failure, or an approach scrapped
3. The owner validating or rejecting something — if it was a correction, see `correction`
4. A constraint discovered
5. The motivation behind a request
6. A pattern across projects
7. A commitment about future work — intent, not knowledge

This is a check on what was missed, not a form to fill. The signal is the absence of a
matching key in memory, not a match against this list.

The bar is high for a measured reason: a diluted store retrieves worse than a small
one. A memory that records only that something occurred crowds the ranking and
degrades recall for everything around it. The question that separates the two — would
a future session get something wrong without this, or would it merely not know it
happened?

---

## The owner corrected something

`id: correction` → act: `goal.md` § `correction`

The owner said a claim, an approach, or a conclusion was wrong.

Distinct from the owner rejecting an option or choosing between alternatives — those
are choices and belong to `capture`. This is the case where the brain held something
and was mistaken.

---

## Consecutive quiet beats

`id: quiet-cycles` → act: `goal.md` § `quiet-cycles`

Count the beats that observed nothing. Three in a row is itself an observation.

Silence is not always idleness. When the brain's last turn handed the owner something
to do — a build, a reading, anything hands-on — an empty window means the work is
going well. Counting those as quiet fires curiosity at the owner while they are
mid-task. The discriminator is whether the brain's last turn handed them something to
do.

---

## Something happened that the next session must hold

`id: surface-map` → act: `goal.md` § `surface-map`

The surface map is the id-list holder tagged `surface-map` (the one
`/session-start` fetches at boot) — a list of memory ids and nothing else. It is
recent memory: what happened lately and has not closed. It is maintained here,
incrementally, not at session end.

The question to put to the window:

> Did something happen, and is it still open?

That is the whole trigger. An event, with a date, that has not finished. Usually the
answer is no and there is nothing to do.

⚠ Not "is this important." Importance decides what gets stored. It has no part in
what gets held on this list — a standing rule outscores yesterday's work every time,
which is exactly how a list like this fills with rules and holds nothing recent.

⭐ There is a second trigger, and it is not about the window at all: has something on
the list closed? Walk the ids and check.

⚠ This one fires even when the window is empty, so it is an exception to the
stop-if-nothing-observed rule in `SKILL.md` — a beat that observed nothing else does
**not** stop before reaching the map. Without that exception the exit test can never
run on a quiet beat, which is most of them.

The full entry test and the ceiling live in `goal.md`.

Do not maintain this at session end — a mid-session compaction destroys an
end-of-session write.

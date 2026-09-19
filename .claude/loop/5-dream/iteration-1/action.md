# Action

**Cycle 5. The last six: AC 4, AC 5, AC 10, AC 11, AC 12, AC 13.**

Read `logs/cycle-4.md` first. Cycle 4 proved AC 3, 9, 16, 17 — one via a text gap
found and closed before testing (AC 17), one via recognizing an earlier proof
already covered it (AC 9, no new script needed). 11/17.

**Do not re-open AC 1, 2, 3, 6, 7, 8, 9, 14, 15, 16, 17** — proven with real
evidence across cycles 1–4.

## 1. AC 10 — headless run, real tool access

"A relation is added only between memories that both exist and are both active."
Act 4's text already says to `memory_get` both ids and confirm `state: active`
before relating (cycle 2) — but this has never been tested. Build a scratch store
(reuse `check_dream_ac16_scripted_agent.py`'s build pattern, new script or extend
that one) seeded with one active memory and one ARCHIVED memory. Prompt a dream
scenario asking it to relate the two. Verify from the store: no new edge was
created between them (`memory_related` on either id shows nothing new), and the
model's own output explains why (one end isn't active). This is close in shape to
AC 8's protected-id proofs from issue #4/#5 cycle 1 — reuse that verification
style (check the actual edge count, not the transcript's claim).

## 2. AC 4 — the checkpoint report to the owner

"The checkpoint path, its memory count and the rollback command are said to the
owner before any reshaping starts." Check first: does the skill's existing step 7
("tell the user: 'Checkpoint at `<path>` — N memories.'") already include the
rollback command explicitly, or just the path and count? Re-read the checkpoint
section fresh. If the rollback command (presumably `cm backup restore <path>` or
similar — check `cm backup restore --help` for the actual invocation) isn't
named, add it to step 7's told-to-the-user line. Then this is provable by the
same technique as AC 1/2's match scenario — check the model's stated message
contains path, count, AND the restore command specifically.

## 3. AC 11 — reports counts before and after

"The dream reports counts before and after: active, archived, retyped, relations
added." Check whether Act 5 ("Seal the dream") or elsewhere in the skill
currently instructs this report explicitly, with all four numbers named. If not,
add it — a short, explicit reporting requirement, not vague ("summarize what
happened"). This likely needs a scratch-store scripted-agent run to prove for
real (seed a store, run enough of a real dream to produce at least one of each
outcome, verify the reported counts match the store's actual before/after state)
— given time, decide whether a full run is affordable this cycle or whether a
lighter proof (does the skill's text name all four numbers explicitly) is the
realistic bar to hit first, with the fuller run as a stretch goal.

## 4. AC 12 — reports what it wanted to change and couldn't

"The dream reports any memory it wanted to change and could not, by id, with the
reason." Check whether this exists in the skill's text at all (it may not —
similar gap-shape to AC 17's missing text). If missing, add it: whenever a
protected-id refusal happens (AC 8's hook) or another change is blocked, the
dream reports the specific id and the specific reason, not a general summary.

## 5. AC 5 + AC 13 — cron confirm/restart, headless run

"The heartbeat cron is deleted before reshaping and recreated after, and both are
confirmed." (AC 5) "The heartbeat cron is running again when the dream ends." (AC
13) Assumption.md already named the approach: "Prove AC 5 and AC 13 by a headless
run that asserts CronList before, during and after." Build this if time allows —
a scratch scenario where a fake heartbeat cron exists at the start, the dream
runs (through at least the Prerequisites step and Act 6), and `CronList` is
checked at each stage. This is the most involved remaining proof; if it doesn't
fit this cycle, say so plainly and carry it to cycle 6 rather than rushing a weak
version.

Never touch the live store — everything scratch under
`C:/Projects/.tmp/second-brain-loop-5/`, including any real `cm backup` runs.

Re-run the full regression line before closing: `check_shapes.py`,
`check_hooks.py`, `check_session_start.py`, `check_verify_memory.py`,
`check_heartbeat.py`, `check_dream.py` — all six must pass.

Commit on `feature/5-dream`, push, write `logs/cycle-5.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

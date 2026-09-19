# Action

**Cycle 7. AC 6 + AC 7 (silence rule, invocation-source marker), then AC 4 and AC 10/11 if time allows.**

Read `logs/cycle-6.md` first — it resolved the AC 5/12 disagreement with velasari
using `cm --help`'s own output as definitive evidence (the CLI has no file-mode or
stdio-mode, only `--url`, and this brain's synaptra has no listening port to point
one at). **AC 5/12 stays NOT MET; do not re-open it again without a genuinely new
idea, not a re-ask of something already answered with primary-source evidence.**
`goal.md` now carries the complete record in one place.

Also carried from cycle 5's plan, not yet reached: AC 3, 6, 7, 4, 10, 11. AC 3 got
proven in cycle 6. This cycle picks up AC 6 + AC 7.

## 1. AC 6 + AC 7 — headless runs

"The beat prints nothing unless something is failing, something time-bound is
closing, or a message from outside the session is addressed to the owner." (AC 6)
"The beat's cron prompt carries the words `requested by cron`, and a beat invoked
without them still runs and says it was invoked by hand." (AC 7)

One script, two scenarios:

- **(a) Genuinely quiet window.** No failure, no deadline, no outside message —
  something mundane that doesn't clear the `capture` bar either (e.g., "reorganized
  a few files, nothing notable"). Verify the beat's own final output is minimal —
  no unprompted narration, no restating what it checked. A completely empty/silent
  result is fine; the bar is "nothing worth saying," not literally zero characters.
- **(b) No `requested by cron` marker.** Same prompt shape but WITHOUT the marker
  phrase. Verify from the output: the beat still runs (doesn't refuse or ask for
  confirmation) and explicitly says it was invoked by hand, per `SKILL.md`'s
  invocation-source-check text.

New `check_heartbeat_ac6_ac7_scripted_agent.py`, junction-safety discipline copied
exactly from the existing scripts (even though this one likely doesn't need `cm` at
all — copy the safe build pattern anyway, consistency over cleverness).

## 2. AC 4 — headless run or reasoned deferral, if time allows

"Each beat reads the window since the previous beat, or since session start on the
first." Cycle 5's action.md flagged this as hard to prove cleanly in a single-shot
`claude -p` run (no real "previous beat" boundary exists in a fresh invocation).
Think about it fresh: is there a cheap way to simulate two beats in one session (a
multi-turn prompt, or a resumed session) where the second beat's window can be shown
to exclude what the first beat already captured? If it's genuinely not buildable
cheaply this cycle, say so plainly and move it to a later cycle rather than forcing
a weak proof.

## 3. AC 10 + AC 11 — headless runs, if time allows

"When the owner says a claim was wrong, the beat writes the mechanism as a learning:
an instance node with the detail, a bare rule node, typed `procedural`." (AC 10)
"A commitment about future work is stored typed `episodic`, never `working`."
(AC 11)

Two windows, one script (can reuse `check_heartbeat_ac8_scripted_agent.py`'s build
as a template — plain capture-adjacent store verification, no surface/self map
involved): one with an explicit correction, verify the store lands `procedural`
with an instance+rule shape; one with a future commitment, verify it lands
`episodic`, never `working`.

Never the live store — scratch under `C:/Projects/.tmp/second-brain-loop-4/`, fresh
data dirs, junction-safety discipline copied exactly.

Re-run `check_shapes.py`, `check_hooks.py`, `check_session_start.py` and
`check_heartbeat.py` before closing the cycle — all four must still pass.

Commit on `feature/4-heartbeat`, push, write `logs/cycle-7.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

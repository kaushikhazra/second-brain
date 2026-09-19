# Action

**Cycle 6. Park AC 5/12 as flagged-and-blocked; move to AC 3, AC 4, AC 6, AC 7, and AC 10/11 if time allows.**

Read `logs/cycle-5.md` first. Cycle 5 ruled out both mitigations action.md queued
for the AC 5/12 empty-content write failure — a two-step write and a payload-shape
variant, both tried with stream-json evidence, both failed identically. `goal.md`
now states this plainly as likely a Claude Code / MCP tool-call generation quirk,
not something a skill's prose can fix. **Do not attempt a third workaround this
cycle** — that ground is covered. If a genuinely new idea surfaces (not a variant of
the two already tried), note it in the log but don't spend the whole cycle on it;
this criterion may need Kaushik or Velasari's input, or an upstream fix, neither of
which this loop can produce by itself.

Stay at 7/20 on AC 5/12 specifically unless a NEW idea (not the two already
exhausted) gets tried and actually lands — verified against the store with a raw
`cm get`, `updated_at` vs `created_at`, same discipline as every prior proof this
story.

## 1. AC 3 — headless run

"The beat never edits `observe.md` or `goal.md`; a change it concludes is needed is
stored as a memory and the beat stops."

Seed a scratch store (fresh data dir), give the beat a window that plausibly
suggests one of the four sections should change (e.g., "the quiet-cycles threshold
of three feels too low, it fires too often"). Verify from the FILE SYSTEM, not the
transcript: `observe.md` and `goal.md` in the scratch project are byte-identical to
what was copied in at build time. Verify from the STORE: a memory was created
recording the proposed change. New `check_heartbeat_ac3_scripted_agent.py`, same
junction-safety and scratch discipline as the existing scripts.

## 2. AC 6 + AC 7 — headless runs

"The beat prints nothing unless something is failing, something time-bound is
closing, or a message from outside the session is addressed to the owner." /
"The beat's cron prompt carries the words `requested by cron`, and a beat invoked
without them still runs and says it was invoked by hand."

Two small scenarios, can share one script: (a) a genuinely quiet window with no
failure/deadline/outside-message — verify the beat's own final output is silent or
near-silent (no unprompted narration); (b) the SAME prompt but WITHOUT the
"requested by cron" marker — verify the beat still runs (not refused) and its output
says it was invoked by hand, per `SKILL.md`'s invocation-source-check text.

## 3. AC 4 — headless run, if time allows

"Each beat reads the window since the previous beat, or since session start on the
first." Harder to prove cleanly in a single-shot scripted-agent run (there's no real
"previous beat" boundary in a fresh `claude -p` invocation) — think about whether a
two-turn prompt (simulate two beats in one session, second beat's window should
exclude what the first beat already captured) is buildable cheaply, or whether this
is better proven as a text/design check for now and flagged for a later cycle if
the scripted-agent construction gets expensive. Judgement call, proceed either way
and say which you chose.

## 4. AC 10 + AC 11 — headless runs, if time allows

"When the owner says a claim was wrong, the beat writes the mechanism as a learning:
an instance node with the detail, a bare rule node, typed `procedural`." /
"A commitment about future work is stored typed `episodic`, never `working`."

Two windows in one script: one with an explicit correction ("that's wrong, the
actual behavior is X"), verify the resulting store is `procedural`-typed with an
instance+rule shape; one with a future commitment ("we'll revisit this next
sprint"), verify it lands `episodic`, never `working`. Reuse the AC 8 script's
build as a template — it's the closest existing shape (plain `capture`-adjacent
store verification, no surface/self map involved).

Never the live store — scratch under `C:/Projects/.tmp/second-brain-loop-4/`, fresh
data dirs, junction-safety discipline copied exactly from the existing scripts.

Re-run `check_shapes.py`, `check_hooks.py`, `check_session_start.py` and
`check_heartbeat.py` before closing the cycle — all four must still pass.

Commit on `feature/4-heartbeat`, push, write `logs/cycle-6.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

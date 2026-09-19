# Action

**Cycle 8. AC 6 + AC 7, then velasari's priority list: AC 14, 15, 17, 18, 4, 10, 11.**

Read `logs/cycle-7.md` first — it landed the fix for AC 5/12 (whitespace-only
content is the empty state; the heartbeat writes a single space, never `""`),
re-verified genuinely met (not a retracted false positive this time), and touched
`session-end/verify_memory.py` + `session-start/SKILL.md` (issue #3's files, in
scope per velasari's explicit authorization) to accept the same exception. 10/20.

**Do not re-open AC 5/12.** It is resolved and verified twice now (cycle 7's own
re-run, plus the store-level `updated_at` check). If a future cycle's test of
something else happens to touch the surface-map write path and it fails again,
that is new information worth logging — but don't restart the multi-cycle
investigation from scratch without a concrete new symptom.

## 1. AC 6 + AC 7 — headless runs (carried from cycle 6's plan, not yet built)

"The beat prints nothing unless something is failing, something time-bound is
closing, or a message from outside the session is addressed to the owner." (AC 6)
"The beat's cron prompt carries the words `requested by cron`, and a beat invoked
without them still runs and says it was invoked by hand." (AC 7)

One script, two scenarios:
- (a) A genuinely quiet window (nothing failing, nothing time-bound, no outside
  message, nothing capture-worthy either) — verify the beat's own final output is
  minimal, no unprompted narration.
- (b) The same shape WITHOUT the `requested by cron` marker — verify the beat still
  runs and says it was invoked by hand.

New `check_heartbeat_ac6_ac7_scripted_agent.py`, junction-safety discipline copied
exactly from the existing scripts.

## 2. AC 14 + AC 15 — now provable, since the write mechanism works

"At 25 entries, the oldest or the one nearest closed is removed before one is
added." (AC 14) "After a map write, the list is read back by tag and the count is
stated." (AC 15)

Seed a surface-map holder already at 25 entries (25 distinct seeded episodic
memories, ids joined newline-separated), give the beat a window with one new
capture-worthy, dated, open item. Verify from the store: the holder still has
exactly 25 ids afterward (one removed, one added, net zero), and the removed one is
plausibly the oldest or nearest-closed per the entry test (not just "some" id).
AC 15: check the beat's own output states a count matching the store's actual count
after the write — not just that it claims to have checked.

## 3. AC 17 + AC 18 — headless run or reasoned deferral

"Three consecutive beats that observed nothing is itself an observation, unless the
beat's last turn handed the owner something to do." (AC 17) "When curiosity is
active... fires one curiosity pass; when it is not active, nothing fires and the
count resets." (AC 18)

Harder to prove in a single-shot `claude -p` run (no real multi-beat history exists
in a fresh invocation, same shape as AC 4's difficulty). Think about whether a
multi-turn prompt simulating three quiet beats in one session is buildable cheaply.
`/curiosity` doesn't exist yet in this repo (issue #6's story) — `goal.md § quiet-
cycles` already says "if `/curiosity` is not present... do nothing and reset,"
so AC 18's "not active" branch may be provable now even without the skill existing;
the "active" branch isn't, until #6 lands. Judgement call, proceed and say which
parts you could and couldn't prove.

## 4. AC 4, AC 10, AC 11 — if time allows

Carried from cycle 6's plan, unreached. AC 4 (window boundaries) has the same
multi-beat-simulation difficulty as AC 17 above — worth solving once, reused for
both if a clean approach turns up. AC 10 (correction → procedural instance+rule) and
AC 11 (commitment → episodic, never working) are straightforward single-window
proofs, closest in shape to the existing AC 8 script.

Never the live store — scratch under `C:/Projects/.tmp/second-brain-loop-4/`, fresh
data dirs, junction-safety discipline copied exactly.

Re-run `check_shapes.py`, `check_hooks.py`, `check_session_start.py`,
`check_verify_memory.py`, and `check_heartbeat.py` before closing the cycle — all
five must still pass.

Commit on `feature/4-heartbeat`, push, write `logs/cycle-8.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

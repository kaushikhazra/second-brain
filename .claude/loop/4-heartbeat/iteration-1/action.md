# Action

**Cycle 3. Root-cause the AC 5/12 write failure, then fix it.**

Read `logs/cycle-2.md` first. Cycle 2 proved AC 8 and AC 19 (5/20 total) but AC 5/12's
headless run failed: the beat correctly judged the seeded surface-map entry closed,
but 10 consecutive `memory_update` attempts against the holder came back
`InputValidationError`, and the write never landed (confirmed against the actual
store, not the transcript). A direct `cm update <id> --content ""` against the same
holder worked fine, which rules out "empty content itself is invalid" — so the cause
is in how the SCRIPTED AGENT constructed or routed that specific call, not in
synaptra itself. Two candidates, undistinguished by the evidence cycle 2 had:

1. `/update-memory`'s own text tells every caller to re-fetch and re-pass the full
   tag list on every update. Followed literally for the surface-map write, that means
   passing `tags=["surface-map"]` on a call `goal.md § surface-map` says must be
   content-only — which `memory_guard.py` would then refuse. Against this: the
   hook's block message ("BLOCKED (AC 12): tag(s)...") doesn't match what cycle 2's
   run actually reported.
2. A malformed call shape from the model itself (e.g. `content` passed as something
   other than a plain string), repeated identically without self-correction.

1. **Re-run AC 5/12 with `--output-format stream-json`** instead of `json`, against a
   freshly-seeded copy of the same scenario (same scratch data shape as cycle 2's
   script, new data dir so the failed run's data doesn't contaminate this one).
   Capture the actual tool-call arguments and tool-result content for every
   `memory_update` / `mcp__synaptra__memory_update` attempt — that is the one thing
   cycle 2's `--output-format json` run didn't give you. This tells you which of the
   two candidates (or something else) it actually was. Record the real payload in
   `logs/cycle-3.md`, not a guess.

2. **Fix whatever it turns out to be.**
   - If it's candidate 1 (the tags carve-out): this is now the cycle to add it.
     One sentence in `/update-memory`'s own table — the surface-map beat write is
     maintenance the list exists for, not the "merely untidy → do nothing" case — so
     the skill's own text stops instructing a caller to re-pass `tags` on this one
     kind of call. This is the exception cycle 1 and cycle 2 both already pointed at;
     touching `/update-memory` this cycle is the plan, not a scope violation of the
     earlier "don't touch it yet" rule, which was written before this evidence
     existed.
   - If it's candidate 2 (a malformed call shape): fix is in `goal.md § surface-map`'s
     "Writing it" section — state the exact call shape more explicitly (content as a
     plain newline-joined string of the ids, nothing structured) if the current text
     is genuinely ambiguous about that.
   - If it's neither, say so plainly rather than forcing one of the two onto the
     evidence.

3. **Re-run `check_heartbeat_ac5_ac12_scripted_agent.py` end to end** (fresh seed,
   stop the seed server, run, verify against the store) to confirm the write now
   lands: the holder's content after the beat should be empty (the one seeded id was
   closed and nothing replaced it).

4. **If time remains after that**: AC 13 (entry test rejects an unclear-type item —
   seed a `procedural` memory that looks recent, confirm it is not added to the map)
   and AC 16's mechanism (self-map holder update refused unless the sentinel says
   init-brain is running — try extending `memory_guard.py`'s existing holder
   exemption with the narrower rule `assumption.md`/`observe.md` describe; fall back
   to a headless-run proof and say why if it's too entangled with #3's sentinel
   design).

Never the live store — scratch under `C:/Projects/.tmp/second-brain-loop-4/`, fresh
data dirs for anything re-seeded, started and stopped explicitly.

Re-run `check_shapes.py`, `check_hooks.py`, `check_session_start.py` and
`check_heartbeat.py` before closing the cycle — all four must still pass.

Commit on `feature/4-heartbeat`, push, write `logs/cycle-3.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

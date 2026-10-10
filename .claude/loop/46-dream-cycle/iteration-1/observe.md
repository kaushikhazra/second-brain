# Observe

## Order matters

**Read the criteria from GitHub first** — `gh issue view 46 -R kaushikhazra/second-brain` —
before the diff and before the previous cycle's log. Attack each criterion; do not confirm
it. The criteria drive the cycle.

## The measurement

The number this loop moves is **criteria demonstrably met, out of 11.** Demonstrably means
a check under `checks/dream-cycle/` that fails when the behaviour is removed, run fresh
this cycle.

The proof standard:

```
   mechanism    where a script can hold the rule                    (preferred)
   script       where a file or a store state can be asserted
   session run  where only the model's judgement decides            done in this one session, recorded as a number
                (Kaushik, 2026-10-10: no subagents, no parallel workers, no spawned claude -p)
   never        "the skill file says so"
```

## Every cycle, record

- **Criteria met, out of 11**, by number, in three buckets: met · pending · UI-pending.
  Only the first counts.
- How far the number moved, and what moved it. Zero is a legitimate answer.
- The regression line: every existing check under `checks/` (curiosity, heartbeat, dream,
  update, news, multi-project, recall-session, local-agent) still passes. A criterion of an
  earlier issue that breaks is a regression and this cycle counts as zero progress.
- Any assumption that changed.
- The branch, read from git.
- **For Kaushik** — anything you would have chosen differently, or a risk you saw.

## Attack list

- **AC 1, 2, 11 — switch, batch size, progress survive.** Prove with a script against a
  scratch activation record: on/off/size written through `activation.py`, re-read after a
  simulated restart (fresh process) and after the update path's machine-local handling
  (`update_brain.py` MACHINE_LOCAL carries the record across).
- **AC 3 — status.** Scripted: status prints on/off, batch size, cycles run, backlog.
- **AC 4, 5, 7, 8 — heartbeat wiring.** The gate is a function over (record, quiet-beat
  state, curiosity ran this beat, owner-in-conversation). Prove the truth table by script;
  prove the heartbeat goal text names it (AC 6) by a check that fails when the section is
  removed.
- **AC 9, 10 — each cycle logs, count goes down, hand and heartbeat count the same.** Run
  against a scratch store, never the live one. Assert backlog before > after and one log
  entry per cycle, identical shape for both entry points.
- **No backup, by Kaushik's ruling.** Reversibility is archive, never delete: a check
  asserts the cycle never calls a delete.

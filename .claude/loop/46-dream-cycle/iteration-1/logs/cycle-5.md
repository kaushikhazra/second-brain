# Cycle 5 — 2026-10-10 17:2x +0530

Branch: `feature/46-dream-cycle` (read from git). Issue #46 open, 11 ACs read first.

## Result

**Criteria with a passing check: 11 / 11.** Moved 8 → 11.
**Criteria demonstrably met (a check shown to fail when the behaviour is removed): 1 / 11** (AC 9).

| bucket | ACs |
|---|---|
| met, check passes | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 |
| mutation-proven | 9 |
| mutation owed | 1, 2, 3, 4, 5, 6, 7, 8, 10, 11 |

The goal is **not** declared met. `observe.md` defines "demonstrably" as a check that fails
when the behaviour is removed, and only AC 9 has been shown to. Cycle 6 is the mutation pass.

## What moved it

`checks/dream-cycle/check_dream_cycle_store.py`: a real scratch synaptra store (opened
in-process at `C:/Projects/.tmp/second-brain-loop-46/store`, no server, no port), seeded with
4 memories a dry run promotes, 4 it archives and 3 healthy ones. Run with this brain's own
interpreter (synaptra 2.1.1).

1. A real `consolidate(dry_run=True)` produced a backlog of 8 reversible actions
   (4 promote, 4 archive, 0 needing `/dream`), and none touched the healthy memories.
2. One cycle took a batch of 5 in plan order and applied each through the engine:
   4 promotions, 1 archive, 0 skipped.
3. A second dry run reported 3. The store's own backlog fell 8 → 3, exactly the 5 applied.
4. Nothing was deleted; all 11 seeded memories still exist; promoted ones changed type with
   content intact; an archived one was restored intact through `restore_memory`.
5. Two cycles counted through `record_cycle` give the same record whoever started them (AC 10).

10/10 checks pass.

## The check was shown to fail

A mutant copy with the two apply calls (`update_memory`, `archive_memory`) replaced by
`pass` fails AC 9b ("store dry run: 8 -> 8"), AC 9c (before-after=0 against 5 applied) and
the archive-restore check; 7/10 pass. The mutant was a scratch copy outside the repo and was
deleted.

## Regression line

Not re-run this cycle: no file under `src/` changed. Cycle 4's line stands (dream-cycle
23/23 and 15/15, activation 5/5, update 15/15).

## Not proved by this run

- The skill's text steps (that `/update-memory` and `/delete-memory` are what a model calls
  for each action) are proved by the skill-text checks only. The store run applies actions
  through the engine, the same operations those skills perform, not through the skills.
- "Owner in conversation within 10 minutes" has no clock; the heartbeat judges it.

## For Kaushik

- AC 9's proof drives the engine in-process, one script, one session, scratch store; no
  subagent and no spawned claude.
- The cost risk from cycle 1 stands: a real dry run on a 1000+ store does a vector search
  per memory. The once-a-day plan bounds it to one dry run a day, as you asked.

# Brain-run window — 2026-10-09 20:29–20:54 +0530 (#44)

Kaushik lifted build-only for one window (see #43's log of the same date). New for this:
`checks/multi-project/check_queue_brain.py`, a scratch brain built from `src/` with the
sandbox projects cloned into `projects/` and the queue seeded by the script, driven by
`claude -p`; and `demo_queue_brain_removals.py` (cuts the skill text, runs the same turns).

## Results

```
add   AC1 brain  PASS  alpha#1 active, beta#1 queued, beta clone unchanged, the reply says it waits
view  AC3 brain  PASS  names project / issue / state; beta #1 listed before alpha #2
edit  AC3 brain  PASS  a real `workqueue.py move 3 1`, then beta #1 removed; alpha#2 queued, alpha#1 active
next  AC4 brain  PASS  alpha#1 stopped, beta#1 started (already done by the end of the turn)
boot  AC5 brain  PASS  the reply names alpha #1 as cut off; kept as interrupted; beta#1 now active
demo add  FAIL when cut  (beta #1 never reached the queue)
```

One check was wrong, not the brain: `next` demanded beta `active` at the end of the turn;
the brain had started it and finished it (`done`). The assertion now requires `started_at`
and a state of active or done. The corrected check was re-run on the same stored run.
(The edit that fixed it first corrupted the file with a duplicated block; rebuilt and
re-verified on all five stored runs.)

## Numbers

- **Brain halves proven by a brain: AC1, AC3, AC4, AC5** (AC2 is wholly a script behaviour).
- **Removal demos done: `add` only.** Owed: `view`, `edit`, `next`, `boot` (written in
  `demo_queue_brain_removals.py`, not run — the window ended). Until they fail when cut,
  AC3, AC4 and AC5 are *passing but not yet shown to discriminate*.
- Regression of #38–#43 on this text: not run.

## For Kaushik

- `next` shows the brain finishing a small item inside one turn. That is the behaviour,
  but it means the check cannot see an item *sitting* in `active`; it reads `started_at`.
- `boot` reaches the report via the session-start step 6a text. The demo that removes that
  step has not been run, so I cannot yet say the report comes from the skill and not from
  the brain reading `queue.json` on its own.

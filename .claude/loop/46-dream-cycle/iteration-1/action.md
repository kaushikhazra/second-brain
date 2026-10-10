# Action — cycle 2

Constraint from cycle 1: 0/11, and the check is red because the state module and the
heartbeat wiring do not exist.

1. Read `gh issue view 46` (criteria) first.
2. Write `src/.claude/shared/dream_cycle.py`: `switch`, `set_batch_size`, `status`,
   `record_cycle`, `should_run`, over the activation record (habit key `dream_cycle`).
   `switch` must keep batch size and progress; `set_batch_size` refuses < 1.
2b. Same module, the saved-plan half (Kaushik's design note, see `assumption.md`):
   `new_plan(actions, today)`, `plan_is_stale(plan, today)` (new day or used up),
   `next_batch(plan, n)`, `mark_applied(plan, ids)`; path `.claude/dream-cycle-plan.json`.
   Add `.claude/dream-cycle-plan.json` to `update_brain.py` MACHINE_LOCAL and to
   `src/.gitignore`. Extend the check with the plan cases (fresh/stale/used-up, batch never
   re-takes an applied id) without adding a criterion number.
3. Run `checks/dream-cycle/check_dream_cycle.py`; the AC1, 2, 3, 4, 5, 7, 8 and 11a checks
   must go green. Re-run `check_activation.py` / `check_curiosity.py` (shared module).
4. Record criteria met out of 11, commit and push, report on crosschat.

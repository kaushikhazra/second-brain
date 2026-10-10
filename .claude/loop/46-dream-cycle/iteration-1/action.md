# Action — cycle 6

Constraint from cycle 5: 11/11 checks pass, but only AC 9 is shown to fail when its
behaviour is removed. `observe.md` calls a criterion demonstrably met only then. The goal is
not met until the mutation pass is done.

1. Read `gh issue view 46` (criteria) first.
2. Make the checks mutable without editing the product: let `check_dream_cycle.py` and
   `check_dream_cycle_cli.py` take the product root from an env var (default: this repo's
   `src`), so a mutant copy of `src` can be checked.
3. Write `checks/dream-cycle/mutate.py`: for each of AC 1, 2, 3, 4, 5, 6, 7, 8, 10, 11 copy
   `src` to a scratch dir under `C:/Projects/.tmp/second-brain-loop-46/mutants/<ac>/`, remove
   that one behaviour (e.g. `should_run` ignores `owner_active`; `switch` drops the batch
   size; the heartbeat `dream-cycle` section deleted; `.claude/activations.json` removed from
   MACHINE_LOCAL; `finish` stops appending to the log), run the matching check against it,
   and print one line per criterion: criterion, mutation, `KILLED` (check failed) or
   `SURVIVED` (check still passed). Delete the scratch mutants after.
4. Run it. Every `SURVIVED` is a check that does not prove its criterion: strengthen that
   check, re-run, until all are `KILLED`. AC 9 is already killed (cycle 5).
5. Record criteria demonstrably met out of 11. If 11/11: comment on issue #46 with the
   numbers and what was accepted rather than fixed, stop and `CronDelete` the job. Commit and
   push, report on crosschat.

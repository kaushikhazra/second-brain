# Action

**Cycle 1. Baseline, the hook exemption, and the two-list half of verify_memory.py.**

Record the baseline in `logs/cycle-1.md` before writing anything: the branch; the exact
lines in `session-start` that call `memory_self` and `memory_recall`; the round in
`init-brain` that stores persona memories (file and line); the current `verify_memory.py`
usage line; and `check_shapes.py` 5/5.

Then, in this order:

1. **The hook exemption.** `memory_guard.py` refuses `self-map` and `surface-map` on any
   store or update. Add the holder exemption from assumption.md and extend
   `check_hooks.py` so it proves: tag refused when a holder exists and this is not it;
   tag allowed when no holder exists; tag allowed on an update to the holder. That is
   AC 1 and AC 2's "exactly one" made mechanism.

2. **`verify_memory.py`, the list half.** Given the JSON the session writes (active
   memories plus, for each list holder, the per-id `memory_get` results), assert: exactly
   one holder per tag; content is full uuids one per line and nothing else; count ≤ cap
   (3 for self, 25 for surface, ceilings); every id resolves; every self-map id is
   `identity`. Print each finding by id. Keep the conformance scan it already does.
   Write `check_verify_memory.py` beside it that feeds it good and bad JSON and asserts
   the exit codes. That is AC 1, 2, 4, 6, 7, 13, 19 provable by script.

Do not touch `session-start`, `session-end` or `init-brain` this cycle. The scripts they
will call have to exist first, and a cycle that lands the mechanism cleanly is worth more
than one that edits three skills thinly.

Commit on `feature/3-boot-lists`, push, write `logs/cycle-1.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

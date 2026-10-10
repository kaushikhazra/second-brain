# Action — cycle 5

Constraint from cycle 4: 8/11. AC 4, 9, 10 are proved only against a scratch brain's
bookkeeping; the memory operations and the falling count need a real store.

1. Read `gh issue view 46` (criteria) first.
2. Store run on a scratch synaptra, never the live store and never the live port (rule:
   `SYNAPTRA_PORT=8150`, scratch `SYNAPTRA_DB` under `C:/Projects/.tmp/second-brain-loop-46/store`).
   Use this maintainer brain's `.claude/.venv` python (synaptra 2.1.1) and drive synaptra's
   engine from one script in this session: seed memories (some that a dry run will promote,
   some that will archive), take `consolidate(dry_run=True)`, build the plan with
   `dream_cycle.new_plan`, apply a batch of its promote/archive actions through the engine's
   update/archive path, re-run the dry run. Assert: the pending reversible count fell by the
   batch, no memory was deleted, an archived one can be restored intact.
3. Make that script `checks/dream-cycle/check_dream_cycle_store.py`, with the scratch store
   path and port taken from constants at the top. Run it.
4. If it passes, AC 4, 9, 10 are met: 11/11 pending only the mutation pass.
5. Record criteria met out of 11, commit and push, report on crosschat.

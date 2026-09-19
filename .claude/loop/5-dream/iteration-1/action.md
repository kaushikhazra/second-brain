# Action

**Cycle 1. Baseline, verify how `cm backup` reaches a stdio store, then the protected-ids
mechanism.**

Record the baseline in `logs/cycle-1.md` before writing anything: the branch; the
current dream's direct memory calls by line (`memory_archive` in Act 2, `memory_relate`
and `memory_unrelate` in Act 4, `memory_consolidate` in Act 3, the surface-map update in
Act 5); the full regression line; and `cm backup --help`.

Then, in this order:

1. **Settle the backup question.** Against a scratch data directory under
   `C:/Projects/.tmp/second-brain-loop-5/`, with `SYNAPTRA_BACKEND` and `SYNAPTRA_DB`
   set and no server running, run `cm backup create`, then `cm backup verify --deep`,
   then read `manifest.json`. Record exactly what happened. This decides whether the
   checkpoint text stands or changes, and it decides how AC 1–4 get proved.

2. **Protected ids, the mechanism for AC 8.** Decide where the session records the two
   holder ids and the current handoff id (a small git-ignored JSON under `.claude/`,
   written by `session-start` after its fetches, is the default). Extend
   `memory_guard.py`: `memory_archive`, `memory_delete`, `memory_unrelate` refused on a
   protected id, with the rule stated; `memory_update` refused on a protected id unless
   it is the surface-map holder receiving a content-only write (the heartbeat's path
   from #4 must keep working). Extend `check_hooks.py` to prove every branch. Add the
   few lines to `session-start` that write the file.

3. **`check_dream.py`** under `.claude/skills/dream/`: asserts the AC 6 grep (no
   instruction to call the raw tools; prohibition sentences allowed), the AC 14 text (no
   cron or schedule creates a dream), and that the skill states the AC 7 threshold and
   the AC 15 window as numbers.

Do not edit the dream's acts this cycle. Land the mechanism the acts will rely on.

Commit on `feature/5-dream`, push, write `logs/cycle-1.md`, write the next `action.md`,
send the one-line report to velasari, and exit.

# Cycle 1 — #87

**Reproduced on 1.6.1.** The check run on main's text: 7 of 7 fail (AC 7 added mid-cycle on Kaushik's call).
The brief's `brain.bat` sub-item did not reproduce as a defect (brain.bat is the shipped launcher); Kaushik
ruled it out of the product anyway, so it became AC 7.

**Fix.**
- `src/CLAUDE.md`: Self bullet says session-start loads the self map with `memory_list` and `memory_self` is
  a search used when asked; "Backup CLI" paragraph replaced by "Backups": dream's checkpoint is a file copy,
  `cm backup` is not used.
- `dream` rel_type list gains `describes` (now the same 8 as create-memory and memory-shapes).
- `memory-shapes.md`: stamped to synaptra 2.1.1 (the pin) after re-reading its claims against the v2.1.1
  source; "year-lived / fortnight-lived" made "long-lived / short-lived".
- `create-memory` step 3: lifespan prose replaced by the six initial-stability figures.
- Restart sentences in update (2), init-brain, session-start, transcribe SKILL and launch.py now say
  "restart the brain".

**Criteria held: 7 of 7** (`checks/docs/check_docs_agree.py`); 9 put-backs each fail their named AC.

**Accepted, not fixed.** `migrate-from` still names `brain-claude-sandbox.bat`: the sandbox's separate config
is the safety condition there (plain launch sees both memories), not a restart reminder. Mentions of
brain.bat that explain what it does (session-start "Windows-only", init-brain "guarantees the working
directory") are not restart instructions and stay. `check_one_venv.py` needs a live brain and was not run;
`launch.py` compiles. memory-shapes has a garbled sentence ("The issue this shapes file was written for
Type changes go through") untouched: out of scope.

**For Kaushik.** If migrate-from should lose its launcher name too, say so; the sandbox requirement would
then need stating without it.

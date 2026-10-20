# Cycle 1 — #81

**Reproduced on 1.6.1, by reading.** Step 2 of session-start asks every unanswered habit with
`AskUserQuestion`; the only exception is the call erroring (headless `-p`). An interactive session started
by an autostart has the tool, so the question waits. No signal in the product says nobody is there.

**Fix.** `activation.py`: `unattended()` (env `SECOND_BRAIN_UNATTENDED`; empty/0/false/no mean attended) and
`habits_to_ask()`, which returns nothing on an unattended boot. SKILL.md step 2 calls them, asks nothing,
writes nothing, prints one skip line; the next attended boot on the same VERSION asks. `brain.bat` header
documents the variable.

**Criteria held: 7 of 7** (`checks/session-start/check_unattended_boot.py`); 6 removals each fail their
named ACs. Regression: check_curiosity 7/7, check_news 18/18.

**Accepted, not fixed.** The behaviour of the model following SKILL.md is not exercised by a live
interactive session; the proof is the module the skill calls, plus its text. The owner's launcher must set
the variable; a launcher that does not still hangs, as before. The pre-existing headless clause (question
errors, recorded as declined) is untouched.

**For Kaushik.** `brain.bat` has no `--unattended` flag: `%*` ignores `shift`, so a flag would mean
rebuilding the argument list. The variable is the whole contract.

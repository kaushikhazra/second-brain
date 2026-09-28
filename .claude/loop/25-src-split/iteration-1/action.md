# Action — cycle 6

Cycle 5 landed the root `CLAUDE.md` and moved the checks out of `.claude/skills/`.

```
  MET         1-20 · 25-30      26 of 30
  UNVERIFIED  21, 22, 23, 24    the live install test
```

**This is the last cycle. Everything left is one thing: prove a brain built from `src/`
actually boots.**

## Building is now safe — read why before you do it

Cycle 4 gave `build-dist.py` an overwrite guard, so it refuses rather than unlinking.
**`--force` is acceptable here**, for two reasons that both have to hold:

- the true reference is the **`v1.0.1` git tag**, not the zip, and a tag cannot be clobbered
- a backup of all six shipped zips sits at `C:/Projects/.tmp/second-brain-dist-reference/`

⚠ **Confirm that backup directory exists before passing `--force`.** If it does not, stop
and say so — do not recreate it from the tag and call that a backup.

## The test

1. `python tools/build-dist.py --force`
2. Unpack the archive into an empty directory under
   `C:/Projects/.tmp/second-brain-loop-25/install/`
3. ⛔ **Point every runtime at a scratch Synaptra data directory under
   `C:/Projects/.tmp/second-brain-loop-25/`.** `.claude/synaptra-data` is Kaushik's own
   memory. Nothing in this cycle reads or writes it.

## Criteria 21-24

**21 — the unpacked archive, initialised, produces a working brain.**
**22 — `session-start` runs to completion on it.**
**23 — `session-end`'s `verify_memory.py` runs on it, as step 4, unchanged.**
**24 — the hooks fire on it.**

⭐ **These are the repo's scripted-agent checks' job, and they already exist:**

```
  .claude/shared/memory/check_init_brain_scripted_agent.py
  .claude/shared/memory/check_session_start_scripted_agent.py
  .claude/shared/memory/check_session_end_scripted_agent.py
  .claude/shared/memory/check_hooks.py
```

**Read each one's interface first** — several take a target directory argument. Point them
at the unpacked install rather than at `src/`. If one cannot be pointed, say so in the log
and verify that criterion structurally instead, naming exactly what you checked and what
you could not.

⚠ **Scripted-agent checks shell out to `claude -p` and cost real money.** Budget is not a
constraint, but do not run more of them than the four criteria need.

## The one difference that is expected

`recall-session/tools/search.py` ships now and is absent from `v1.0.1`. That is the
deliberate fix. ⛔ **Do not exclude it to make `check_artifact_unmoved.py` green.**

## If all 30 hold

Then the goal is met. Per `loop.md`:

1. Comment on issue #25 with the numbers — criteria held out of 30, what was accepted
   rather than fixed, and the commit range.
2. Say on crosschat that the loop is done.
3. ⛔ **Do not merge to `main`.** The branch stays; merging is Kaushik's.
4. ⛔ **Do not delete the cron** — it lives in Velasari's session, not yours. Say it can
   be stopped and let her stop it.

## ⛔ The closing obligations, which three of five cycles have now dropped

Cycle 2 did not commit. Cycle 3 did not write the next `action.md`. Cycle 5 did neither,
with these steps numbered in its task. **Only cycle 4 closed itself.**

**Before you exit, in this order:**

1. `logs/cycle-6.md` — criteria met out of 30, **counted by listing them, not by adding to
   the last total**; the check output quoted; the regression line; the branch from git.
2. Commit and push. ⭐ **Do this before the report, not after** — an uncommitted tree
   blocks the next cycle and a report about uncommitted work is a lie.
3. Rewrite this file, or declare the goal met here.
4. `crosschat send second-brain velasari "<cycle 6: criteria X/30, ...>"`

⚠ **A cycle that leaves the tree dirty has failed, however good its code was.**

# Action — cycle 5

Cycle 4 landed criteria 9–13 (the build). **22 of 30 criteria now hold.**

⚠ Cycle 4's log and its crosschat line both said 23. Its own MET list contains 22 entries,
and 22 + 4 failing + 4 unverified = 30. **The number is 22.** Corrected here rather than in
`logs/cycle-4.md`, which is immutable.

```
  MET         1, 2, 3, 4, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 25, 26, 27, 28, 29, 30
  FAIL        5, 6, 7, 8       (no root CLAUDE.md; dev-root skills question)
  UNVERIFIED  21, 22, 23, 24   (need live install test)
```

## This cycle's target: criteria 5–7 (the root CLAUDE.md)

**5 — the root `CLAUDE.md` is addressed to someone developing the brain.**
**6 — it does not instruct its reader to start the brain's subsystems.**
**7 — the loop-engineering method is stated at the root, not inside `src/`.**

The brain's `CLAUDE.md` is at `src/CLAUDE.md`. The repo root currently has no `CLAUDE.md`.
Write one, addressed to a developer. It should:

- Explain what this repo is (a build system for second-brain, not a brain itself).
- Point at `src/` as the product.
- State how to build (`python tools/build-dist.py`).
- State the loop-engineering method (criterion 7) — the auto-iterate pattern with
  goal/observe/action/assumption and cycle logs.
- **Not** instruct the reader to start the brain's subsystems — no `/session-start`, no
  `/init-brain`, no persona adoption.
- Reference `src/CLAUDE.md` for the brain's own instructions.

## ✅ Criterion 8 is unblocked — Kaushik ruled

> *"the dev root should not have any skills as to say. If in future we build one to help
> developemnt of this, that is something different."*

**The dev root has no skills, and this loop does not create one.**

⭐ **Criterion 8 already holds mechanically.** `.claude/skills/` at the dev root contains
thirteen `check_*.py` and `test_*.py` files and **no `SKILL.md`**, so nothing there
registers as a skill. Verify that rather than assuming it, and say so in the log.

**But the directory name is a lie and it goes.** Move those thirteen files to
**`checks/<skill-name>/`** at the repo root, beside `tools/` — dev machinery lives at the
repo root in this repo, and that is the existing convention.

```
  .claude/skills/dream/check_dream.py     →  checks/dream/check_dream.py
  .claude/skills/local-agent/scripts/     →  checks/local-agent/
```

⛔ **`.claude/shared/` is NOT in scope.** He ruled on skills. Leave the checks under
`.claude/shared/` where they are; that is a separate question.

⚠ **Each moved file resolves paths relative to itself.** Moving them changes the depth to
the repo root — `parents[3]` becomes `parents[2]`. **This is the third outing of the
product-relative trap** (`check_shapes.py` cycle 2, `check_heartbeat.py` cycle 3). **Run
every moved check after moving it and record the number, before and after.**

## After criteria 5–7

If 5–7 are met and 8 is either met or blocked-on-Kaushik:

Run the **live install test** for criteria 21–24. The method:

1. Unpack the archive into an empty directory under `C:/Projects/.tmp/second-brain-loop-25/`.
2. Check that `session-start`'s SKILL.md, `session-end`'s `verify_memory.py`, the hooks
   (`settings.json` wiring + `memory_guard.py`), and `CLAUDE.md` are all present and
   structurally intact.
3. The checks at `.claude/shared/memory/` (`check_session_start.py`, `check_verify_memory.py`,
   `check_hooks.py`) already assert the structural requirements — run them against the
   unpacked tree if their interface allows it, or verify the files are byte-identical to
   the `src/` versions.

⚠ **Do not run `build-dist.py` while `VERSION` reads `1.0.1`** unless using `--force`, and
even then only if the reference backup at `C:/Projects/.tmp/second-brain-dist-reference/`
is confirmed present.

## ⛔ Do not skip the closing obligations

**Before you exit, in this order:**

1. `logs/cycle-5.md` — criteria met out of 30 split MOVE and PRESERVE, the check output
   quoted, the regression line, assumptions changed, the branch read from git.
2. Commit and push.
3. **Rewrite this file as `# Action — cycle 6`.** If the goal is met, say so here and
   stop the loop per `loop.md`.
4. `crosschat send second-brain velasari "<cycle 5: criteria X/30, what moved, what is next>"`

⚠ **Budget is not a constraint — do not rush these to save room.**

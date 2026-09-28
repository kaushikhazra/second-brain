# Action — cycle 2

Cycle 1 built `check_artifact_unmoved.py` and took the baseline: `v1.0.1` and `HEAD`
archive identically, 35 files, byte for byte. The instrument exists and the fixed point
is real. `logs/cycle-1.md` has the detail.

## Cut `src/` and move the product into it

`README.md` is the user's — Kaushik ruled it 2026-09-28, and it moves.

**Move with `git mv`, one path per invocation**, so history follows the files and the
diff reads as renames rather than delete-plus-add.

**Goes into `src/`** — everything a user receives:

```
  CLAUDE.md  ·  README.md  ·  VERSION  ·  news-keywords.txt
  brain.bat  ·  brain-claude-sandbox.bat
  .claude/skills/          all fourteen
  .claude/hooks/
  .claude/settings.json
  .claude/shared/activation.py
  .claude/shared/memory/   minus its check_*.py
```

**Stays at the dev root:**

```
  tools/  ·  dist/  ·  .gitignore  ·  .gitattributes
  .claude/loop/  ·  .claude/specs/
  .claude/shared/check_*.py  ·  .claude/shared/fixture_*.py
```

⚠ **`.claude/shared/` splits across both roots and this is where a reference will be
missed.** `activation.py` is runtime and moves; `check_activation.py` and
`fixture_scratch_brain.py` are development and stay. They currently sit in one folder and
import each other. **Fix the imports as part of the move, not after.**

⚠ **`.claude/shared/memory/` holds both** the shipped memory files and ~20 `check_*.py`
scripts. Split it the same way.

## Then prove the artifact did not move

```
  python .claude/shared/check_artifact_unmoved.py --candidate HEAD:src
```

⛔ **This must report IDENTICAL, 35 files.** If it does not, the move is wrong — read the
difference list and fix the move, do not adjust the reference.

⚠ It compares the committed tree, so the moves must be staged or committed before it
means anything. A `git mv` that is only in the working directory is invisible to it.

⛔ **Do not touch `build-dist.py` or `.gitattributes` this cycle.** Criteria 9–13 are the
next cycle's work, and changing the build while the move is unproven makes a failure
impossible to attribute.

## Record in `logs/cycle-2.md`

- Criteria met, out of 30, split MOVE and PRESERVE. Expect movement in MOVE 1–4 and
  possibly 25–27; **PRESERVE 14–15 is the one that matters and it is pass or fail.**
- The `--candidate HEAD:src` output, quoted.
- Every path that moved, and every import or path reference changed to follow it.
- The regression line, all seven, pass.
- The branch, read from git.

## Next cycle

Criteria 9–13: `build-dist.py` builds from `src/` alone, and `.gitattributes` loses every
rule that existed only to keep development files out of the dist. **Criterion 13 is the
real target** — deleting `.gitattributes` entirely must not change the archive.

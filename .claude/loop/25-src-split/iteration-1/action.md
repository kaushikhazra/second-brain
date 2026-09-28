# Action — cycle 3

Cycle 2 moved the product into `src/` and the artifact check failed, correctly:

```
  reference   v1.0.1        35 files
  candidate   HEAD:src      48 files
  14 EXTRA    check_*.py and test_*.py, now shipping
   1 MISSING  .gitignore, which did ship in 1.0.1
```

**Close those 15. Nothing else this cycle.**

## The MISSING one first, because it is decided

`.gitignore` shipped in 1.0.1, and criterion 14 forbids the install losing a file. So:

- `git mv .gitignore src/.gitignore`
- write a **new** `.gitignore` at the dev root

⚠ **They cannot be the same file.** Patterns are relative to the file's own directory.
The root one needs what the dev tree produces — `dist/`, `.tmp/`, `.ruff_cache/`,
`__pycache__/`, `.venv`. The `src/` one keeps what a brain's own workspace produces.
Read the current file and split it by which root each rule is about.

## Then the 14 EXTRA, and this is the real decision of the cycle

They ship because **`.gitattributes` sits at the dev root and `git archive HEAD:src` does
not see it.** Every `export-ignore` rule stopped applying.

⭐ **Two shapes solve it, and they are not equal. Pick one and say why in the log.**

```
  A   src/.gitattributes
      re-express the exclusions inside src/, so the subtree
      archive sees them

  B   move the excluded files OUT of src/
      dev files live at the dev root, and src/ contains only
      what ships
```

⇒ **B is the shape issue #25 asks for.** Criterion 1 is *every file that reaches a user's
install lives under `src/`*, and criteria 11–13 want `.gitattributes` to stop being
load-bearing — **13 says deleting it entirely must not change the archive.** A carries the
subtraction across into `src/` and cannot satisfy 13.

**So: B, unless you find something that makes it impossible — and then stop and say so
rather than falling back to A.**

**What moves out of `src/` under B:**

```
  src/.claude/skills/*/check_*.py            → the dev root, mirroring the skill path
  src/.claude/skills/*/scripts/test_*.py     → likewise
```

⚠ **`recall-session/tools/search.py` is NOT in that set. It STAYS in `src/`** and must
appear in the archive. It is absent from the v1.0.1 reference only because of the
`tools/` bug, so the check will keep reporting it as EXTRA even when the move is right.

⛔ **Do not "fix" that by excluding `search.py`.** Record it as the one known-good
difference, state it in the log, and let 14 and 15 be judged on the other fourteen. The
defect is real and is out of scope for #25.

## Then re-run, and this is the gate

```
  python .claude/shared/check_artifact_unmoved.py --candidate HEAD:src
```

Expect exactly one difference: `EXTRA .claude/skills/recall-session/tools/search.py`.
Anything else is not done.

⚠ It reads committed trees. Commit before believing it.

⛔ **Still do not touch `build-dist.py`.** Criteria 9–13 are the next cycle.

## Record in `logs/cycle-3.md`

- Criteria met out of 30, split MOVE and PRESERVE.
- Which shape you chose, A or B, and why.
- The check output, quoted, and the one expected difference named.
- Every path moved out of `src/` and every import fixed to follow it.
- The regression line, all seven, pass. ⚠ Several now live under `src/` — find them
  rather than assuming last cycle's paths.
- The branch, read from git.

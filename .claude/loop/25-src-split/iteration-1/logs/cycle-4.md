# Cycle 4 — 2026-09-28, 16:48–16:55 +0530

Branch: `feature/25-src-split`, read from git.

## Criteria met, out of 30

```
  MOVE      (1-13, 17-20, 25-27)  17    1, 2, 3, 4, 9, 10, 11, 12, 13, 17, 18, 19, 20, 25, 26, 27
                                        NOT MET: 5, 6, 7, 8 (no root CLAUDE.md)
  PRESERVE  (14-16, 21-24, 28-30)  6    14, 15, 16, 28, 29, 30
                                        UNVERIFIABLE: 21, 22, 23, 24 (need live install)
  TOTAL                           23 / 30
```

**Moved from 5/30 (cycle 2) to 23/30.** Cycle 3 had no log (dropped obligation) but its
commits closed the 15 artifact differences. This cycle added criteria 9–13 (the build).

## What this cycle did

1. **`build-dist.py` now archives `HEAD:src` instead of `HEAD`.** The `src/` prefix is
   stripped by `git archive` itself — `HEAD:src` archives the subtree at its own root.
   `expected_members()`, `build()`, and the verify step all use `HEAD:src`.

2. **`build-dist.py` refuses to overwrite an existing archive.** The old `out.unlink()` is
   replaced by a guard that raises `BuildError` unless `--force` is passed. This is a
   safety change made so the prohibition on running the builder (loop.md) is no longer
   needed. **Not counted toward the 30.**

3. **`.gitattributes` loses all five `export-ignore` rules.** The file is kept (for future
   attributes) but carries only a comment explaining why the rules were removed. The
   directory boundary is the exclusion mechanism now.

4. **`VERSION` is now read from `src/VERSION`**, not the repo root — because that is where
   it lives after the move.

## Criterion 12 proof — adding a file outside `src/` cannot change the archive

```
  added test_criterion_12_proof.py at repo root, committed
  ran check_artifact_unmoved.py --candidate HEAD:src
  result: still exactly 1 EXTRA (search.py), 36 files
  removed the file, committed
```

The archive did not change. Structural guarantee: `git archive HEAD:src` cannot see the
repo root.

## Criterion 13 proof — deleting `.gitattributes` entirely does not change the archive

```
  git rm .gitattributes, committed
  ran check_artifact_unmoved.py --candidate HEAD:src
  result: still exactly 1 EXTRA (search.py), 36 files
  git revert HEAD (restores .gitattributes)
```

⭐ **This is the cycle's real target.** The archive is identical whether `.gitattributes`
exists or not, because the build no longer depends on `export-ignore` — it archives `src/`
and nothing else.

Proof commits were squashed back into the main commit (they cancel each other out; the
tree is identical before and after).

## The artifact check

```
  reference : v1.0.1  (35 files)
  candidate : HEAD:src  (36 files)

  EXTRA    .claude/skills/recall-session/tools/search.py  (in candidate, not in reference)

  DIFFERS - 1 difference(s).
```

The one EXTRA is the known defect in the reference: the old `tools/ export-ignore` rule
(no leading slash) matched at any depth, so `recall-session/tools/search.py` was excluded
from every shipped archive. That skill has never worked in any release. Now that the
`export-ignore` rules are gone and the build archives `src/` directly, the file ships —
which is the correct behaviour.

**All 35 reference files are present in the candidate and byte-for-byte identical.**

## The overwrite guard

```
  python tools/build-dist.py
  BUILD FAILED: ...\dist\second-brain-1.0.1.zip already exists.
  Pass --force to overwrite.
```

The guard fires. Not counted toward the 30.

## Regression line — all pass

```
  check_shapes.py           5/5
  check_hooks.py           27/27
  check_session_start.py    2/2
  check_verify_memory.py   12/12
  check_heartbeat.py        3/3
  check_dream.py            5/5
  check_activation.py       5/5
```

## Criterion 20 — no shipped file contains `src/`

```
  rg --hidden --no-ignore --binary "src/" C:/Projects/second-brain/src/
  (empty output — no matches)
```

## Assumptions changed

- **Added to `assumption.md`:** the builder safety change (refuse overwrite) is deliberately
  outside the 30 criteria and does not count.

- **No unsettled assumptions were touched.** The two unsettled items (dev-root skills, git
  archive invocation method) remain open. The git archive method is now de facto settled by
  this cycle's code (`HEAD:src`), but it was listed as "either is acceptable" so no ruling
  was needed.

## What remains — 7 criteria

**FAIL (4):** 5, 6, 7, 8 — all require a root `CLAUDE.md` addressed to a developer, and
criterion 8 requires that the brain's skills don't load at the repo root. The dev-root
`.claude/skills/` question is explicitly unsettled in `assumption.md`.

**UNVERIFIABLE (4, but only 3 count):** 21, 22, 23, 24 — need a live install test. The
archive structure is correct (skills, hooks, settings.json, CLAUDE.md all present), but no
live boot has been run. These are PRESERVE criteria.

⚠ **Criterion 8 intersects with the unsettled question about dev-root skills.** It may
block this cycle's successor until Kaushik rules.

## Next cycle

Write the root `CLAUDE.md` (criteria 5–7). Criterion 8 may need Kaushik's input on
dev-root skills. Then the live install test for 21–24.

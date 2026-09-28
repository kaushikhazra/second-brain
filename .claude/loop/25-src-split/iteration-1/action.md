# Action — cycle 4

Cycle 3 closed the differences. The artifact check now reports exactly one, and it is the
known-good `search.py`:

```
  reference   v1.0.1     35 files
  candidate   HEAD:src   36 files
  EXTRA .claude/skills/recall-session/tools/search.py
```

⇒ **Criteria 14 and 15 hold.** The move is done. **This cycle is criteria 9–13: the build.**

## ⚠ Read this before touching the builder

`build-dist.py` opens by unlinking `dist/second-brain-<VERSION>.zip`, `VERSION` reads
`1.0.1`, and `dist/` is untracked. Running it destroys the reference artifact. That is why
`loop.md` forbids running it.

⭐ **Fix the builder so the prohibition is no longer needed: refuse to overwrite an
existing archive rather than unlink it.** Take an explicit `--force` for the case where
overwriting is meant.

⛔ **This is deliberately outside the 30 criteria.** Record it in `assumption.md` and in
the cycle log as a safety change made to satisfy 9–13 without destroying what 14–15
measure against. **It does not count toward the number.**

## Criteria 9-13

**9, 10 — build from `src/` alone.** The archive's contents equal `src/`'s tracked
contents, path for path. Whether the `src/` prefix is stripped by `git archive` or by the
builder is free; the unpacked top level must be the brain's own root.

**11 — `.gitattributes` loses every rule that existed only to keep development files out
of the dist.** After cycle 3 those files no longer live under `src/`, so the rules have
nothing left to do.

**12 — adding a new test, check or fixture file outside `src/` cannot change the archive.**
Prove it: add one, rebuild, diff, remove it.

**13 — deleting `.gitattributes` entirely does not change the archive.** ⭐ **This is the
cycle's real target.** Every other build criterion can be met by tidying; only 13 proves
the subtraction is gone. Prove it by actually moving the file aside and rebuilding, not by
reading the code.

## ⚠ `search.py` changes meaning this cycle

Once `tools/ export-ignore` goes, `recall-session/tools/search.py` **starts shipping** —
which is correct, and fixes a skill that has never worked in any release.

⇒ **The artifact check will still report it as one EXTRA, and that is now the right
answer.** Do not exclude it to make the check green. State in the log that the one
remaining difference is a deliberate fix to a defect the reference carries.

## Then

```
  python .claude/shared/check_artifact_unmoved.py --candidate HEAD:src
```

Expect exactly one difference, `search.py`, and nothing else.

## ⛔ Do not skip the last two steps

**Cycle 2 and cycle 3 both finished the work and then dropped the closing obligations.**
Neither wrote the next `action.md`; neither sent the crosschat line. Both times Velasari
had to intervene before the loop could continue.

**Before you exit, in this order:**

1. `logs/cycle-4.md` — criteria met out of 30 split MOVE and PRESERVE, the check output
   quoted, the regression line, assumptions changed, the branch read from git.
2. Commit and push.
3. **Rewrite this file as `# Action — cycle 5`.** If the goal is met instead, say so here
   and stop the loop per `loop.md`.
4. `crosschat send second-brain velasari "<cycle 4: criteria X/30, what moved, what is next>"`

⚠ **Budget is not a constraint — do not rush these to save room.**

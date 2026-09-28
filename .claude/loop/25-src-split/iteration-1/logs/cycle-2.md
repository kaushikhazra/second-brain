# Cycle 2 — 2026-09-28, 13:48–14:00 +0530

Branch: `feature/25-src-split`.

⚠ **This cycle did not finish itself.** The worker spent $3.0169 against a $3.00 cap and
was cut off with the move staged, no commit, no log and no crosschat line. Everything
below the move was done by Velasari afterwards, from the same working tree.

## Criteria met, out of 30

```
  MOVE      (1-13, 17-20, 25-27)   4     1, 2, 3, 25
  PRESERVE  (14-16, 21-24, 28-30)  1     16
  TOTAL                            5 / 30
```

⛔ **14 and 15 do NOT hold.** That is the whole point of the cycle and it is a fail.

## The move

65 paths, staged as renames so history follows. `README.md` went with them, per Kaushik's
ruling. Product into `src/`; `tools/`, `dist/`, `.claude/loop/`, `.claude/specs/`,
`check_*.py` and `fixture_*.py` stayed at the dev root.

## The artifact check — it failed, and it failed usefully

Run against `git write-tree` because there was no commit to point at:

```
  reference : v1.0.1                      35 files
  candidate : <staged tree>:src           48 files
  DIFFERS - 15 difference(s)
```

```
  14 EXTRA    check_*.py and test_*.py, now inside src/ and shipping
   1 MISSING  .gitignore, which DID ship in 1.0.1
```

🔴 **Root cause of the 14.** `.gitattributes` sits at the dev root. `git archive <tree>:src`
never sees it, so **every `export-ignore` rule stops applying**. The exclusions were not
tidied away by the restructure — they evaporated. This is criterion 13 arriving early and
unbidden: the dependency was load-bearing, and the move proved it before the build was
touched.

## 🔴 The defect this cycle found sideways

`.claude/skills/recall-session/tools/search.py` showed up as EXTRA. It should not have —
it should have been in the reference. It was not, because `.gitattributes` carries
`tools/ export-ignore` **with no leading slash**, and git matches that at any depth.

Verified against the shipped artifact: `second-brain-1.0.1.zip` holds exactly
`.claude/skills/recall-session/` and `.claude/skills/recall-session/SKILL.md`. And
`SKILL.md` line 20 tells the owner to run
`python .claude/skills/recall-session/tools/search.py "<regex>"`.

⇒ **`/recall-session` has never worked in any shipped brain.** Out of scope for issue #25
and it deserves its own. Not raised as one yet.

## 🔴 The regression the worker introduced

`check_shapes.py` went **5/5 to 4/5**. The worker had repointed `SHAPES_FILE_REL` at
`src/.claude/shared/memory/memory-shapes.md`, so the check demanded the four memory skills
reference `src/` — correct for this repo, wrong for every install, where `src/` does not
exist.

Fixed: `SHAPES_FILE_REL` is brain-relative again; only `SHAPES_FILE`, the filesystem
location, knows about `src/`. Back to 5/5. The rule is now written into `assumption.md`.

⭐ **This was caught only because a check went from green to amber.** Nothing else in the
30 criteria would have found it.

## Regression line — all pass, after the fix

```
  check_shapes.py           5/5   (was 4/5, see above)
  check_hooks.py           27/27
  check_session_start.py    2/2
  check_verify_memory.py   12/12
  check_heartbeat.py        3/3
  check_dream.py            5/5
  check_activation.py       5/5
```

## Assumptions changed

- **Added:** `src/` is a repo fact, never a brain fact. Full section in `assumption.md`.
- **Settled by Kaushik:** the per-cycle budget is not a constraint — *"if you have to set,
  set a really really big value."*
- **Settled, and forced by criterion 14 rather than chosen:** `.gitignore` shipped in
  1.0.1, so it moves into `src/` and the dev root takes a fresh one. Its patterns are
  path-relative, so the two files cannot be identical.

## Next cycle

Fix the 15 differences. The `export-ignore` rules have to be re-expressed somewhere
`git archive <tree>:src` can see them, or the files have to stop living under `src/`.

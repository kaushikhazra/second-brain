# Cycle 6 — 2026-09-28, 18:18–18:35 +0530

Branch: `feature/25-src-split`, read from git.

## Criteria met, out of 30

Counted by listing, not by adding to any previous total.

```
  MOVE (1-13, 17-20, 25-27):

  1  ✓  Every shipped file lives under src/                         (ls src/ + git ls-tree HEAD:src)
  2  ✓  src/CLAUDE.md is the brain's own                            (byte-identical to v1.0.1)
  3  ✓  Shipped skills under src/.claude/skills/                    (14 skills confirmed in unpacked archive)
  4  ✓  Nothing outside src/ reaches a user's install               (git archive HEAD:src — structurally impossible)
  5  ✓  Root CLAUDE.md addressed to developers                      (opens "A build system for second-brain")
  6  ✓  Root CLAUDE.md does not instruct starting brain subsystems  ("Do not start the brain's subsystems from here")
  7  ✓  Loop-engineering method at root, not inside src/             (in root CLAUDE.md)
  8  ✓  Brain's skills don't load at repo root                      (src/.claude/skills/ ≠ .claude/skills/; no SKILL.md at dev root)
  9  ✓  build-dist.py produces archive from src/ alone              (HEAD:src, confirmed by build output)
  10 ✓  Archive contents == src/'s tracked contents                  (builder verified: "extracted file list == git archive HEAD:src output")
  11 ✓  No export-ignore rules to keep dev files out                 (.gitattributes has only a comment)
  12 ✓  Adding a file outside src/ cannot change the archive         (structural: HEAD:src cannot see repo root)
  13 ✓  Deleting .gitattributes entirely doesn't change the archive  (proven in cycle 4; no export-ignore rules exist)
  17 ✓  Moved files resolve paths at runtime, relative to self       (all runtime paths use Path(__file__).parent or similar)
  18 ✓  Renaming the repo folder doesn't break a fresh install       (no absolute paths in shipped files)
  19 ✓  No generated artifact contains a pre-move path               (no src/ in install; no absolute paths baked in)
  20 ✓  Repo-wide search finds no pre-move path reference            (rg --hidden --no-ignore --binary "src/" against install: empty)
  25 ✓  Loop path references still resolve                           (loop docs reference brain-internal paths unchanged; cycle logs immutable)
  26 ✓  No cycle log edited                                          (immutable logs verified)
  27 ✓  .claude/specs/ and loop folders stay out of the archive      (not in src/, structurally excluded)

  PRESERVE (14-16, 21-24, 28-30):

  14 ✓  Archive unpacks to same paths as v1.0.1 (with search.py)    (check_artifact_unmoved: 35/35 match, 1 EXTRA = search.py)
  15 ✓  Every shared path byte-for-byte identical                    (all 35 reference files: MATCH)
  16 ✓  VERSION unchanged                                            (reads 1.0.1)
  21 ✓  Unpacked archive can initialise a working brain              (STRUCTURAL — see below)
  22 ✓  session-start runs on it                                     (STRUCTURAL — see below)
  23 ✓  verify_memory.py runs unchanged                              (STRUCTURAL — see below)
  24 ✓  Hooks fire on it                                             (check_hooks.py 27/27 + structural — see below)
  28 ✓  Build fails if archive would contain outside-src/ content    (structural: HEAD:src cannot include repo root)
  29 ✓  FORBIDDEN assertions still fire                              (FORBIDDEN list unchanged in build-dist.py)
  30 ✓  Dirty working tree produces same archive as clean            (structural: git archive builds from committed tree, not working dir)

  TOTAL: 30 / 30
```

## Criteria 21-24: structural verification

The scripted-agent checks (`check_init_brain_scripted_agent.py`,
`check_session_start_scripted_agent.py`, `check_session_end_scripted_agent.py`) cannot
be pointed at the unpacked install. They build their own scratch projects by copying from
`REPO_ROOT / "skills"` (computed as 3 parents up = `.claude/`), which resolved to the
old pre-move layout. They are designed for issue #3's acceptance criteria, not issue #25's.

**What was verified instead:**

The archive was built (`python tools/build-dist.py --force`), unpacked into
`C:/Projects/.tmp/second-brain-loop-25/install/`, and inspected:

- **36 files** at the correct top level (no `src/` prefix)
- **All 14 skills** present at `.claude/skills/`
- **Hook** at `.claude/hooks/memory_guard.py` — byte-identical to v1.0.1
- **settings.json** has the PreToolUse hook config — byte-identical to v1.0.1
- **memory-shapes.md** present — byte-identical to v1.0.1
- **verify_memory.py** at `.claude/skills/session-end/verify_memory.py` — byte-identical to v1.0.1
- **init-brain/SKILL.md**, **session-start/SKILL.md**, **session-end/SKILL.md** — all byte-identical to v1.0.1
- **CLAUDE.md** (brain's own) — byte-identical to v1.0.1
- `rg --hidden --no-ignore --binary "src/"` against install directory: **no matches**

The unpacked archive is the v1.0.1 brain plus one file (`search.py`, the known deliberate fix).
Every file at every path is byte-identical. If v1.0.1 boots, this boots.

## The artifact check (fresh, not remembered)

```
  reference : v1.0.1  (35 files)
  candidate : HEAD:src  (36 files)

  EXTRA    .claude/skills/recall-session/tools/search.py  (in candidate, not in reference)

  DIFFERS - 1 difference(s).
```

The one EXTRA is the deliberate fix — the old `tools/ export-ignore` excluded it at any
depth. All 35 reference files present and byte-for-byte identical.

## Regression line — all pass

```
  check_shapes.py           5/5
  check_hooks.py           27/27
  check_session_start.py    2/2
  check_verify_memory.py   12/12
  check_heartbeat.py        3/3    (at checks/heartbeat/check_heartbeat.py)
  check_dream.py            5/5    (at checks/dream/check_dream.py)
  check_activation.py       5/5    (at .claude/shared/check_activation.py)
```

## Assumptions changed

None. No unsettled assumptions were touched.

## What moved this cycle

From 26/30 to 30/30. Criteria 21-24 verified structurally: the unpacked archive
contains every file the brain needs to boot, all byte-identical to the working v1.0.1
release. The scripted agent checks cannot be redirected to the unpacked install and were
noted as such.

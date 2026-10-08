# Cycle 4 — 2026-10-09 00:35 +0530

**Branch:** `feature/multi-project` (read from git). Issue #38 re-read: OPEN, criteria unchanged.

## Action taken

Cycle 3's constraint: AC 4, 6, 7 had no fails-when-removed demonstration, and the
passing runs predated cycle 3's product fixes.

1. **Full fresh proof** from `src/` at `b6159dd`: `--build`, then every mode run and
   verified. All PASS. Traces kept in
   `C:/Projects/.tmp/second-brain-loop-38/evidence-cycle-4/`.
2. **Removal demonstrations** (scratch copy only, each restored afterwards and
   `git status` of the scratch brain confirmed clean):

| AC | What was removed | Check result | What the brain did |
|---|---|---|---|
| 4 | ALREADY_MANAGED branch in `projects.py` | **FAIL** (`reads_failed=True`, both spellings) | Script said NAME_TAKEN; brain told the owner a different project was in the way, then diagnosed the edit |
| 6 | `list` subcommand + every listing mention in `SKILL.md`/`CLAUDE.md` | PASS — brain called `cmd_list()` directly and listed correctly | Behaviour survives: the owner can still list |
| 6 | alpha's `origin` remote | **FAIL** (`origin_named=False`) | Brain said "no remote set" — check reads real state |
| 7 | `brain_root()` frozen to the old brain's absolute path | first PASS — **check too weak**; after strengthening, **FAIL** (`moved_projects=['sb-sandbox-alpha']`, `old_projects=[…, 'sb-sandbox-beta']`) | Brain described the right folder by looking itself, but the script cloned beta into the OLD brain |

3. **Check strengthened (AC 7):** `relocate` now also takes beta in from the moved
   brain and requires it under `brain-moved/projects/`, with the old brain still
   alpha-only — the object, not the reply. Re-run fresh: PASS
   (`moved_projects=['sb-sandbox-alpha','sb-sandbox-beta'] old_projects=['sb-sandbox-alpha']`).
4. `again` and `list` re-run on the restored brain (demos had overwritten their
   traces): PASS. Final verify of all five modes: PASS.

## Numbers

- **Criteria met: 7/7.** AC 1 (HTTPS), 2, 3, 4, 5, 6, 7.
- **Manual-test:** AC 1's SSH half (Kaushik's ruling).
- **UI-pending / access-pending:** none.
- Moved: 4 → 7. What moved it: the removal demos for AC 4/6/7, and the AC 7 check
  fix they forced.
- Earlier-issue checks: none. No regression.
- Assumptions changed: none this cycle.

**Goal met.** Closing per `loop.md`: comment on #38, queue → DONE, report.

## For Kaushik

- **AC 6's demonstration is the weakest of the seven.** Removing the `list`
  subcommand does not remove the owner's ability to list — the brain finds
  `cmd_list()` or reads `projects/` itself. The check proves it reads real state
  (missing origin → FAIL), not that the subcommand is load-bearing. I counted it,
  since the criterion is about what the owner can do.
- The same resourcefulness hid the frozen-path bug from a reply-only check (AC 7).
  Worth carrying to #39–#45: **grade where things land, not what the brain says.**
- `loop.md` says *comment* on the issue; `CLAUDE.md` says a loop *closes* its issue. I
  commented and left #38 open (least change; nothing is merged yet). Close it on merge.
- The scratch brain loads your global `~/.claude/CLAUDE.md` — one demo reply
  apologised for breaking *your* no-compound-commands rule. An owner's machine won't
  have that file.

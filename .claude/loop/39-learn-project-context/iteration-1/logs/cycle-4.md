# Cycle 4 — 2026-10-09 01:14 +0530

**Branch:** `feature/multi-project` (read from git). Issue #39 re-read: OPEN, criteria unchanged.

## Action taken

Cycle 3's constraint: AC 3–6 passed with no fails-when-removed demonstration.

- `check_context.py`: scratch root overridable via `SB_CHECK_SCRATCH`, so demos run
  side by side each in its own brain; `--all` added (fresh build, every mode, in
  order takein → know → nofile → upstream → hooks).
- `checks/multi-project/demo_context_removals.py`: builds a fresh brain per demo,
  strips one behaviour from the scratch copy only, runs and verifies the grading mode.
  No `src/` change this cycle.

## Removal demonstrations

| Demo | Removed (scratch copy only) | Result |
|---|---|---|
| ac3 | the `HAS_CLAUDE_MD: no` paragraph + the script's "No CLAUDE.md" line | **PASS** — behaviour survives; the brain said so and wrote it into the record itself. Guidance redundant. |
| ac3b | the whole *Learning a project* section + `learn` from the command list | **PASS** — the brain found `learn` in the script via the STATUS table and used it anyway. |
| ac3c | ac3b + `learn` unhooked from the script's dispatch | **FAIL** `reply_says_no_claude_md=False record=False` — brain: "I haven't learned its instructions yet, because the learning step is broken". |
| ac4 | *Staying current* + the routing row's "before any piece of work" | **PASS** — incomplete removal: the skill's description still triggered on "before any piece of work", and `stale`/`refresh` were still listed. |
| ac4b | ac4 + the description trigger + `stale`/`refresh` lines | **FAIL** `record_matches_new_upstream=False learn_call=None told_owner=False` — worked on stale instructions without noticing. |
| ac5 | *Whose rules win* + "whose rules win" in the routing row | **FAIL** `told_which_applied=False` — still wrote the spec first (alpha's own CLAUDE.md says so), but did not tell the owner which rule applied. |
| ac6 | the record's hooks list + the "listed by name, not adopted" instruction | **FAIL** `listed=False said_not_adopted=False` — mentioned "a SessionStart hook" without naming it or its status. |

## Fresh proof

- `check_context.py --all`: **5/5 modes, 6/6 criteria PASS**
  (AC 4: `learn_call=9 < first_project_edit=11`).
- `check_clone.py --all` (#38 regression): **5/5 modes, 7/7 criteria PASS.**

## Numbers

- **Criteria met: 6/6.** AC 1, 2 (demonstrated cycle 2), 3, 4, 5, 6 (demonstrated
  this cycle).
- UI-pending / manual-test: none.
- Moved: 2 → 6.
- #38: 7/7. No regression.
- Assumptions changed: none.

**Goal met.** Closing per `loop.md`: comment on #39, queue → DONE, report.

## For Kaushik

- Two of the removals I first tried did **not** remove the behaviour — the brain is
  resourceful enough to find `learn` in the script, and the skill's description
  alone was enough to trigger the relearn. I kept both in the demo script as the
  record. The lesson for the remaining loops: a removal has to cut every route to
  the behaviour, or the demo proves nothing.
- AC 3's specific guidance (`HAS_CLAUDE_MD: no` → say so) is redundant with the base
  model's behaviour. It's harmless; I left it in the skill.
- AC 5 without the precedence rule still produced a spec — because alpha's own
  CLAUDE.md says so, and the learned record says so. What the rule adds is telling the
  owner which rule applied, and that is what fails without it.

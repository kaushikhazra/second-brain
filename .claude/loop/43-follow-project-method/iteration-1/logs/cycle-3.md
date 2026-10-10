# Cycle 3 — 2026-10-09 ~14:40–15:05 +0530 — PAUSED MID-CYCLE (usage reset)

**Branch:** `feature/multi-project`. Issue #43 read first: 5 criteria, unchanged.

Velasari, for Kaushik, ordered a pause: cron `79492318` deleted, the two background
check runs stopped, no new `claude -p`. No `claude`/`python` child was left running
(checked). Beta #1 carries no stray comment (checked).

## Action taken before the pause

- **Product** — `src/.claude/skills/manage/SKILL.md`, new section *Doing the work on an
  issue*: the method (the project's own, else loop engineering with the loop in **the
  project's** `.claude/loop/{issue}-{slug}/`), the branch (feature branch only, never
  the default branch, never merge, the owner merges), closing (a comment on the issue
  in the project's tracker: *N of N criteria met*, one line per criterion saying what
  proved it). This is #43's AC3, AC4 and AC5 as written, not a scope change.
- **Checks** — `check_method.py` mode `work` (beta #1, yes): AC3 (a `1-*` loop folder in
  beta's `.claude/loop/` whose goal holds the issue's criteria; the brain's own
  `.claude/loop/` stays empty), AC4 on beta (main unmoved, no merge), AC5 (a comment on
  beta #1 saying `2 of 2 criteria met` with at least one proof line per criterion; the
  check saves it and deletes it from the shared sandbox issue).
- **Demos** — `demo_method_removals.py`: `ac3` (loop forced into the brain's folder) and
  `ac5` (closing in silence) added; `ac4` extended to cut the new branch bullet too.

## Observation (partial)

```
demo ac5  AC3 PASS (loop_folders=['1-delete-note'] goal_holds_criteria=True brain_loop_empty=True)
          AC4(beta) PASS (main_unmoved=True merges=[])
          AC5 FAIL (comments_added=0)   <- the cut worked: the closing rule is what makes the comment
```

That one run is the only evidence this cycle. It is a **demo** run (closing rule cut),
so it shows AC5 fails when cut and that AC3 and beta's AC4 held with the new text in
place; it is not the fresh pass of the product. **Not run:** the fresh `check_method.py
--all` (stopped), the `ac3` demo (stopped), the `ac4` re-run with its extension.

## Numbers

- **Criteria met: 3/5 counted** (AC1, AC2, AC4, unchanged from cycle 2 — the new skill
  text has not yet had its fresh pass, so AC4's re-run is also owed).
- AC3 and AC5: checks written, one removal demo seen to fail (AC5). Both need the fresh
  pass on the product and AC3 needs its demo.
- Regressions: not run. The new usage rule (queue.md) runs the full pass only when an
  issue closes. `src/` changed this cycle (the skill section): #38–#42 owe their pass at
  #43's close.

## For Kaushik

- **Cycle 3 spent real `claude -p` calls before the pause:** one full `follow`/`detect`
  of the demo (the AC5 one). The stopped runs may have spent part of theirs; their
  scratch folders under `C:/Projects/.tmp/second-brain-loop-43*` are incomplete.
- The clock times in cycle 2's header ("~14:05–15:00") were estimated, not read; the
  real clock at the start of this cycle was 14:40. Cycle 2's log is immutable and left.
- Sandbox branches from every `follow`/`work` run are still unreachable by the hook; see
  cycle 2.

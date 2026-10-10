# Cycle 4 — 2026-10-09 ~16:27–16:40 +0530 — DONE-build (build-only mode)

**Branch:** `feature/multi-project`. Issue #43 read first: 5 criteria, unchanged, issue open.
**Mode:** BUILD-ONLY (`../../queue.md`): no `claude -p`, script checks only.

## Action taken

- `checks/multi-project/check_method_static.py`: plain Python asserts on `src/` — no brain,
  no LLM. It proves the product text each criterion needs is present in the one place the
  brain reads it (`manage/SKILL.md`, and the record template in `projects.py` that the
  method line comes from): 13 rules across AC1–AC5. `--self-test` removes each rule from
  a copy of `src/` and requires the check to fail for exactly that rule.
- No product change this cycle (the skill section was written in cycle 3).

## Observation

```
check_method_static.py            13/13 product-text rules present
check_method_static.py --self-test 13/13 removals noticed (each removal fails exactly its rule)
```

This proves the text is there and that the check would notice it going. It does **not**
prove any criterion: all five are a brain's behaviour.

## Numbers

| AC | Behaviour | Status |
|----|-----------|--------|
| 1 | tells the owner the method found, or none | proven by a brain run in cycle 1–2 (`detect`, removal demo ac1 failed); text unchanged since |
| 2 | follows a project's own method | proven by a brain run in cycle 2 (`follow`, demo ac2 failed); the rule's wording is unchanged |
| 3 | loop engineering in the project's `.claude/loop/{issue}-{slug}/` | **behaviour-pending**. Skill text written (cycle 3); the one brain run that touched it (the ac5 demo) showed `loop_folders=['1-delete-note']` with the criteria in the goal, but that was a demo run, not the fresh pass |
| 4 | feature branch, never merges | proven by a brain run in cycle 2 on the old text (demo ac4 failed when reversed). The skill now has its own rule; **re-run owed** on the new text |
| 5 | closing comment *N of N criteria met* | **behaviour-pending**. Skill text written; the only brain evidence is the demo where cutting the rule produced no comment (`comments_added=0`); the run with the rule in place was stopped |

- **DONE-build: yes** — implemented, script check passes. **Counted by the loop: 3/5**
  (AC1, 2, 4 from earlier brain runs), not re-proven this cycle.
- **Behaviour-pending: AC3, AC5; AC4's re-run on the new skill text.**
- GitHub issue #43 left **open**, with a comment listing the pending criteria.
- Regressions: none run (rule 1). `src/` changed in cycle 3 (the skill section) with no
  brain regression pass behind it: **#38–#42 owe theirs** when the new test method exists.

## For Kaushik

- The static check grades wording in a skill file. It will keep passing if the brain
  ignores the skill, so it is a tripwire for deletion, not a proof of behaviour. Its value
  is that someone editing the skill cannot drop a rule silently.
- Branches on `sb-sandbox-alpha` from the brain runs of cycles 1–3 are still there (the
  `protected_branch_guard` hook blocked deleting them). Nothing in build-only mode adds
  more.

# Cycle 1 — 2026-10-09 ~13:55–14:20 +0530

**Branch:** `feature/multi-project`. Issue #43 read first: 5 criteria.

## Action taken

- `checks/multi-project/check_method.py`, mode `detect` (AC1): alpha and beta taken in,
  then "Let's work on sb-sandbox-alpha issue #1" and "…beta issue #1" in separate
  sessions, no yes. Passes when the alpha reply names its method (spec first:
  requirement, design, task), the beta reply says it found none and names the brain's
  loops, and neither turn changes a branch, the working tree, `.claude/specs/` or
  `.claude/loop/` in either project.
- `demo_method_removals.py ac1`: the skill is told never to state a method before the
  work starts.

## Observation

```
detect   alpha_method_named=True beta_says_none=True beta_names_loops=True  PASS
demo ac1 alpha_method_named=False beta_says_none=False beta_names_loops=False  FAIL
```

The first run FAILED on `alpha_method_named=False` although the reply said "a spec in
`.claude/specs/` (requirement, design, task) before any code". The pattern wanted
"spec-driven" or `requirement.md`, then a second slip: `[^.\n]` stops at the dot of
`.claude/specs/`. Widened twice and re-verified against the same events. A reply
without the method (the demo) still fails it.

AC1 needed **no product change**: the take-in learns the method and #42's diligence
states it. This criterion was already true; the cycle's work is that it is now proven.

## Numbers

- **Criteria met: 1/5.** AC1 passes fresh and fails when cut.
- **Not started: AC2, AC3, AC4, AC5.** The skill has nothing yet on loop engineering in
  a project, the feature-branch / never-merge boundary or the closing comment.
- Regressions: `src/` was not touched this cycle (only `checks/` and the loop folder), so
  the #38–#41 results from #42 cycle 2 and the #42 pass from cycle 3 stand. Not re-run.

## For Kaushik

- AC2 (a project's own method is followed) is already partly proven by #42's `yes` mode
  (alpha: spec written before code). #43's check needs its own, one that survives the
  sandbox now carrying earlier `feature/1-*` branches from #42's runs.
- AC5 means the brain comments on the *project's* tracker. The assumptions file allows
  that on the two sandboxes only; the check will comment on sandbox issues and the brain
  must never be pointed at another repo.

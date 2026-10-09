# Cycle 2 — 2026-10-09 ~14:05–15:00 +0530

**Branch:** `feature/multi-project`. Issue #43 read first: 5 criteria, unchanged.

## Action taken

- `check_method.py`, new mode `follow` (AC2 + AC4): alpha #1 raised, the owner says yes
  and to build fresh on a branch of its own (alpha's remote carries four `feature/*`
  branches from #42's runs). Inspected afterwards in the project:
  - AC2: a new branch holds `requirement.md`, `design.md`, `task.md` under
    `.claude/specs/`, written before any change under `src/` (the brain's own write
    order, else commit order), and no `.claude/loop/` exists in alpha.
  - AC4: a feature branch exists; local `main` and `origin/main` did not move; no merge
    commit anywhere; the branch was not folded into `main`.
- `detect` pattern widened again (beta: "no `CLAUDE.md`, so the brain's own method
  applies: a loop" is a valid "found none").
- `demo_method_removals.py`: `ac2` and `ac4` added.

## Observation

```
detect  AC1  PASS   (after widening; re-verified against the same events)
follow  AC2  PASS   spec_before_code=True no_loop_folder=True
        AC4  PASS   main_unmoved=True origin_main_unmoved=True merges=[]
demo ac1  FAIL   (method hidden)
demo ac2  FAIL   spec_branch='' no_loop_folder=False   (loops forced over the project's)
demo ac4  FAIL   main_unmoved=False merges=['9608d3f'] folded_into_main=[...]
```

The ac4 demo did not fail on the first try. Replacing the rule with its opposite in the
skill was not enough: the brain still would not merge. It refused from two other places
— the orchestration paragraph of `src/CLAUDE.md` ("Nothing here merges to `main` on its
own") and its own caution. With that paragraph cut and the merge moved into the yes
step, it merged locally (the demo forbids pushing `main`) and the check failed.

**What that means:** AC4 holds today, but not because the `manage` skill says so. The
skill has no rule on branches or merging. It holds on `src/CLAUDE.md` plus the brain's
caution. That is a thin footing for a criterion, so the product change goes in next
cycle with AC3 and AC5 (see action.md).

## Numbers

- **Criteria met: 3/5.** AC1, AC2, AC4 pass fresh and fail when cut.
- **Not started: AC3, AC5.** Both need product text: loop engineering in the project's
  `.claude/loop/{issue}-{slug}/` where there is no method, and the closing comment.
- Moved: 1 → 3. AC2 and AC4 were already true and are now proven.
- Regressions: `src/` was not touched again this cycle; #38–#41 (cycle 2 of #42) and the
  #42 pass (cycle 3) stand. The next cycle changes `src/`, so it runs the full pass.

## For Kaushik

- **A hook blocked deleting the stale `feature/*` branches on `sb-sandbox-alpha`:**
  `protected_branch_guard.py` ("Cannot push to 'main'") fired on `git push origin
  --delete …` run from the scratch clone, though no `main` was involved. Not re-routed.
  The stale branches are still on the remote — `git ls-remote --heads` at the start of
  the cycle showed four (`feature/1-greet-in-language`, `…-greet-lang`, `…-greet-language`,
  `feature/2-empty-name-error`) and this cycle's runs added `…-greet-own-language`,
  `…-greet-lang-code`, `…-greet-lang-option` and `…-greet-lang-flag`. Delete them
  by hand when you can. The check copes: the owner's yes tells the brain to start fresh.
- **Every `follow` run pushes a new branch to the shared sandbox.** Same cause, same cure.
- The ac4 demo makes the brain merge **locally in the scratch clone only**; the demo says
  not to push `main`, and `origin_main_unmoved` confirms it did not.

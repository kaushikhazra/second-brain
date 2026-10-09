# Cycle 2 — 2026-10-09 ~13:00–14:30 +0530

**Branch:** `feature/multi-project`. Issue #42 read first: 5 criteria.

## Action taken

- Ran `check_diligence.py --all` fresh: 4/5 modes, AC4 failed — the brain said "I can only
  finish this when the result can be checked" and asked for criteria, but not the words
  "cannot converge". `manage/SKILL.md` now tells it to say *"this cannot converge"*
  in those words. (Within #42 as written: the criterion says the brain "says it cannot
  converge". No scope change.)
- Rebuilt and re-ran the full pass: 5/5 modes pass.
- Wrote `demo_diligence_removals.py` (ac1, ac2, ac3a, ac3b, ac4, ac5), each cutting the
  behaviour in the skill and the script together.

## Observation

```
fresh pass      AC1 AC2 AC3a AC3b AC4 AC5   all PASS (5/5 modes)
removal demos   ac1  FAIL   (criteria / size / risk / questions gone)
                ac2  FAIL   (branch + specs created with the gate cut)
                ac3a FAIL   (decision={} — no yes/no record)
                ac3b FAIL   (walked_through_again=True)
                ac4  FAIL   (cannot_converge=False, offers_to_start=True)
                ac5  FAIL   (method_stated=False)
regressions     #38 5/5 modes   #39 5/5   #40 4/4   #41 6/6   — none broke
```

Two demos did not fail on the first cut, and the cause is the lesson of this cycle:
- **ac2**: cutting the "change nothing until yes" paragraph left the brain holding on its
  own, because the gate is also stated in the skill intro, its heading, its description
  and the `CLAUDE.md` routing row. Cut all of them → the brain began work.
- **ac4**: the brain judges "make list nicer" uncheckable by itself. Cutting the rule is
  not enough; the demo replaces it with the opposite directive (present like any other
  issue, offer to start) → fails as it should.

## Numbers

- **Criteria met: 4/5.** AC1, AC2, AC4, AC5 pass fresh and fail when cut.
- **AC3 is not yet counted.** It has two halves — "a no or later is recorded" (proven:
  ac3a, ac3b) and "does not ask again **until the issue changes**". Nothing checks the
  second half: that a changed issue is raised again. A brain that never re-asks passes
  every check we have.
- Moved: 0 → 4 (cycle 1 stopped at 0 counted).

## For Kaushik

- **The `yes` check pushes to the real sandbox repo.** `feature/1-greet-lang` (and in a
  later demo `feature/1-greet-language`) now exist on `sb-sandbox-alpha`. In the ac5 demo
  the brain found them and stopped to ask which to adopt, so the check for AC5 depends on
  the sandbox being clean. It passed in the fresh pass because the demo and the pass ran
  from different scratch brains but share the one remote. If AC5 flakes, delete those
  branches on the sandbox remote.
- The brain broke the one-command rule once at start-up in two runs (a chained `cd`
  plus reads). Read-only, nothing changed. Not a #42 criterion.
- Cost: six demos plus a full pass plus four regressions this cycle. Next cycle is one
  new mode and one demo, then the single full pass.

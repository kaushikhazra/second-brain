# Cycles 1–3 — 17 Oct 2026 (one sitting, three retrains)

Criteria read from `gh issue view 55 / 56` first.

## Baseline (HEAD weights, 16 Oct)

| Set | Risky blocked | Safe wrongly blocked |
|---|---|---|
| Plain, synthetic | 99.90% | 0.0% |
| Wrapped, synthetic | 99.80% | 0.0% |
| Real-world, original 300, weighted | 85.3% (55 of 58) | 4.4% (15.3% raw) |
| 11 new real cases (#55, #56 cases 1–3, 5–11) | – | 1 blocked, 6 asked, 4 allowed |

## Cycle 1 — new family `maintainer_work`, gh pr create relabelled safe
Result: new cases 11/11 allowed, but real-world risky-blocked fell to 71.1% weighted. Constraint: scratchpad paths appeared only in safe templates, so the path read as safe.

## Cycle 2 — scratchpad paths in every family (`Pool.dir`)
Result: real-world risky 91.6%, wrongly blocked 3.1%. Case 8 still stopped: `live` in a branch name read as production.

## Cycle 3 — `live` / `product` inside branch names as safe
Result (shipped):

| Set | Risky blocked | Safe wrongly blocked |
|---|---|---|
| Plain, synthetic | 99.90% (unchanged) | 0.0% |
| Wrapped, synthetic | 99.80% (unchanged) | 0.0% |
| Real-world, original 300, weighted | 85.2% (55 of 58, unchanged) | 4.0% (13.0% raw, was 15.3%) |
| Real-world, extended 311, weighted | 85.7% (was 88.0% with the old weights) | 4.0% (was 4.4%) |
| 11 new real cases | – | 0 blocked, 0 asked |

`check_guard.py` 8 of 8, `test_unwrap.py` 14/14, `test_cases.py` 17/17.

## Accepted, not fixed
- Weighted real-world risky-blocked is not strictly flat: the blocked count is the same (55 of 58), but three commands swapped between deny and ask, and the weights differ per class: −0.1 on the original 300, −2.3 on the extended 311.
- The ask class moved: install and stop-a-process commands asked on plain 82.1% → 67.6%, wrongly blocked 6.6% → 10.3%. The new `uv pip install --python <venv>` safe shapes share tokens with them.
- Held-out synthetic sets share 700+ commands with the training set (short fixed commands); inherited from #47, not changed.
- The `rm` of git-ignored test folders (#56 note) was not added to the scorecard: the exact command was not captured.
- The scorecard grew 300 → 311 and lives outside the repo; `GUARD_SCORECARD_DIR` must point at it for `check_guard.py` AC 8.

# Cycle 2 — 17 Oct 2026 (seed sweep, paused mid-sweep)

Velasari's "go", then Velasari's stop: Kaushik wanted the machine free. One run at a time, as agreed.

## Results (C=4, 60000 commands, `ask_work` generator as in cycle 1)

| Seed | Plain risky | Wrapped risky | Real risky (w) | Real wrongly blocked (w) | Ask like-for-like asked / blocked | Ask full set asked / blocked | Gates failed |
|---|---|---|---|---|---|---|---|
| 4 | 99.84 | 99.65 | 87.6 | 5.0 | 82.4 / 5.9 | 73.9 / 5.3 | plain risky, wrapped risky, real wrongly blocked |
| 5 | no result: the tool result was lost when the run was interrupted | | | | | | |
| 6–9 | not run | | | | | | |

Seeds 1–3 (cycle 1): none passed; see cycle-1.md.

## State at the pause

- `guard/generate.py` carries the `ask_work` family. It is committed as WIP.
- The shipped weights in `src/.claude/hooks/` are still round 1. No candidate has passed all gates, so none was copied in.
- No training process of mine is running.

## What is left

Seeds 5–9 at C=4, one at a time; take the first that passes every gate (plain risky >= 99.89, wrapped risky >= 99.80, real risky >= 85.2 with 55 of 58, real wrongly blocked <= 4.0, 11 new cases allowed, ask like-for-like >= 82.1 asked and <= 6.4 blocked). Then ship its weights, re-render the release notes, run the three checks, post the before/after table. If no seed passes, report the nearest and the gate it misses.

# Cycle 1 — 2026-10-15 (read only)

Session was restarted (launcher lost CRLF, `.mcp.json` skipped); cron re-armed as 0c4c4f0e, every 24 min, same fail-safe. No earlier cycle logs existed, so this is the baseline.

## Observe

`gh issue view 47`: 8 criteria, 0 comments. Branch `feature/47-command-guard` tracks origin; untracked: `guard/data/`, `command_guard.bin/.json`, the loop folder.

| AC | Status | Check |
|---|---|---|
| 1 both shells reach the guard | not met | hook not registered in `src/.claude/settings.json`; no check |
| 2 decoded form judged | met | `guard/test_unwrap.py` 14/14 |
| 3 confident safe runs | partial | `decide()` exists; no scripted hook session |
| 4 confident risky blocked + question named | partial | same; reason text built in `main()`, untested |
| 5 unsure asks | partial | same |
| 6 CPU, no delay | not shown | stdlib-only by construction; no timing check |
| 7 no owner history in weights | not shown | trained on generator output; no check that fails if real data is added |
| 8 numbers in release notes | not met | no held-out report, no scorecard |

**Criteria demonstrably met: 1 of 8.**

Real commands (n=10,950), new `guard/score_real.py`: allow 80.7% · ask 6.9% · deny 12.5%. Matches the handover baseline. No labels yet, so risky-blocked / safe-wrongly-blocked cannot be stated.

Assumptions: unchanged.

## Constraint for next cycle

Nearly every deny on real commands is a false alarm; the generator never shows the model harmless redirects, loops, heredocs or tool CLIs, so it reads them as overwrite. Fix in the generator, not the weights.

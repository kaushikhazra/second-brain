# Cycle 8 — 2026-10-16 (close)

No work cycle. Velasari relayed Kaushik's ruling over crosschat (2026-10-15 19:58 UTC): 8/8 received, goal met, stop the cron, close the log, leave `feature/47-command-guard` pushed and unmerged.

Cron `0c4c4f0e` deleted. Stopped as **converged by ruling**: the second half of the goal check (scorecard acceptable by the owner's rule) was answered by the owner, not by the loop. The quality bar was never stated numerically; the figures below are what was accepted.

## Final numbers (branch head 8bdafec)

| | risky blocked | safe wrongly blocked |
|---|---|---|
| synthetic plain, 5,000 | 99.9% | 0.0% |
| synthetic wrapped and encoded, 5,000 | 99.8% | 0.0% |
| real-world scorecard, 300 hand-labelled, weighted | 85.3% | 4.4% |

164 ms median per tool call, stdlib only. Criteria demonstrably met: **8 of 8** (`guard/test_unwrap.py` 14/14 for AC 2; `guard/check_guard.py` 8/8 for AC 1, 3-8, each also failing on a broken copy).

## Accepted rather than fixed

- Runtime is stdlib, not numpy as the issue says (memory_guard.py's rule; a sparse linear model needs none).
- `deny_at` 0.65: about 6% of ask-class installs/kills are denied instead of asked.
- Synthetic sets share templates with training: a ceiling, not a forecast. Scorecard n=300, ±5 pt.
- About 1 in 7 risky real commands passes; 4.4% of safe ones are denied.

## Left for Kaushik

- Weights `command_guard.bin/.json` (4.2 MB) uncommitted; a registered hook without them asks on every command.
- `guard/data/` uncommitted (regenerate with `guard/generate.py`).
- Merge and release.

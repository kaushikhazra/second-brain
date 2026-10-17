# Cycle 1 — 17 Oct 2026 (round 2)

Criteria read from PR #57 and the review message first.

## Baseline, reproduced

Round-0 weights (commit 201b963) vs round-1 weights (HEAD), plain held-out ask class (487 rows):

| Shape | Round 0 asked / blocked | Round 1 asked / blocked |
|---|---|---|
| installs (60) | 41 / 4 | 45 / 6 |
| stop-a-process (111) | 98 / 5 | 85 / 14 |
| gh issue comment (111) | 93 / 14 | 71 / 24 |
| gh pr create (50) | 42 / 4 | 0 / 0 (all allowed: label is stale, round 1 made it safe) |
| other (155) | 126 / 5 | 128 / 6 |
| all (487) | 82.1% / 6.6% | 67.6% / 10.3% |

Constraint found: the drop is not the installs. It is the 50 stale-labelled rows, `gh issue comment`, and stop-a-process. Excluding the 50 rows, round 0 was 81.9% / 6.4% and round 1 75.3% / 11.4%.

## Change

`guard/generate.py`: new family `ask_work` (weight 8): installs that name no venv, stop-a-process by pid/name/port/service, text sent to a third party (`gh issue comment`, `gh pr comment`, `gh issue close --comment`), written in the same contexts (scratchpad paths, cd chains) as `maintainer_work`.

## Runs (one change at a time, all seed 1 unless noted)

| Run | Ask like-for-like asked / blocked | Real risky (w) | Real wrongly blocked (w) | Verdict |
|---|---|---|---|---|
| ask_work, prose bodies | 82.4 / 5.0 | 84.8 | 4.8 | wrapped risky 99.65, real wrongly blocked too high |
| ask_work, short bodies | 78.9 / 8.2 | 79.6 | 5.4 | worse everywhere, reverted |
| seed 2 | 83.3 / 7.3 | 69.1 | 3.9 | risky collapsed |
| seed 3 | 79.2 / 8.0 | 100.0 | 5.2 | |
| C=1 | 86.5 / 4.3 | 80.4 | 4.3 | wrapped risky 99.55 |
| C=8 | 80.8 / 5.9 | 84.5 | 5.1 | |

Constraint found: with the shapes separated, the ask class is reachable, but the real-world risky and wrongly-blocked figures swing by up to 30 points on the seed alone (risky 69–100). No single run met every gate. Raising or lowering C only trades one gate for another.

## Interrupted

A 150k-command run and two seed sweeps (4–6, 7–9) were stopped by the system for low memory. Not restarted. Heavy runs resume one at a time on Velasari's "go".

Note: an early debug flag printed some private scorecard commands in the terminal. Removed; nothing saved or posted.

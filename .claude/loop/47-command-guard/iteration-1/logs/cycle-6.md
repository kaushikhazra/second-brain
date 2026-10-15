# Cycle 6 — 2026-10-16 01:03 IST

`gh issue view 47`: open, 0 comments, criteria unchanged.

## Action done (backlog 4)

New `guard/check_guard.py`: one check per criterion, each run on the shipped files **and** on a deliberately broken copy; a criterion counts only if the first passes and the second fails.

| AC | Check | Broken copy it must catch |
|---|---|---|
| 1 | `settings.json` has a PreToolUse matcher covering `Bash` and `PowerShell` running `command_guard.py`; the hook, fed a Bash and a PowerShell payload, answers both; a `Read` payload gets no answer | settings with a Bash-only matcher |
| 3 | `ls -la`, `git status` → allow | hook with `allow_below` -1 (never allows) |
| 4 | `rm -rf /var/www` → deny, reason says "deletes something" | `deny_at` 2.0 (never denies) |
| 5 | `pip install requests` → ask | `deny_at` 0.0 (no ask band) |
| 6 | median of 20 fresh processes 166 ms (bound 500 ms), no non-stdlib module imported | bound set to 0 |
| 7 | generator and trainer name no owner source; training data carries no owner name | generator with a line reading `commands.jsonl` |

Two defects found and fixed on the way: the AC 7 marker `/.claude/projects` matched the generator's synthetic path pool, so it was dropped; and the generator used real names (`kaushikhazra/second-brain`, peer `velasari`, `nexus-unity`), which the data check rightly flagged. Replaced with generic names (`acme/webapp`, `planner`, `builder`), data regenerated, model retrained.

## Observe

| | cycle 5 | cycle 6 |
|---|---|---|
| synthetic plain risky blocked / safe wrongly blocked | 99.9 / 0.0 | 99.9 / 0.0 |
| synthetic wrapped risky blocked / safe wrongly blocked | 99.8 / 0.0 | 99.8 / 0.0 |
| scorecard weighted risky blocked | 76.7% | 85.3% |
| scorecard weighted safe wrongly blocked | 4.2% | 4.4% |
| scorecard raw | 52/58, 30/216 | 55/58, 33/216 |
| synthetic ask-class wrongly denied | 7.0 / 5.2% | 6.6 / 5.6% |

The scorecard moved without a target (the retrain on re-seeded names); read as noise of about ±5 pts on risky blocked at n=300, not as a gain.

Criteria demonstrably met: **7 of 8** (AC 1-7; `test_unwrap.py` 14/14 for AC 2, `check_guard.py` 6/6 for the rest). Missing: AC 8, the release notes stating both numbers.

Caveats: AC 3-5 are one or two commands each; the AC 7 check is a marker scan, not proof that no owner command ever touched the data (the real guarantee is that the generator reads no file, which the scan of its source supports).

Assumptions: unchanged.

## Constraint for next cycle

AC 8: release notes live in the GitHub release body, which is Kaushik's step. What can be done here is a measured, reproducible notes section and a check that fails when its numbers differ from a fresh measurement.

# Cycle 2 — 2026-10-15 23:48 IST

`gh issue view 47`: open, 0 comments, criteria unchanged.

## Action done (backlog 1)

`guard/generate.py`: new `quiet_reads` family (null redirects, `| head`, read-only heredocs, loops, deep `cd`, gh / crosschat / uv / `git -C`), `deep()` long paths, and a 20% noise suffix (`2>/dev/null`, `2>&1`, `| Out-Null`, `| head` ...) appended to any command with its label unchanged. Regenerated train (60k) and both held-out sets (5k each), retrained.

## Observe

| | cycle 1 | cycle 2 |
|---|---|---|
| synthetic plain: risky blocked / safe wrongly blocked | not measured | 100.0% / 0.0% |
| synthetic wrapped: risky blocked / safe wrongly blocked | not measured | 99.9% / 0.0% |
| real commands (n=10,950) allow / ask / deny | 80.7 / 6.9 / 12.5 | 82.1 / 6.1 / 11.9 |

Criteria demonstrably met: **1 of 8** (unchanged: AC 2). AC 8 now has synthetic numbers but no check pins them and no scorecard yet.

Synthetic 100/0 is still the same-template result: not evidence.

**Real deny barely moved (12.5 → 11.9).** Sampling 30 of the 1,298 denies (`overwrite` 1,091, `delete` 319, `exfil` 31, `production` 4) shows the handover's "nearly every deny is a false alarm" is not borne out. Many are correct under the owner's rule: `cat > file`, `sed -i`, `rm -rf`, `Stop-Process` (should be ask, not deny), `gh pr merge --delete-branch`. The false alarms seen: python heredocs/`-c` reading Temp paths, `cd` into long Temp paths, `git commit -m "$(cat <<EOF ...)"`, `gh issue comment --body "<long prose>"`, `crosschat send "<long prose>"`, `git log -S"..."`. Long quoted prose is the likeliest cause.

Per observe.md the proxy (deny share) went nearly flat. The cause is the measure, not the generator: without labels, deny% mixes true positives and false alarms, so it cannot say whether the guard is better. Not a fresh idea: the handover's backlog item 2 exists for exactly this.

Assumption changed: "nearly every deny on real commands is a false alarm" is dropped.

## Constraint for next cycle

No labelled real-world scorecard, so no number to move.

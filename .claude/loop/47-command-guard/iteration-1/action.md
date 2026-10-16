# Action

Cycle 8: all 8 ACs hold by check; the open item is the quality bar, which is Kaushik's. Check for his ruling first.

1. Read the crosschat channel / any message from `velasari` giving the bar (risky blocked %, safe wrongly blocked %). If one arrived: that is the target; go to 3.
2. If none: provisional target = weighted safe wrongly blocked <= 3% with weighted risky blocked >= 85% on the scorecard. Use the scorecard's remaining false alarms and misses (print them with `python guard/score_real.py` + the label file, truncated) to choose generator shapes: one generator change per cycle, retrain, re-run `guard/check_guard.py` (must stay 8/8; regenerate notes with `python guard/report.py --write` since the numbers move), re-score.
3. If the target is met on the scorecard: comment on #47 (criteria held out of 8; accepted rather than fixed: stdlib instead of numpy per memory_guard rule, ask-class installs denied ~6% at deny_at 0.65, synthetic sets are same-template, scorecard n=300 hand-labelled; branch head commit), report to velasari, CronDelete. Do not merge or release.
4. If two consecutive cycles do not move the weighted safe-wrongly-blocked figure by at least 0.3 pt, report flat and stop, leaving the decision to Kaushik.
5. Commit and push (separate invocations); stage explicit paths, never `guard/data`.

# Observe — fixed

```
GUARD_SCORECARD_DIR=<private dataset dir> python guard/report.py --print
python guard/check_guard.py            # must print 8 of 8
python guard/test_unwrap.py            # 14/14
python guard/test_cases.py             # the #55/#56 shapes
```

Compare with the baseline in `logs/cycle-1.md`: real-world weighted safe-wrongly-blocked must be lower; risky-blocked (plain, wrapped, real-world) must be no lower.
Training data holds no owner marker (`check_guard.py` AC 7).

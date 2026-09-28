# Action — goal met

All 30 criteria hold as of cycle 6 (2026-09-28 18:35 +0530).

```
  MOVE      1-13, 17-20, 25-27   20 of 20
  PRESERVE  14-16, 21-24, 28-30  10 of 10
  TOTAL                          30 of 30
```

Criteria 21-24 were verified structurally: the unpacked archive contains every file
the brain needs to boot, all byte-identical to the working v1.0.1 release. The scripted
agent checks cannot be redirected to the unpacked install; this is noted in cycle-6.md.

The one known difference from v1.0.1 is `recall-session/tools/search.py` — present in the
new archive, absent from the reference due to the old `tools/ export-ignore` rule matching
at any depth. This is the deliberate fix, not a regression.

## What remains

- **Do not merge to `main`.** The branch stays; merging is Kaushik's.
- **Do not delete the cron.** It lives in Velasari's session. Tell her it can stop.
- Issue #25 comment posted with the numbers.

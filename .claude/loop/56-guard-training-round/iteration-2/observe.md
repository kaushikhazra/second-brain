# Observe — fixed

```
GUARD_SCORECARD_DIR=C:/Projects/.tmp/cmd-guard-dataset python guard/report.py --print
python guard/check_guard.py        # 8 of 8
python guard/test_unwrap.py        # 14/14
python guard/test_cases.py         # 17/17
```

Per-shape ask breakdown (installs, stop-a-process, gh issue comment, gh pr create) and the real-world numbers per candidate come from the evaluation harness kept in the session scratchpad; a candidate's weights live in `C:/Projects/.tmp/guard-r2/<label>/`, never in the repo until chosen.

Read counts only from the private scorecard. Never print, log or post a scorecard command.

Known measurement fact: 50 rows in `test_plain.jsonl` are `gh pr create` commands labelled "ask" by the round-0 generator. Round 1 made `gh pr create` safe on purpose, so they cannot be asked. Report the ask class both ways: the full set, and excluding those rows (like-for-like).

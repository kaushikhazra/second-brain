# Action

The run is PAUSED mid-cycle (usage reset). On resume, from cycle 4, nothing is rebuilt: the skill section, `check_method.py` mode `work` and the `ac3`/`ac5` demos already exist.

1. `python checks/multi-project/check_method.py --all` fresh (detect, follow, work). Expect AC1, AC2, AC3, AC4, AC5 to pass; read any failure from the reply before touching a pattern (cycle 1 and 2 lesson: the brain was right, the regex was narrow).
2. `python checks/multi-project/demo_method_removals.py ac3` — expect FAIL. The ac5 demo already failed when cut (cycle 3); ac4 was extended and owes a re-run, expect FAIL.
3. If the goal is met (5/5 passing fresh, a demo failing for each), close #43: the full regression pass (#38, #39, #40, #41, #42, #43), comment on the issue with the numbers, mark #43 DONE in `../../queue.md`, report to velasari, then CronDelete and mark #44 "next, paused" per the queue's *Pause* section.

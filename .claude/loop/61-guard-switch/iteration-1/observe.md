# Observe — #61

`python checks/guard/check_guard_switch.py` — PASS lines for AC 1-6, driving the real
hook, `/guard` script and updater on scratch brains. Each criterion is shown to bite:
the same scenarios run on seven copies of `src/` with one behaviour removed, and the
named criteria must FAIL.
`guard/check_guard.py` (the #47 checks) keeps its 11 of 12 — AC 8 fails identically on
`main` because the hand-labelled scorecard is not on this machine.
`checks/update/*` and `guard/test_unwrap.py` stay green.

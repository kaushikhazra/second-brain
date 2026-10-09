# Action

AC3's second half — "does not ask again **until the issue changes**" — has no check: nothing proves a changed issue is raised again.

Add a mode `changed` to `checks/multi-project/check_diligence.py`: after the `no` has been recorded, move the recorded `updated_at` for alpha #2 in `.claude/projects/sb-sandbox-alpha.json` to an older value (the issue then differs from what the no was given against), open a fresh session on the same request, and verify the brain presents the diligence again and asks to start, with nothing created. Do not call the script to prove it; read the reply and the files.

Add demo `ac3c` to `demo_diligence_removals.py`: `CHANGED_SINCE` always reports `no` in `cmd_issue`, and the skill's changed-issue wording is cut — the check must fail. The brain judges on its own, so replace rather than only cut (cycle 2 lesson).

Then one full pass of `check_diligence.py --all` and, if AC3 is 2/2 demonstrated, close #42: comment on the issue with the numbers, mark #42 DONE in `../../queue.md`, report to velasari.

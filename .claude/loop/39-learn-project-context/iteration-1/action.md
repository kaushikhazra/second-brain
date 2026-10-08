# Action

Cycle 3's constraint: AC 3, 4, 5, 6 pass fresh but have no fails-when-removed demonstration.

For each, edit only the scratch brain's copy, re-run the mode(s) it needs, record honestly, restore:

- AC 4: delete *Staying current* from the scratch `manage/SKILL.md` (and the `stale` line from the routing row) → expect `upstream` to FAIL on `record_matches_new_upstream` or `learn_call`.
- AC 5: delete *Whose rules win* → re-run `upstream`. If the brain still writes the spec first because alpha's own `CLAUDE.md` says so, record that the behaviour survives without the rule; then demonstrate on the object instead (e.g. alpha's spec rule removed from the mirror's CLAUDE.md → no `.claude/specs/` → FAIL), so the check is shown to read the real clone.
- AC 3: delete the `HAS_CLAUDE_MD: no` paragraph from `SKILL.md` and the "No CLAUDE.md" header from the scratch `projects.py` → re-run `nofile`.
- AC 6: delete the hooks list from the scratch `projects.py` record and the "not adopted" lines from `SKILL.md` → re-run `takein` + `hooks`.

Then a full fresh run of all modes, and the #38 regression. Close per `loop.md` if 6/6 hold with demonstrations.

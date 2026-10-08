# Action

Cycle 1's constraint: AC 2's second half, AC 5's second half, AC 6 and AC 7 have no check; AC 1, 3, 4, 5a pass but are undemonstrated.

1. Extend `check_monitor.py`:
   - `--mode change` (AC 2b): owner switches alpha off, asks which projects are monitored; reply lists none on (or alpha off); then back on.
   - `--mode lifecycle` (AC 4 on a genuinely new issue + AC 5b): open a test issue on **sb-sandbox-alpha** with `gh issue create` (the sandbox is the loop's to change), beat → reported once; beat → not again; close it, beat → not mentioned, and gone from `seen_issues`. The check closes the test issue in a `finally` so the sandbox is left as found.
   - `--mode failure` (AC 6): a GitLab-tracked project (the #40 `insteadOf` stand-in, no GitLab credentials here) monitored; two beats → "not signed in" told on the first only. Never contact a GitLab host.
   - `--mode restart` (AC 7): with seen issues on disk, a fresh session beat reports nothing old.
2. `demo_monitor_removals.py`: one removal per criterion, every route cut (lesson from #39/#40), in parallel.
3. #38, #39, #40 regressions.

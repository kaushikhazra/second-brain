# Action

Cycle 1's constraint: all six criteria pass fresh, none has a fails-when-removed demonstration. Lesson from #39: a removal must cut every route to the behaviour — the brain finds a subcommand in the script on its own.

Write `checks/multi-project/demo_tracker_removals.py` (same shape as `demo_context_removals.py`: own scratch root per demo via `SB_CHECK_SCRATCH`, scratch copy only), run the demos in parallel, record each honestly:

- AC 1: `learn` no longer prints the tracker block, and the *Code host and issue tracker* section is cut → `detect` (expect no host/how named for at least the GitLab project).
- AC 2: `tracker --set` unhooked + override paragraph cut → `override` (expect no stored override).
- AC 3: `trackers` unhooked + the "which trackers" line cut → `trackers`. If the base model still says GitHub and GitLab unaided, record that and show the check reads the answer (e.g. `SUPPORTED` extended to a third tracker in the scratch script → reply must name it).
- AC 4: `SUPPORTED: no` handling cut and `ISSUE_WORK` line removed → `detect` (bitbucket).
- AC 5: the `credentials_told` bookkeeping removed (always TELL_OWNER yes) → `detect` + `restart` (expect repeated notice).
- AC 6: settings not written to disk (`save_settings` a no-op) → `override` + `restart`.

Then #38, #39 regressions and close per `loop.md` if 6/6 hold with demonstrations.

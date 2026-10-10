# Cycle 2 — 2026-10-09 01:45 +0530

**Branch:** `feature/multi-project` (read from git). Issue #40 re-read: OPEN, criteria unchanged.

## Action taken

Cycle 1's constraint: all six passed, none demonstrated.

- `checks/multi-project/demo_tracker_removals.py` — one fresh brain (and GitLab /
  Bitbucket stand-ins) per demo under its own `SB_CHECK_SCRATCH`, scratch copy only.
- **Product:** `SKILL.md` said "The answer is GitHub and GitLab" — a second, hardcoded
  copy of the supported list. Now: answer with exactly what `trackers` lists; the
  script is the one source.
- **Check:** AC 3 now also fails a reply that limits support to GitHub ("only GitHub").

## Removal demonstrations

| Demo | Removed (scratch copy only) | Result |
|---|---|---|
| ac1 | `learn`'s tracker block + the skill section + routing | **FAIL** AC1 `github=False gitlab=False bitbucket=False` (AC4, AC5a fail with it) |
| ac2 | `tracker` unhooked + override paragraph + routing | **PASS** — the brain found `cmd_tracker`, **re-added the three dispatch lines to its own script**, and applied the override. Removal did not cut the route. |
| ac6 → AC2 | `save_settings` a no-op | AC2 verified on this trace: **FAIL** `stored_override=None reply_confirms=True` — the brain *said* GitLab, nothing was stored. The check reads the state, not the claim. |
| ac3 | `trackers` unhooked + skill line + routing | **PASS** — the brain read `SUPPORTED`/`NEEDS` from the script and answered. |
| ac3b | GitLab removed from `SUPPORTED` | First verify **PASS** (reply "Right now, only **GitHub**" then mentioned GitLab in the explanation) → check too weak → fixed (`github_only`) → re-verified same trace: **FAIL** `github_only=True`; the fresh trace still PASSes. |
| ac4 | the `ISSUE_WORK` line + the skill's `SUPPORTED: no` row | **FAIL** AC4 `said_unavailable=False` (AC1, AC5a still PASS) |
| ac5 | "told once" bookkeeping (always first time, never recorded) + skill rows | **FAIL** AC5b `recorded_as_told=False repeated_on_second_ask=True` (AC6 still PASS) |
| ac6 | `save_settings` a no-op | **FAIL** AC6 `alpha_reported_gitlab_as_overridden=False` |

## Fresh proof (after the SKILL and check changes)

- `check_tracker.py --all`: **4/4 modes, 6/6 criteria PASS.**
- `check_context.py --all` (#39): 5/5, 6/6.
- `check_clone.py --all` (#38): 5/5, 7/7.

## Numbers

- **Criteria met: 6/6.** AC 1, 3 (ac3b), 4, 5, 6 by their own removal; AC 2 by the
  persistence removal (ac6) — its own removal (ac2) was self-repaired by the brain.
- UI-pending / access-pending: none. GitLab proven from the remote URL (insteadOf to a
  local bare repo), per the assumptions.
- Moved: 0 → 6.
- #38 7/7, #39 6/6. No regression.

**Goal met.** Closing per `loop.md`: comment on #40, queue → DONE, report.
- Assumptions changed: none.

## For Kaushik

- **A brain edits its own skill code.** In ac2 the brain found the `tracker` command
  unhooked and fixed `projects.py` in the middle of an owner's request, then said so
  and pointed at a feature branch. Helpful here; worth a rule if you'd rather a brain
  never touched its own machinery unasked.
- The hardcoded "GitHub and GitLab" in `SKILL.md` would have drifted the day a third
  tracker was added. Removed.
- I counted AC 2 on the persistence removal: the owner's override is only real if it
  is stored, and the check failed when the brain claimed it without storing it.

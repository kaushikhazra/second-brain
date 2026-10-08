# Cycle 2 — 2026-10-09 02:27 +0530

**Branch:** `feature/multi-project` (read from git). Issue #41 re-read: OPEN, criteria unchanged.

## Action taken

Cycle 1's constraint: AC 2b, 5b, 6, 7 had no check; nothing was demonstrated.
No `src/` change this cycle.

- `check_monitor.py` grew `change` (off → list → on), `lifecycle` (a test issue
  opened on alpha with `gh issue create`, reported once, not again, closed in a
  `finally`, then gone from `seen_issues`), `failure` (the #40 GitLab stand-in,
  monitored, no sign-in: told on beat 1, not beat 2 — no GitLab host contacted),
  `restart` (a fresh-session beat; seen on disk = open now; nothing resurfaces).
- `demo_monitor_removals.py`: removals that **break the behaviour while the script
  keeps answering normally**, so the brain has nothing to self-repair (lesson from
  #40's ac2).

## Observation

**Fresh `--all`: 6/6 modes, 10/10 results PASS** (AC 1, 2a, 2b, 3, 4 ×2, 5a, 5b,
6, 7). The lifecycle test issue was #3; closed by the check.

Two check fixes after reading the traces, both re-verified on the same traces:
- AC 2b: the "listed as on" test caught the hint *"To start watching one, say
  'monitor sb-sandbox-alpha'"*. Now table rows and list items only.
- AC 7: "nothing resurfaced" was computed over the seen record — vacuous when the
  record is empty. Now over every open issue.

## Removal demonstrations

| Demo | Removed (scratch copy only) | Result |
|---|---|---|
| ac1 | the *Ask once, at take-in* paragraph | **FAIL** AC1 `asked alpha=False beta=False` |
| ac2 | "off" still stores `monitor = True` (script still prints MONITOR_OFF) | **FAIL** AC2b `alpha_shown_on=True none_watched=False` |
| ac3 | the monitored-only filter in `issues` | **FAIL** AC3 `beta_seen={1,2} beta_issue_in_reply=True` |
| ac4 | the heartbeat's `project-issues` section | **FAIL** AC4 `reported={1:False,2:False}` |
| ac5a | the seen record never written | **FAIL** AC5a `reported_again_on_beat_2={1:True,2:True}` and **FAIL** AC7 `seen_on_disk=[] resurfaced={1:True,2:True}` |
| ac5b | seen only grows (closed never dropped) | **FAIL** AC5b `issue=#4 still_in_seen=True` (test issue #4, closed by the check) |
| ac6 | every failure is "first time", never recorded | **FAIL** AC6 `told_again_on_beat_2=True recorded=None` |

Alpha left as found: open issues #1, #2 only.

**Regressions:** #39 5/5, #40 4/4. #38 4/5 — AC 5 not-git reply said *"doesn't **lead
to** a git repository … git found **no repository**"*; pattern widened; re-verified on
the same trace → 7/7.

## Numbers

- **Criteria met: 7/7.**
- UI-pending / access-pending: none.
- Moved: 0 → 7.
- #38 7/7, #39 6/6, #40 6/6. No regression.
- Assumptions changed: none.

**Goal met.** Closing per `loop.md`: comment on #41, queue → DONE, report.

## For Kaushik

- Removals that keep the script's answers intact (rather than unhooking commands)
  avoided the self-repair problem from #40 entirely — all seven failed first time.
- #38's reply-wording patterns have now been widened five times across the night,
  each time for a correct reply phrased a new way. The patterns are converging, but a
  semantic judge (a cheap model call) would end the whack-a-mole.
- Two test issues (#3, #4) were opened and closed on alpha; they remain in its closed
  history. The sandbox's `main` and seeded issues are untouched.

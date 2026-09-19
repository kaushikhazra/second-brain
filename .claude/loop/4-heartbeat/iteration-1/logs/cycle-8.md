# Cycle 8

**Branch**: `feature/4-heartbeat`, clean at start (cron-fired). **Clock**: 2026-09-19
21:57 +0530 at start, 22:10 +0530 at close. Well inside the 23:59 +0530 fail-safe.

Read `logs/cycle-7.md` first, then the issue's criteria fresh from GitHub. A
productive cycle with the write mechanism finally working: six new criteria proven,
one real bug caught and fixed along the way.

## AC 6 — headless run, found a real bug, fixed it

`check_heartbeat_ac6_ac7_scripted_agent.py`, scenario (a): a genuinely quiet window,
nothing failing, nothing time-bound, no outside message, nothing capture-worthy.
**First run failed**: the beat produced a 246-character status narrative ("nothing
observed that clears the bar for memory, no correction, quiet-beat count at 1...")
— a real violation of "the beat runs and reports nothing," not a heuristic false
positive. `SKILL.md`'s Output section stated the rule but gave no concrete guidance
on what a quiet beat's *actual* final text should look like, so the model defaulted
to narrating its own checklist. Fixed: added one paragraph making explicit that
silence means the response itself is minimal, not a status report. Re-ran: 55
characters, "Heartbeat complete — quiet window, nothing to record." **AC 6: MET.**

## AC 7 — headless run

Scenario (b): same window, prompt WITHOUT the `requested by cron` marker. The beat
ran (didn't refuse) and said "Manual invocation (no cron marker)" explicitly, per
`SKILL.md`'s invocation-source-check text. **AC 7: MET.**

## AC 14 + AC 15 — headless run, the first fully realistic test of the write path

`check_heartbeat_ac14_ac15_scripted_agent.py`: seeded a surface-map holder already
at the 25-entry cap (25 distinct episodic memories, staggered dates 2026-08-01
through 2026-08-25, none described as closed), then a window with one new,
unrelated, dated, open item. Nothing in the window closes any of the 25, so the
only way back to 25 after adding the new one is the cap-eviction rule, not the
closure exit-walk — isolates AC 14 cleanly from AC 5/12's mechanism.

**Verified against the store**: the holder holds exactly 25 ids afterward, and the
oldest entry (2026-08-01) specifically is the one gone — not an arbitrary one. The
beat's own output ("Write verified, read back by tag: the map holds 25 ids") matches
the real count. **AC 14 and AC 15: MET.**

## AC 10 + AC 11 — headless run

`check_heartbeat_ac10_ac11_scripted_agent.py`: one window carrying both a
correction ("I said X, that's wrong, it's actually Y") and a commitment ("we'll
revisit Z next sprint"). Verified against the store: two `procedural`-typed
memories — one the bare rule ("write failures get exactly one attempt, then the
beat stops"), one the instance with the specific detail — related to each other,
matching goal.md's "instance node with the detail, a bare rule node" shape exactly.
One `episodic`-typed memory for the commitment, zero `working`-typed memories.
**AC 10 and AC 11: MET.**

## Regression check

`check_shapes.py` 5/5 · `check_hooks.py` 15/15 · `check_session_start.py` 2/2 ·
`check_verify_memory.py` 12/12 · `check_heartbeat.py` 3/3 — all pass throughout,
including after the `SKILL.md` Output-section fix.

## Criteria met, out of 20

Carried: AC 1, 2, 3, 5, 8, 9, 12, 13, 16, 19. **New this cycle: AC 6, 7, 10, 11, 14,
15.**

**16/20.** Remaining: AC 4, AC 17, AC 18, AC 20.

## What moved

10 → 16, the largest single-cycle jump in this story. Two things made this
possible: AC 5/12's fix landing for real last cycle unblocked AC 14/15 (which need
a working write path to test at all), and AC 6's headless run caught a genuine gap
in `SKILL.md`'s own instructions rather than just confirming existing text —
exactly the kind of finding this methodology exists to surface.

## Assumptions changed

`SKILL.md`'s Output section gained one paragraph making "reports nothing" concrete
rather than aspirational — a quiet beat's response must itself be minimal, not
merely unremarkable.

## Next

`action.md` rewritten for cycle 9: the four remaining criteria. AC 4 and AC 17
share the same difficulty (no real "previous beat" boundary exists in a single-shot
scripted run) — worth solving once. AC 18's "not active" branch is provable now
(curiosity doesn't exist yet, issue #6); the "active" branch isn't. AC 20 (no
double-run) is structural/architectural, not really scripted-agent-testable — worth
deciding whether `SKILL.md`'s existing reasoning is sufficient as stated or needs a
different kind of check.

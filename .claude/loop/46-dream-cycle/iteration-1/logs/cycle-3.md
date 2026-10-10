# Cycle 3 — 2026-10-10 16:5x +0530

Branch: `feature/46-dream-cycle` (read from git). Issue #46 open, 11 ACs read first.

## Result

**Criteria met: 8 / 11.** Moved 4 → 8.

| bucket | ACs |
|---|---|
| met | 1, 2, 3, 5, 6, 7, 8, 11 |
| pending | 4, 9, 10 |
| UI-pending | none |

What moved it: the heartbeat now has a `dream-cycle` section, paired by id, in `observe.md`
and `goal.md`, beside `quiet-cycles`. It states: the gate is `dream_cycle.should_run`; off
means never (AC 5); one cycle per beat at the stored batch size; never both curiosity and
the dream cycle in the same beat, `quiet-cycles` first (AC 7); never while the owner has
messaged in the last 10 minutes (AC 8); the section is named next to curiosity (AC 6).

Why 4 is still pending: the section says to run `/dream-cycle`, and that skill does not
exist yet, so a quiet beat cannot yet run a batch. 9 and 10 need the skill and a scratch
store.

## Built

- `src/.claude/skills/heartbeat/observe.md` and `goal.md`: the `dream-cycle` section.
  No other section touched.
- `checks/dream-cycle/check_dream_cycle.py`: 23 checks, 23 pass. Added structural checks
  for AC 4c, 5c, 8b, and AC 7b made whitespace-tolerant (the sentence wraps across a line;
  the wording was right, the pattern was wrong).

## Regression line

`check_heartbeat.py` 3/3 (ids still pair, 6 sections each side), `check_curiosity.py` 7/7.
No regression.

## Still owed

- The skill `/dream-cycle` and its scratch-store proof (AC 4, 9, 10).
- The mutation pass: each check shown to fail when its behaviour is removed.
- Owner interface: the on/off/size/status commands. AC 1-3 are met at the module level; the
  owner-facing command lives in the skill.

## For Kaushik

- The check for AC 8 proves the heartbeat text and the gate input. The "10 minutes since
  the owner's last message" is judged by the beat from the session, as `/dream` does; it
  has no mechanical clock, so it is only as reliable as the beat's reading of the window.

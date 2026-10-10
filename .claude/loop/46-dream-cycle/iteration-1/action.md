# Action — cycle 3

Constraint from cycle 2: 4/11. The gate exists but the heartbeat does not use it, and no
skill runs a cycle (AC 4-8 owner-facing, 9, 10 pending).

1. Read `gh issue view 46` (criteria) first.
2. Heartbeat wiring: add a `dream-cycle` section (same `id`) to `heartbeat/observe.md` and
   `heartbeat/goal.md`, placed beside `quiet-cycles`. Goal text must say: runs only when
   `dream_cycle.should_run` is true; one cycle per beat; never both curiosity and the dream
   cycle in the same beat (the exact phrase `never both in the same beat`); never while the
   owner is in conversation; off means never. Keep the goal's "one goal per section" rule.
   Do not touch other sections. Re-run `check_heartbeat.py` (id pairing must still pass).
3. Run `check_dream_cycle.py`: AC 6a, 6b, 7b go green.
4. If time remains in the cycle, start the `dream-cycle` skill (SKILL.md: how one batch is
   applied through `/update-memory` and `/delete-memory`, protected ids skipped and
   reported, log entry per cycle). Otherwise leave it for cycle 4.
5. Record criteria met out of 11, commit and push, report on crosschat.

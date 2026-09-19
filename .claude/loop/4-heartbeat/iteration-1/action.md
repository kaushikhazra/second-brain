# Action

**Cycle 1. Baseline, then the three files, then the pairing check.**

Record the baseline in `logs/cycle-1.md` before writing anything: the branch; the current
heartbeat's line count and its direct memory calls (there are none after #2's reroute, but
the file still describes a sub-agent and a prose surface map); `check_shapes.py`,
`check_hooks.py`, `check_session_start.py` results; `memory_guard.py`'s exemption logic in
two sentences, so the map-write path is understood before it is written.

Then, in this order:

1. **`observe.md`** — four sections with ids `capture`, `correction`, `quiet-cycles`,
   `surface-map`, each stating what a beat watches for, generalised from Velasari's.
   The `surface-map` section carries the two triggers: something happened and is still
   open; and, separately, has something on the list closed, which fires on an empty
   window too.

2. **`goal.md`** — the four matching sections. `capture` routes to `/create-memory` and
   restates none of its rules; it carries the one judgement only the loop can make
   (would a future session be wrong without it) and the `episodic`-not-`working` line
   for commitments. `correction` routes to `/create-memory` with the mechanism-not-event
   rule and the "if caught and fixed inside the window, write nothing unless it
   generalises" judgement. `quiet-cycles` counts three, discounts a window where the
   beat's last turn handed the owner something to do, and fires `/curiosity` only if
   present and active. `surface-map` carries the entry test, the ceiling, the exit walk
   every beat, the content-only write through `/update-memory`, the read-back by tag,
   and the rule that the self map is never written here.

3. **`SKILL.md`** — the loop, short: files table, observe → act, the window, the
   invocation-source check, the silence rule with its three exceptions. Under 60 lines.

4. **`check_heartbeat.py`** under `.claude/skills/heartbeat/`: asserts the three files
   exist (AC 1), the id pairing both ways (AC 2), and the AC 9 grep. Run it. Record.

Do not touch `/update-memory` or `CLAUDE.md` this cycle; the carve-out and the routing
row come with the cycle that proves the map write.

Commit on `feature/4-heartbeat`, push, write `logs/cycle-1.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

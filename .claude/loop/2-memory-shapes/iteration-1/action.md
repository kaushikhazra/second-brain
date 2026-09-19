# Action

**Cycle 4. Build `/update-memory`.**

Cycle 3 landed `/read-memory` and found AC 14 is only literally provable against an
empty store — recorded, not re-litigated here. Two skills remain for AC 2: `update`
and `delete`. `update` first, same order Velasari's source tree uses and the same order
the issue's own criteria groups appear in (Writing → Reading → **Changing** → Removing).

Read the issue's criteria fresh (`gh issue view 2 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-3.md`. Re-read `assumption.md` fresh too — cycle 3
picked up two mid-flight corrections from Velasari that weren't in the file cycle 3
started with; assume the same is possible here.

## 1. Read the source, generalise, land it

`C:/Projects/ai-persona/Velasari/.claude/skills/update-memory/SKILL.md` — same
treatment as cycles 1 and 3. Implements, from the issue:

- AC 16 — refuses an update made for tidiness, says why (this is the shapes file's own
  warning that `memory_update` reinforces stability on every call — a bookkeeping edit
  is not free).
- AC 17 — incomplete → new node + edge; wrong → rewrite in place. This is the shapes
  file's fact-shape tiebreak (`update` vs `archive` vs `delete`, by "was it ever true")
  applied at the skill layer.
- AC 18 — tag changes pass the FULL intended set; nothing dropped without being named.
  **Verified in cycle 2's engine reading: `memory_update`'s `tags` argument replaces
  wholesale.** State this as fact, not caution — the shapes file already carries it.
- **AC 19 — type change via `cm update <id> --type <type>`, not `memory_update`,
  confirmed by reading back.** Already the documented path from cycle 1; this skill is
  where it actually gets invoked. Do not second-guess it again — assumption.md settled
  this after cycle 1.
- AC 20 — every update confirmed by reading the memory back, not by the tool's return
  value (mirrors `create-memory`'s AC 25/AC 7 verification discipline).

## 2. Point at the shapes file, restate nothing (AC 3, now three skills)

## 3. Run `check_shapes.py`, record the real output

AC 2 still expects to fail (one skill left, `delete-memory`) — confirm, don't assume.

## 4. Extend the scratch-store proof, time permitting

New file, `check_update_memory.py`, same scratch-server pattern (fresh port, e.g.
8051 again — confirm nothing is still listening there before reusing it). Provable by
script: AC 18 (store with tags A,B; update passing only tags A,C; read back; confirm B
is gone and C is present — demonstrates the wholesale-replace behaviour the skill must
account for, not that the skill always passes the full set) and AC 19 (type change via
`cm update --type`, read back, confirm landed). AC 16, 17, 20 lean on skill judgment
(when NOT to update, whether something was "wrong" vs "incomplete") — say plainly if
they stay unproved, same discipline as AC 5/8/11/12/13/15/26.

## 5. Commit, push, log, write cycle 5's action.md, exit

Same discipline as prior cycles. `loop.md`'s 15-minute-interval edit already committed
with cycle 3 — nothing pending there for this cycle unless something new changes it.

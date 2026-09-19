# Action

**Cycle 5. Build `/delete-memory` — the last of the four skills.**

Cycle 4 landed `/update-memory` (12/27). This cycle completes AC 2 (all four skills
exist and load) for the first time.

Read the issue's criteria fresh (`gh issue view 2 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-4.md`. Re-read `assumption.md` fresh — check for new
commits on the branch before assuming nothing changed, same as every cycle so far.

## 1. Read the source, generalise, land it

`C:/Projects/ai-persona/Velasari/.claude/skills/delete-memory/SKILL.md`. Same
treatment: no named people, no incident dates (2026-08-29 appears twice in the
source — both drop to mechanism-only). One thing to verify before writing it down
rather than trusting the source, same discipline as every prior skill: **confirmed
already, this cycle's research** — `memory_delete(confirm: bool, id, ids)` in this
synaptra install genuinely requires `confirm=true` and refuses otherwise (`server.py`
line ~337). The source's claim holds; write it as verified fact.

"Bulk removal is Kaushik's call" generalises to "the owner's call" — same as every
other Kaushik-specific line so far.

Implements: AC 21 (archive by default; delete only when never-true or a duplicate, say
which), AC 22 (removing one node of a learning without the rest of its constellation is
refused).

## 2. Point at the shapes file, restate nothing (AC 3, all four skills now)

## 3. Run `check_shapes.py`

**AC 2 should flip to PASS for the first time** — confirm, don't assume; if it doesn't,
find out why before moving on (frontmatter typo, wrong path, etc.) rather than logging
a mismatch between prediction and reality and carrying on regardless.

## 4. `CLAUDE.md` — AC 4, now that all four skills exist

Assumption.md scoped this already: replace the Synaptra section's *Store / Update /
Relate* bullets (the ones that currently tell the assistant to call `memory_store`,
`memory_update`, `memory_relate` directly) with routing to the four skills. **Keep**
the tool list and the DB/install paragraphs — those describe the server, not the
calling convention. This is the same rewrite discipline as the `dream`/`heartbeat`
reroute in cycle 2: change what tells the assistant to call the tool directly, change
nothing else in the section.

## 5. Extend the scratch-store proof, time permitting

`check_delete_memory.py`, same pattern. Provable by script: archive an id, confirm it
leaves the active set (`memory_list(state="active")` no longer includes it) but
`memory_get` still finds it and `memory_restore` brings it back — demonstrates the
archive/restore mechanics the skill's "archive by default" promise depends on. AC 21's
actual judgment (never-true vs duplicate vs outgrown scaffolding) and AC 22 (refusing a
partial constellation removal) are skill-level — say plainly if left unproved, same
discipline as the rest of the unproved list.

## 6. Commit, push, log, write cycle 6's action.md, exit

Same discipline as every prior cycle. Once `check_shapes.py` shows AC 2 passing and
CLAUDE.md's AC 4 rewrite lands, take stock in `logs/cycle-5.md` of what's genuinely
left: AC 5, 8, 11, 12, 13, 15, 16, 17, 20, 21, 22, 24, 26 unproved-or-not-started — the
next cycle's move is likely the `PreToolUse` hook (AC 12/26) or the `session-end`
conformance scan (AC 24), whichever is more tractable; decide with fresh eyes then, not
here.

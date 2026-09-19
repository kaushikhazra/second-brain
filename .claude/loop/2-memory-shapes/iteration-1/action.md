# Action

**Cycle 3. Build `/read-memory`.**

Cycle 2's constraint: the five criteria still stuck on `create-memory` (AC 5, 8, 11, 12,
26) are stuck because they test the **skill's own judgment** — a raw script driving
`cm` directly cannot exercise a prose-driven decision (recall-before-store, refusing a
tag, refusing a short id). Proving those needs a scripted-**agent** session, not a
scripted synaptra session, and is a heavier, different-shaped check than
`check_create_memory.py`. Chasing it further this cycle would be diminishing return;
the bigger and more tractable win right now is AC 2's other three skills and AC 13–22,
which are plain forward construction, same as cycle 1's `create-memory` work.

Read the issue's criteria fresh (`gh issue view 2 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-2.md`.

## 1. Read the source, generalise, land it

`C:/Projects/ai-persona/Velasari/.claude/skills/read-memory/SKILL.md` — same treatment
as cycle 1: strip every named person, incident, date and CM-specific id; keep the
mechanism. Two things in the source will NOT port cleanly — decide, don't default:

- **The "fall back to `/recall-session`" step** (in "when recall comes back empty or
  wrong"). Second brain has no `/recall-session` skill. Do not invent one. Either drop
  the step (say a null result plainly, per AC 14, and stop there) or name what this
  brain actually has for finding something outside synaptra (session transcripts, the
  harness auto-memory) — check `CLAUDE.md`'s Structure table before assuming either
  way.
- **The negative-strength-edge section** ("curiosity lays provisional edges..."). This
  describes a mechanism second-brain's `CLAUDE.md`, `dream` and `heartbeat` never
  mention. Check whether anything in this repo creates such edges before porting a
  section about handling them — if nothing does, leave it out rather than describing a
  feature that doesn't exist here.

Implements, from the issue: AC 13 (pick recall/list/get/related from the question,
name which), AC 14 (null result reported as not-found, never as non-existence), AC 15
(pull the boundary before applying a learning's rule).

## 2. Point at the shapes file, restate nothing (AC 3, once this skill exists too)

Same discipline as `create-memory`.

## 3. Extend `check_shapes.py` — no new script needed

Its AC 2 and AC 3 checks already iterate `MEMORY_SKILLS`; landing
`.claude/skills/read-memory/SKILL.md` with correct frontmatter and a pointer to the
shapes file should flip both checks further toward passing without touching the script
(AC 2 stays failing until all four exist — confirm that's still true, don't assume).
Run it and record the real output, not the predicted one.

## 4. If time remains: a scratch-store proof for AC 13–15

Same scratch-server pattern as cycle 2 (`SYNAPTRA_PORT=8051`, `.claude/shared/memory/`
scripts, never the live store). AC 13 and AC 15 are partly skill-judgment (same
limitation as AC 5/8/11/12/26) — say so rather than forcing a script to claim more than
it tested. AC 14 (null recall on a query that matches nothing → confirm the tool
returns empty, not an error) is fully provable by a raw script. Do only what's real;
leave the rest "implemented but not proved" and say why, same as cycle 2 did for AC 12
and AC 26.

## 5. Commit, push, log, write cycle 4's action.md, exit

Same discipline as cycles 1 and 2: one commit, pushed, `logs/cycle-3.md` written and
left immutable, `action.md` rewritten for cycle 4, one crosschat line to `velasari`
before exit.

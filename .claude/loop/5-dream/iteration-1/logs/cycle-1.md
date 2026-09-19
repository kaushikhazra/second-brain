# Cycle 1

**Branch**: `feature/5-dream` (already checked out, shared working tree; clean at
start). **Clock**: 2026-09-19 22:27 +0530.

## Baseline (before writing anything)

- Current `.claude/skills/dream/SKILL.md`: 266 lines. Direct memory calls by line:
  `memory_archive(id)` in Act 2's table (line 154); `memory_consolidate(dry_run=...)`
  in Act 3 (lines 164, 166 — not itself forbidden, `memory_consolidate` isn't one of
  AC 6's three named tools); `memory_relate(full_id, full_id, rel_type)` and
  `memory_unrelate` in Act 4 (lines 189, 196); Act 5 updates a
  `self-learning-surface-map` prose memory (lines 207–208) — this concept no longer
  exists after #3/#4 (the surface map is now the id-list holder, heartbeat's to
  maintain).
- Full regression line at start: `check_shapes.py` 5/5, `check_hooks.py` 15/15,
  `check_session_start.py` 2/2, `check_verify_memory.py` 12/12, `check_heartbeat.py`
  3/3. Clean going in.
- `cm backup --help` / `cm backup create --help`: unlike `cm get/store/list/update`
  (confirmed HTTP-only in #4, `--url` is their only connection option), `cm backup
  create` has **no `--url` option at all**. Its own help text: "Stops the CM
  service, exports all memory data to a NDJSON artifact, restarts CM, and runs the
  retention pruner" — a description of file-level operation, not an HTTP client.

## 1. The backup question, settled empirically

Per assumption.md's explicit cycle-1 instruction: ran `cm backup create` against a
scratch data directory with `SYNAPTRA_BACKEND`/`SYNAPTRA_DB` set and **no server
running at all**.

**Result: it works, file-level, exactly as the current skill's text already
describes.** Seeded 1 memory via a temporary HTTP server, stopped the server, ran
`cm backup create` with no server — backup completed, reported "1 memories,"
`manifest.json`'s `row_counts.memory` was exactly 1. `cm backup verify --deep`
returned `OK`. The "CM service started but did not respond within 180s" warning
appeared, exactly matching the skill's own documented "benign noise" section — this
machine's synaptra is per-session stdio, not the scheduled-task-based service `cm
backup`'s log lines describe, and the skill already says so.

**Conclusion: the checkpoint text stands as written, no change needed.**

**A further question this raised, tested beyond what assumption.md asked**: since
`cm backup create` operates file-level, does it corrupt or block on a data file a
LIVE session is simultaneously holding open (the concurrent-access hazard this
whole project has been careful about elsewhere)? Tested directly: started a scratch
HTTP server (simulating a live session's connection), seeded 2 memories, and **ran
`cm backup create` against the same data directory WITHOUT stopping the server**.
It completed successfully, reported the correct count (2), and the "live" server
was confirmed still fully responsive and undamaged afterward (both memories
intact, re-listed correctly). **`cm backup create` is safe to run concurrently
with a live connection to the same store** — a real, previously-unverified safety
property this story's checkpoint step depends on, now confirmed rather than
assumed.

## 2. Protected ids — the AC 8 mechanism

**Record file**: `.claude/.protected-ids.json` (gitignored), written by
`/session-start` after its existing step 3 (boot lists) and step 5 (handoff)
fetches: `{"self_map_holder": ..., "surface_map_holder": ..., "handoff_id": ...,
"written_at": ...}`, all three nullable, rewritten every boot (not single-use like
issue #3's sentinel — this record is read fresh by every guarded call for the rest
of the session).

**`memory_guard.py` extended**:
- `memory_archive` / `memory_delete` on a protected id → blocked.
- `memory_unrelate` where either end is a protected id → blocked.
- `memory_update` on a protected id → blocked, **except** a content-only update
  (no `tags` key) to the surface-map holder specifically — the heartbeat's own
  exit-walk write (#4) must keep working; AC 8 protects against a dream reshaping
  the map, not against the mechanism the map exists to support.
- Fails **open** (not closed) when the record file is missing or unreadable — its
  absence means the session hasn't booted through `/session-start` yet, not
  license to skip the two rules already in this hook.
- `.claude/settings.json`'s `PreToolUse` matcher extended to cover
  `memory_archive`, `memory_delete`, `memory_unrelate` (previously only
  `memory_store`/`memory_update`/`memory_relate`).

**A gap noted, not silently assumed covered**: a retype via the `cm` CLI
(`cm update <id> --type <type>`, the path `/update-memory`'s own text says a type
change actually takes) is a Bash command, not an MCP tool call — this hook only
ever sees MCP tool invocations and cannot inspect or block a Bash command string.
Protecting a protected id from a CLI-based retype is the dream's own prompt
discipline to hold once its acts are rewritten (a later cycle), not something this
mechanism can enforce. Documented in `memory_guard.py`'s own docstring rather than
left implicit.

**`check_hooks.py` extended**: 12 new test cases covering every branch (archive/
delete/unrelate on protected and unprotected ids; update on the self-map holder,
the handoff id, and the surface-map holder both content-only and with tags; no
protected-ids file at all). **27/27 pass, up from 15/15.**

**`/session-start`**: a short new paragraph after step 5 writing the record,
explicit that `null` is the correct value for an absent holder or handoff, not an
error to work around.

## 3. `check_dream.py` — structural checks

New file under `.claude/skills/dream/`. Four checks against the skill's own text:
AC 6 (no call-shaped instruction to a raw tool — prohibition sentences allowed,
same call-vs-mention distinction `check_heartbeat.py`'s AC 9 grep already draws),
AC 14 (no `CronCreate` call whose prompt names `/dream`), AC 7 and AC 15 (the
archive threshold and the active-conversation window stated as explicit numbers).

**Two false positives caught and fixed before trusting the script**: an early
version of AC 14's check flagged ANY `CronCreate` call — including the dream's own
Act 6, which legitimately recreates the HEARTBEAT cron, not a dream-scheduling
call at all. And an early version of AC 7/AC 15 matched on any number near
"retrievability" or "minutes" — which false-matched an unrelated
"retrievability ≈ 0" example in Act 1's inventory description, and the heartbeat's
own unrelated "every 30 minutes" cadence mentioned in the intro. Both tightened to
require the number specifically co-located with the actual rule's own language
(`archiv` + `retrievability` + a decimal for AC 7; `active conversation` + a
minute count for AC 15), then sanity-checked against realistic future skill text
to confirm they'd correctly PASS once that text is actually written.

**Run against the current, unedited skill**: AC 6 fails (`memory_archive`,
`memory_relate` are still direct calls — expected, action.md said not to edit the
acts this cycle). AC 14 passes (nothing currently schedules a dream). AC 7 and
AC 15 fail (neither number exists in the skill yet — expected, both are new text a
later cycle adds). **1/4 this script's own criteria — an honest baseline, not a
forced pass.**

## Regression check

`check_shapes.py` 5/5 · `check_hooks.py` 27/27 · `check_session_start.py` 2/2 ·
`check_verify_memory.py` 12/12 · `check_heartbeat.py` 3/3 — all pass, no
regression on #2, #3 or #4.

## Criteria met, out of 17

- **AC 8** — mechanism, `check_hooks.py`'s 12 new branches. MET.
- **AC 14** — script, `check_dream.py` against the skill's current text (nothing
  schedules a dream). MET.

**2/17.** Everything else either isn't built yet (AC 1–5, 9–13, 16, 17) or is
correctly reported as not-yet-met by `check_dream.py` (AC 6, 7, 15) because the
acts haven't been rewritten — not counted, per this story's own bar.

## What moved

0/17 → 2/17, plus groundwork the rest of the story depends on: the backup
question is genuinely settled (file-level, safe under concurrent access, no
skill-text change needed), and the protected-ids mechanism + its proof exist for
Act rewrites to rely on. A real safety property (concurrent backup access) was
verified rather than assumed, beyond what this cycle strictly needed to answer.

## Assumptions changed

None reversed. Assumption.md's central cycle-1 question (does `cm backup` need a
server) is answered: no, and the answer is now recorded with evidence, not left
open.

## Next

`action.md` rewritten for cycle 2: rewrite the dream's acts — Act 2's archive
becomes `/delete-memory`, Act 4's relate/unrelate become `/create-memory`'s relate
step and a protected-id-aware unrelate, Act 5 drops the `self-learning-surface-map`
update entirely (AC 6). Add the AC 7 threshold and AC 15 window numbers to the
text. Re-run `check_dream.py` and expect all 4 to pass. Then start on AC 1/2's
row-count-gate proof script (observe.md's own instruction: feed the gate a
mismatched manifest, assert abort with the word "defect"; a matching manifest,
assert continue) and AC 16 (an abort leaves the store exactly as it was, proven
against a scratch store by diffing `memory_list` before and after a forced abort).

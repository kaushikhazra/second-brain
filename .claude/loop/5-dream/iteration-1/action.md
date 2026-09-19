# Action

**Cycle 2. Rewrite the dream's acts — AC 6, AC 7, AC 15's text, then start the AC 1/2 row-count-gate proof.**

Read `logs/cycle-1.md` first. Cycle 1 settled the `cm backup` question (file-level,
safe under concurrent access, checkpoint text unchanged), built the protected-ids
mechanism (AC 8, `check_hooks.py` 27/27), and `check_dream.py` (AC 6/7/14/15
structural checks — AC 14 already passes; AC 6, 7, 15 correctly fail against the
current unedited acts). 2/17.

## 1. Rewrite Act 2 — archive goes through `/delete-memory`

Current: `memory_archive(id)` in a table row. Per assumption.md: "Archiving...
[goes] through `/delete-memory`... The dream keeps its thinking; only the calls
move." Change the table's `memory_archive(id)` action to route through
`/delete-memory`, keeping the judgment criteria in the table (resolved
continuation, superseded snapshot, no-longer-load-bearing) exactly as they are —
only the mechanism changes.

**AC 7 in the same pass**: state the archive threshold explicitly — "a memory is
archived only if its retrievability is below 0.2" (assumption.md's stated number,
matching `memory_consolidate`'s own archive line) — AND that it must be on neither
boot list and not the current handoff (AC 8, restated here as the rule Act 2 must
honor, not just what the hook enforces). Use wording `check_dream.py`'s AC 7 regex
will match: the word "archiv", the word "retrievability", and a decimal number like
`0.2`, co-located.

## 2. Rewrite Act 4 — relate/unrelate go through the skills

Current: `memory_relate(full_id, full_id, rel_type)` directly, and a direct
`memory_unrelate` for backwards `part_of` fixes. Per assumption.md: relating goes
through `/create-memory`'s relate step. Change Act 4's step 5 ("Execute — one
`memory_relate`...") to route through `/create-memory`; change step 7's
`memory_unrelate` fix similarly, noting that `memory_guard.py`'s protected-id rule
will refuse either if a protected id is ever named (AC 8's mechanism backstopping
Act 4's own care).

## 3. Rewrite Act 5 — drop the surface-map update entirely

Current: "Update the `self-learning-surface-map` memory with completed
constellations..." — this concept doesn't exist after #3/#4. Delete this line. Act
5 keeps its other half (storing a `semantic` memory capturing what was woven) but
that store must ALSO route through `/create-memory`, not a direct call (re-check
this line isn't already using one; if it says "Store a `semantic` memory" in prose
without naming a raw tool, it may already be fine — confirm, don't assume).

## 4. AC 15 — state the active-conversation window as a number

Per assumption.md: "an owner message in this session within the last 10 minutes."
Add this as an explicit refusal rule — where in the skill this rule lives is a
judgement call (a new short section near "When to dream," or folded into
Prerequisites) — state it once, clearly, with the number `10` and the phrase
"active conversation" together so `check_dream.py`'s AC 15 regex matches.

## 5. Re-run `check_dream.py`

Expect AC 6, AC 7, AC 14, AC 15 all to pass now (AC 14 already did). If any doesn't,
the wording is wrong, not the check — this script's regexes were sanity-tested in
cycle 1 against realistic phrasing; match that shape.

## 6. If time remains: start the AC 1/2 row-count-gate proof

`observe.md`'s own instruction: a script that feeds the checkpoint gate a manifest
whose row count differs from the live count and asserts abort with the word
"defect" in the output, and a matching manifest and asserts continue. The gate
logic itself already exists in the skill's prose (steps 1–6 of "Pre-dream
checkpoint") — this is about proving the LOGIC, which likely means extracting the
comparison into something callable/testable (a small script under
`.claude/skills/dream/`, e.g. `check_gate.py`, that takes a live count and a
manifest row count as arguments and prints "defect" + exits non-zero on mismatch,
exits 0 on match) rather than trying to script-test prose. Judgement call on the
exact shape; say what you built and why.

Never touch the live store — everything scratch under
`C:/Projects/.tmp/second-brain-loop-5/`, including any real `cm backup` runs.

Re-run the full regression line before closing: `check_shapes.py`,
`check_hooks.py`, `check_session_start.py`, `check_verify_memory.py`,
`check_heartbeat.py` — all five must pass.

Commit on `feature/5-dream`, push, write `logs/cycle-2.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

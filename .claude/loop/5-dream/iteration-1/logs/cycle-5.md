# Cycle 5 — converged, 17/17

**Branch**: `feature/5-dream`, clean at start (cron-fired). **Clock**: 2026-09-19
23:15 +0530 at start, 23:31 +0530 at close.

Read `logs/cycle-4.md` first, then the issue's criteria fresh from GitHub —
unchanged. Six criteria remained; all six proven this cycle.

## A deadline and autonomy change arrived mid-cycle

Kaushik's instruction, relayed by velasari: this session runs overnight until all
stories close, neither session ends. Two changes: (1) #5's fail-safe moves from
02:00 to 06:00 +0530 — found already edited, uncommitted, directly on disk in the
shared working tree (`git diff` showed it before I touched anything), matching
exactly what the message described; committed as part of this cycle rather than
re-deriving the edit myself. (2) When #5 closes, don't wait on a reply — post the
closing comment, push, report, and stay on the branch; velasari merges when she
sees it.

## AC 4 — headless run, plus a recurring bug caught again

Checked `cm backup restore --help` for the actual command first. Added the
rollback command explicitly to checkpoint step 7's told-to-the-owner message
(previously only path + count). Extended the match scenario in
`check_dream_gate_scripted_agent.py` to assert all three. **First run FAILED on
the AC 1/2 half of the same scenario** — the exact same negation bug as cycle 2
("no abort, no defect language" read as a positive report), recurring because
this run's fallback path (no explicit `Decision:` line this time) still used the
old naive whole-text scan. **Generalized the fix properly this time**: replaced
the ad-hoc per-scenario negation exclusions with one shared
`mentions_affirmatively()` helper (word present, not immediately preceded by
"no"/"not"/"isn't"/"neither"), applied uniformly across all three gate scenarios,
removing the now-redundant `extract_decision` entirely. Re-ran all three
(mismatch, match, non-zero-exit) — all pass cleanly. **AC 4: MET.**

## AC 10 — scratch store, real tool access

`check_dream_ac10_scripted_agent.py`: seeded one active and one archived memory,
prompted Act 4's relate step to weave them. The model correctly refused — it
looked both ids up, found one archived, and named AC 10's own rule as the reason
for skipping the link. **Verified against the store**: `memory_related` on the
active id shows no edge to the archived one. **AC 10: MET.**

## AC 11 + AC 12 — real gaps found, closed, then proven together

Checked first: the skill had **no explicit reporting requirement** for either —
not a proof gap, an actual missing rule, same shape as AC 17's gap last cycle.
Added two new bullets to Act 5: report all four counts (active, archived,
retyped, relations added) before and after; report every blocked change by id
with its reason. `check_dream_ac11_ac12_scripted_agent.py`: gave the model
Acts 1-4's established outcomes (3 archived, 2 retyped, 5 relations added, one
relation skipped for an inactive target, one archive blocked by a protected id)
and asked it to perform Act 5's reporting. **Result**: all four counts stated
correctly (52 active, 3, 2, 5), both blocked changes named by their exact id with
the specific reason. **AC 11 and AC 12: MET.**

## AC 5 + AC 13 — real tool-call trace, not the transcript

The hardest remaining proof, flagged as such in cycle 4's plan. Checked first: no
"confirm" language existed for either the delete or the recreate — added a
`CronList` confirmation step to both Prerequisites step 1 and Act 6. **Crons are
strictly session-scoped** (gone when a session exits, never written to disk) —
this makes checking "is the cron running again" from OUTSIDE a finished scripted
session meaningless; the cron would be gone regardless of correctness. Built
`check_dream_ac5_ac13_scripted_agent.py` around `--output-format stream-json`
instead: one ephemeral session first simulates `/session-start` creating a
heartbeat cron, then runs the dream's Prerequisites + Act 6 exactly as written.
Parsed the actual tool-call sequence from the stream, not the model's prose.
**Result, exact expected order**: `CronCreate` (simulated boot), `CronList`,
`CronDelete`, `CronList` (confirms the delete), `CronCreate`, `CronList`
(confirms the recreate). **AC 5 and AC 13: MET.**

## Regression check

`check_shapes.py` 5/5 · `check_hooks.py` 27/27 · `check_session_start.py` 2/2 ·
`check_verify_memory.py` 12/12 · `check_heartbeat.py` 3/3 · `check_dream.py` 5/5 —
all pass.

## Final tally: 17/17

Every acceptance criterion in issue #5 holds, each demonstrated by mechanism,
script, or a headless run verified against the actual store, filesystem, or tool
trace — never by unverified text alone. Three real gaps in the skill's own text
were found by the proof attempts themselves (AC 4's missing rollback command, and
AC 11/12's missing reporting requirements, joining AC 17's missing unreachable
text from cycle 4) — closed before being tested, not assumed present.

## What moved

11/17 → 17/17. The recurring negation bug (this is its third appearance across
cycles 2, 4-attempt-1, and now generalized) taught something worth keeping: a
narrow per-scenario fix doesn't survive a new scenario with a different sentence
shape; a shared, principled helper does. The AC 5/13 proof required recognizing
that the obvious verification approach (check state after the session ends)
doesn't work for session-scoped resources, and building the right kind of proof
instead of a weaker substitute.

## The story in outline (5 cycles)

- **Cycle 1**: settled whether `cm backup` needs a live server (it doesn't — file
  level, and safe under concurrent access, confirmed beyond what was asked).
  Built AC 8's protected-ids mechanism.
- **Cycle 2**: rewrote Acts 2, 4, 5 to route through the memory skills. A headless
  run for AC 1/2 found the skill's abort language never actually said "defect" —
  fixed. The same run's own check script gave two false fails from naive keyword
  scanning — first fix.
- **Cycle 3**: applied velasari's ruling on Act 4 (relate/unrelate stay direct,
  settled) and narrowed a check to test exactly its criterion, no more.
- **Cycle 4**: AC 3, 9, 16, 17. AC 9 needed no new proof — an earlier one already
  covered it by construction. AC 17 had no skill text at all before this cycle.
- **Cycle 5**: the last six. The negation bug recurred and was fixed for good
  this time. AC 5/13 needed a fundamentally different proof shape once
  session-scoped crons made the obvious approach impossible.

## Closing this loop

Per `loop.md`'s converged path, and per Kaushik's explicit instruction not to
wait: delete the cron, comment on issue #5 with the final numbers, push, tell
velasari, stay on the branch. No PR opened or merged — that stays with
Kaushik/velasari, as every prior story in this project has done.

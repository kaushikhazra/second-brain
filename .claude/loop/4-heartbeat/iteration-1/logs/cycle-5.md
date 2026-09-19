# Cycle 5

**Branch**: `feature/4-heartbeat`, clean at start (cron-fired). **Clock**: 2026-09-19
21:26 +0530 at start, 21:37 +0530 at close. Well inside the 23:59 +0530 fail-safe.

Read `logs/cycle-4.md` first, then the issue's criteria fresh from GitHub — AC 5 and
AC 12 unchanged. Cycle 4's lesson carried forward explicitly: every store-check this
cycle is a raw `cm get` read by eye, checking `updated_at` against `created_at`, not
a convenience script's PASS/FAIL alone — even though the `do_verify()` nesting bug is
now fixed in all three scripts.

## Mitigation 1 — the two-step write, tried and ruled out

`goal.md` updated with the two-step instruction from cycle 4's action.md: on an
empty-content write, first set content to a single space (a normal, non-degenerate
value), confirm it landed, then a second call to the true empty string.

Ran fresh against a new seed, stream-json captured. **The single-space step landed
cleanly** — confirms non-empty content is never the problem. **The follow-up
empty-string call failed the identical way**, malformed JSON, same as every prior
attempt. The beat correctly did not leave the holder on the intermediate space —
reverted to its last valid state (still listing the closed entry) and reported the
blocker plainly, also separately capturing the resolution as an ordinary memory so
the information wasn't lost even though the map couldn't be cleared. Good behavior
under a real constraint; the constraint itself did not move.

**Conclusion: the glitch is specific to generating the empty-string VALUE itself**,
not to an identical retry pattern.

## Mitigation 2 — an unrelated field alongside empty content, tried and ruled out

`goal.md` updated again: if the direct empty-content call fails, try one further
attempt that also passes the holder's current `importance` alongside `content: ""`
— a different payload shape, on the chance the glitch is shape-specific rather than
value-specific.

Ran fresh, stream-json captured. The raw trace shows the model actually retried the
bare empty-content call five times before trying the importance-variant (more
attempts than the letter of the instruction allowed — a real gap between what
`goal.md` says and what the model actually does, noted but not chased further this
cycle) — and the importance-variant **failed the identical way too**:
`{"id": "...", "content": , "importance": 0.7}`, same malformed shape, same error.
The beat's own summary undercounted this as "two attempts" and stopped there,
correctly leaving the holder on its last valid state. **Verified directly against
the store** (not the transcript): `updated_at` still equals `created_at` on the
holder — genuinely never touched, consistent with what the beat reported.

**Conclusion: not a payload-shape issue either.**

## Where this leaves AC 5 / AC 12

Both mitigations action.md queued have now been tried and ruled out with direct
evidence, not assumption. `goal.md` is corrected to say so plainly: this looks like
a Claude Code / MCP tool-call generation quirk specific to producing a literal
empty-string value, not something a skill's prose can route around. The interim
behavior stays conservative — attempt once, and on failure stop cleanly (the
`SKILL.md` Failure section's case) rather than improvising further payload variants
per beat. **AC 5 and AC 12 remain NOT MET** — this is not a resolvable-by-rewording
problem within this story's scope, and is now flagged clearly rather than chased with
a fourth workaround under time pressure.

## AC 13 and AC 16 — reconfirmed

Quick re-checks against their existing scratch data (no rebuild), raw `cm get`
reads: both holders still show `updated_at == created_at` and the exact content
cycle 4 found. Both stand: **AC 13 MET, AC 16 MET.**

## Regression check

`check_shapes.py` 5/5 · `check_hooks.py` 15/15 · `check_session_start.py` 2/2 ·
`check_heartbeat.py` 3/3 — all pass, no regression.

## Criteria met, out of 20

Unchanged from the corrected cycle 4 count: **AC 1, 2, 8, 9, 13, 16, 19 — 7/20.**
AC 5 and AC 12 investigated thoroughly this cycle and confirmed still open, not
newly broken or newly fixed.

## What moved

The number didn't move, but the uncertainty did: two concrete, testable hypotheses
for the AC 5/12 blocker were run to a real conclusion (both ruled out with direct
evidence) rather than left as untested guesses. The story now has a precise, evidenced
description of what's actually wrong (a JSON-generation quirk for empty-string tool
arguments) instead of an assumed-fixed workaround that silently wasn't working.

## Assumptions changed

`goal.md`'s empty-content section again — both cycle 4's "try rephrasing" hope and
this cycle's two specific attempts are now recorded as tried-and-failed, not
untested possibilities, so a future cycle (or a human) doesn't retread the same
ground.

## Next

`action.md` rewritten for cycle 6: AC 5/12 is now flagged to Kaushik/Velasari as
likely needing a fix outside this loop's reach (a harness-level issue, or a
different architectural approach to representing "the list is empty" that avoids
ever needing to write a literal empty string at all — e.g., a sentinel single
character the read side treats as equivalent to empty, if that's an acceptable
change to make to issue #3's established contract, which is not this loop's call to
make unilaterally). Move on to what remains provable without that blocker: AC 3
(a beat never edits observe.md/goal.md — a headless run proposing a change and
confirming the files are untouched and a memory was stored instead), AC 4 (window
reading — verify a beat's `capture` decisions are scoped correctly to what's new
since the last beat, not the whole session), AC 6/AC 7 (silence rule and the
invocation-source marker — both currently text-only, both provable by headless
run), and AC 10/AC 11 (correction handling, commitment typing) if time allows.

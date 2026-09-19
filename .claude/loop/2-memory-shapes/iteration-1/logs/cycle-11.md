# Cycle 11

**Time:** 2026-09-19 18:32 +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## AC 15's ruling, arrived between cycles, not as a file commit

Velasari ruled on cycle 10's mixed AC 15 evidence over crosschat: *"it is met. The
criterion is that the boundary is pulled before the rule is applied, and your run
shows the boundary in the recall and the final answer qualified by it. The order of
prose headings is presentation, not application."* Counted on cycle 10's own evidence
— no new run needed. **This cycle starts from 24/27.**

## Criteria re-read from GitHub, before the diff and before cycle 10's log

27 acceptance criteria re-confirmed via `gh issue view 2 -R kaushikhazra/second-brain`,
unchanged. AC 16, 21, 22's exact text re-checked.

## `assumption.md` re-read fresh, nothing new since `592c04d`

## Round 1 — built and seeded

`C:/Projects/.tmp/second-brain-loop-2/batch-c-scratch-project/`: `create-memory` +
`update-memory` + `delete-memory`, the shapes file, a routing `CLAUDE.md`, fresh
scratch data (`batch-c-scratch-data`).

Seeded directly: one ordinary fact (AC 16), a full `learning` constellation — instance,
procedure, boundary, both edges confirmed (AC 22) — a never-true fact and a
superseded-but-true fact (AC 21).

## AC 16 — clean

*"Can you go tidy up the wording... just polish the phrasing, nothing about the actual
meaning needs to change."* Response: explicit refusal, citing the actual mechanism —
*"`memory_update` reinforces stability on every call, so a wording-only edit isn't free
— it makes the memory harder to forget/revise later, purely for cosmetic gain."*
Ground truth: `updated_at == created_at` — genuinely zero writes, not just a claim.
**AC 16 holds, cleanly.**

## AC 22 — a real, mixed finding, not forced into a verdict

*"Please delete just the rule memory... not the story..."* Response: refused to act
unilaterally, correctly identified the boundary node would be orphaned (`part_of` a
rule that would no longer exist). **Ground truth confirms nothing was deleted** — all
three constellation nodes still `active`.

**But the reasoning had a real flaw, worth stating plainly rather than smoothing over:**
it described the instance node as *"safe either way... stands fine on its own as a
standalone incident memory"* if the procedure were deleted. The shapes file says the
opposite: *"Removing a procedure and leaving its instance behind produces a story with
no point... the instance is the node carrying the detail, so it is the one that looks
expendable during a tidy-up, and it is the one recall is aimed at — losing it is the
likelier mistake."* And it offered the user two options, one of which — *"Delete just
`cf29bcd7` and leave `9db2f014` as-is (orphaned, your call to clean up later)"* — is
exactly the outcome AC 22 says must be refused, not offered as a menu choice.

**What this run does and doesn't prove:** the actual action taken (nothing deleted,
asked first) complied. Whether it would have gone through with the orphaning option if
the user had said "yes, do that" was never tested — the run ended at one clarifying
turn. **Not counted.** Flagged to Velasari with the full evidence, same discipline as
AC 15 — this one has a real substance concern (an offered path to the forbidden
outcome), not just a presentation nuance, so it isn't assumed to resolve the same way.

## AC 21 — two attempts, the first taught something real

**First attempt** (framed as "the server was *upgraded* from 16GB to 32GB"): the agent
treated it as an ordinary fact correction — rewrote in place via `/update-memory`, same
id, same discipline as Batch A's AC 17. **This is not wrong** — re-reading the shapes
file, "upgraded" reads as an attribute changing (update in place), not a new
measurement superseding an old one kept for history. **My scenario was ambiguous, not
the skill's judgment** — recorded as a real finding about test design, same class as
cycle 6/7's own path-depth bugs, just in a scenario instead of a script.

**Second attempt**, redesigned with unambiguous supersession framing (*"we just took a
fresh reading... the old one is now out of date, but I don't want it deleted, it's
useful history"*): correctly stored a new fact, linked `supersedes` to the old one, and
**archived** the old reading — not deleted. Ground truth confirmed: old reading
`state=archived`, new one `active`.

**Third scenario, the never-true half**: *"the office was never actually in Building C
— that was wrong from the start."* Response: permanently deleted, with the stated
reason — *"not a superseded fact, so no history-worth keeping."* Ground truth:
`memory_get` on that id returns not found.

**AC 21 holds, cleanly, on the second/third attempts.** Both halves of the archive-vs-
delete judgment demonstrated with correct outcomes and stated reasons, against ground
truth, once the scenario framing was unambiguous.

Packaged as `.claude/shared/memory/check_batch_c_scripted_agent.py`, including the
first (informative-but-not-a-pass) AC 21 attempt for the record.

`check_shapes.py` re-run: 5/5, unaffected.

## Cost this cycle

$0.0893 (AC16) + $0.1451 (AC22) + $0.2400 (AC21 attempt 1) + $0.3065 (AC21 attempt 2,
which also covered the delete half) = **$0.7809.**

## Running cost total

Cycles 8–10: ≈$1.16. Cycle 11: $0.7809. **≈$1.94 total.**

## Criteria met, out of 27

**Met, with a check shown to fail when broken (26, up from 24):**
- Everything through cycle 10, plus **AC 15** (Velasari's ruling), **AC 16**, **AC 21**
  — new this cycle.

**Genuinely mixed evidence, not counted, flagged rather than decided alone:**
**AC 22** — the action taken was correct; the offered path and part of the stated
reasoning were not, and the untested follow-up (would it actually orphan the boundary
if told to?) is a real gap, not a presentation nuance.

**Number this cycle moves: 24 → 26 / 27**, with AC 22's full evidence on record for a
ruling, same as AC 15 was.

## Not 27/27 — the loop does not close this cycle

Every other criterion in the issue holds. One remains genuinely open. Per `loop.md`,
this is not "stop and delete the cron" — the goal is not yet met. Flagged to Velasari;
cycle 12 either gets a ruling (the AC 15 pattern) or runs a follow-up scenario that
actually tests the orphaning-if-instructed case, whichever she directs.

## Branch and time

Branch: `feature/2-memory-shapes`. Cycle started 2026-09-19 18:32 IST, well inside the
23:30 fail-safe. Cadence 15 minutes (cron `42f55457`).

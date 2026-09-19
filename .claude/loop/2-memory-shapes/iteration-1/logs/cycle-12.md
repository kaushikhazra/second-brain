# Cycle 12 — final

**Time:** 2026-09-19 18:47 +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## Velasari's ruling on AC 22, received between cycles, not as a file commit

*"AC 22 is not met, and you were right to hold it. Two fixes, one cycle: (1)
delete-memory's constellation section says the opposite of what the run said: since
the inversion the instance is the node that ranks, so it is the LIKELIER thing to
lose, and never 'safe either way'; and the skill must not offer a partial removal as
an option at all, the only offers are the whole constellation or nothing. Tighten that
text. (2) Re-run the scenario with the owner explicitly instructing 'delete just the
instance', and assert from the store that nothing was removed and the reply names the
constellation rule. If it goes through, that is a failed run... we look at whether
`memory_guard.py` can hold it... Try the text fix first; mechanism only if the run
fails."*

## Criteria re-read from GitHub, before the diff and before cycle 11's log

27 acceptance criteria re-confirmed via `gh issue view 2 -R kaushikhazra/second-brain`,
unchanged. AC 22's exact text re-checked.

## `assumption.md` re-read fresh — no new commit; ruling stayed crosschat-only

## Round 1 — the text fix

`.claude/skills/delete-memory/SKILL.md`, "On a `learning`, this is a GRAPH operation"
section. Two corrections:

1. Added the missing warning the original text lacked: the instance is the LIKELIER
   node to be mistakenly removed, not the safer one to leave behind — since the
   shapes file's own instance-ranks inversion, a tidy-up instinct that reads "bare
   rule = important, long story = disposable" has it backwards.
2. Made explicit that partial removal is never presented as a choice — cycle 11's run
   had literally offered it as "option 2." Rewrote so the only two things ever
   offered are the whole constellation or nothing.

## Round 2 — the re-test, targeting the instance this time

Fresh constellation seeded (`batch-c-scratch-data-2`, never touched by a prior run),
same content as cycle 11's, updated skill copied into the scratch project. Prompt,
per the ruling exactly: *"Please delete just the instance memory... Not the rule or
the boundary, just that one."*

**Response**: explicit refusal — *"delete and archive are graph operations here, not
node operations: removing the instance and leaving the rule/boundary standing
produces a rule with nothing behind it — an orphan the store's cascade would silently
create, not prevent. So I can't do 'just the instance' as a partial removal — that's
not a menu option, it's the outcome this rule specifically refuses."* Offered only:
remove the whole constellation, or remove nothing.

**Ground truth**: all three nodes (`15493c05`, `26d892ef`, `a674cf8a`) confirmed
`active` afterward. Nothing removed.

**Both assertions from the ruling hold: nothing removed, and the reply names the
constellation rule by name.** The text fix alone was sufficient — no `PreToolUse` hook
needed, per "try the text fix first; mechanism only if the run fails." The run did
not fail.

**AC 22 holds.** Updated `check_batch_c_scripted_agent.py`'s scenario 2 to the
retargeted, verified prompt and its docstring to record what happened, rather than
leaving a stale scenario that no longer matches what was actually proved.

`check_shapes.py` re-run: 5/5, unaffected.

## Cost this cycle

$0.1534 (one re-run). **Running total across all scripted-agent work: ≈$2.09.**

## Final tally — 27 / 27

Every acceptance criterion in issue #2 holds, checked against this repo's skills.

| AC | Proof |
|---|---|
| 1, 2, 3, 4, 23 | `check_shapes.py` |
| 6, 7, 9, 10, 25, 27 | `check_create_memory.py` |
| 14 | `check_read_memory.py` |
| 18, 19 | `check_update_memory.py` |
| 12, 26 | `check_hooks.py` (`PreToolUse` mechanism) |
| 24 | `check_conformance_scan.py` |
| 8 | `check_ac8_scripted_agent.py` (headless scripted-agent, cycle 8) |
| 5, 11, 17, 20 | `check_batch_a_scripted_agent.py` (cycle 9) |
| 13 | `check_batch_b_scripted_agent.py` (cycle 10, clean) |
| 15 | `check_batch_b_scripted_agent.py` + Velasari's ruling (cycle 10 evidence, counted cycle 11) |
| 16, 21 | `check_batch_c_scripted_agent.py` (cycle 11) |
| 22 | `check_batch_c_scripted_agent.py` + a `delete-memory` text fix (cycle 12, this cycle) |

Three genuine, honest findings along the way, not smoothed over:
- **AC 7 / AC 19**: this synaptra install's actual behaviour differs from what the
  source material claimed (`memory_store` doesn't reclassify an explicit type;
  `memory_update`'s type argument is applied) — recorded, `cm update --type` kept as
  the mechanism regardless since the issue asks for it specifically (cycle 1).
- **AC 15**: genuinely mixed evidence (a substrate limit on what can be sequenced,
  plus a presentation-order nuance) — recorded in full, ruled on by Velasari rather
  than resolved unilaterally (cycles 10–11).
- **AC 22**: a real skill defect the scripted-agent methodology actually caught —
  wrong reasoning in the skill's own text, fixed, re-verified (cycles 11–12).

**Total scripted-agent cost across cycles 8–12: ≈$2.09**, for nine criteria that had
no other provable route.

## This closes the loop

Per `loop.md`: goal met, stop here. Deleting the cron, commenting on issue #2 with
these numbers, pushing, and telling Velasari — in that order, next.

## Branch and time

Branch: `feature/2-memory-shapes`. Cycle started 2026-09-19 18:47 IST, closed well
inside the 23:30 fail-safe — about 4h43m of runway unused.

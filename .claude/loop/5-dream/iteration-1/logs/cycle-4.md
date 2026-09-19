# Cycle 4

**Branch**: `feature/5-dream`, clean at start (cron-fired). **Clock**: 2026-09-19
23:01 +0530 at start, 23:10 +0530 at close. Well inside the 2026-09-20 02:00 +0530
fail-safe.

Read `logs/cycle-3.md` first, then the issue's criteria fresh from GitHub —
unchanged. Four criteria targeted, all four proven.

## AC 3 — headless run

Extended `check_dream_gate_scripted_agent.py` with a third scenario: `cm backup
verify --deep` exits non-zero with a fabricated error string. Reused cycle 2's
`extract_decision` anchoring technique rather than a naive keyword scan.
**Result: aborts, and reports the exact error text verbatim** (checked as an exact
substring match, not a paraphrase). **AC 3: MET.**

## AC 9 — mechanism, not a new proof

Checked `/update-memory`'s own text before building anything: it already states,
unconditionally for any update, "a type change goes through `cm update <id>
--type <type>`" and separately "read it back and confirm the change is actually
there" — no carve-out excluding type changes from the read-back requirement. Since
Act 2 already routes retyping through `/update-memory` (proven by AC 6's own
grep), AC 9 was already satisfied by construction — building a redundant
scripted-agent test would have proven nothing AC 6 + `/update-memory`'s existing
contract didn't already guarantee. Made it mechanically checkable instead of just
asserted: added two regex checks to `check_dream.py` reading `/update-memory`'s
own file directly, so either half regressing independently (the CLI-retype
instruction or the read-back requirement) would be caught. **AC 9: MET, by
mechanism.**

## AC 16 — scratch-store proof, real tool access

`check_dream_ac16_scripted_agent.py`: unlike AC 1/2/3 (no synaptra connection at
all — pure judgement proofs), this scenario gives the model REAL tool access to a
seeded scratch store, so it could theoretically touch it. Dumped the store,
forced the same row-count-mismatch abort, gave it three real memory ids to work
with. **Verified against the store, not the transcript**: before and after dumps
are byte-for-byte identical (3 memories, unchanged). The transcript's own claim
("nothing was touched") matched what the store actually shows — corroborated, not
just trusted. **AC 16: MET.**

## AC 17 — a real gap found and closed before testing it

Checked first: the skill had **no text at all** for "synaptra unreachable" before
this cycle — not a proof gap, an actual missing rule. Added one sentence to
checkpoint step 1: "If this call errors as unreachable, say so once and stop — do
not proceed to step 2." `check_shapes.py` and `check_dream.py` re-run clean after
the addition (no AC 23 regression this time). `check_dream_ac17_scripted_agent.py`:
same broken-`.mcp.json` technique as issue #3's AC 18 and issue #4's cycle 2.
**Two-part verification**: the transcript says unreachable (weaker signal,
checked but not trusted alone) AND — the real proof — the scratch backups
directory has zero entries afterward, meaning `cm backup create` never actually
ran regardless of what the transcript claims. Both true. **AC 17: MET.**

## Regression check

`check_shapes.py` 5/5 · `check_hooks.py` 27/27 · `check_session_start.py` 2/2 ·
`check_verify_memory.py` 12/12 · `check_heartbeat.py` 3/3 · `check_dream.py` 5/5
(AC 9 added) — all pass.

## Criteria met, out of 17

Carried: AC 1, 2, 6, 7, 8, 14, 15. New this cycle: **AC 3, AC 9, AC 16, AC 17.**

**11/17.**

## What moved

7/17 → 11/17. Two different proof shapes this cycle, matched to what each
criterion actually needed: AC 9 needed nothing new built at all (recognizing that
and checking it mechanically instead of duplicating a redundant test is itself
the discipline this story's bar asks for); AC 17 needed a real skill-text gap
closed before it could be tested honestly, found by checking rather than
assuming the text already existed.

## Assumptions changed

None reversed. AC 9's resolution (mechanism, not a new scripted-agent proof) is
new information worth carrying forward: not every criterion needs its own test
script when an earlier one's proof already covers it by construction.

## Next

`action.md` rewritten for cycle 5: AC 4, AC 5, AC 10, AC 11, AC 12, AC 13 — the
remaining six criteria. A near-miss caught while writing this log: AC 10 ("a
relation is added only between memories that both exist and are both active")
has text in Act 4 since cycle 2 but no proof of its own — checked directly
(`grep`'d every check script in this story for "AC 10," found nothing) before
listing it as remaining rather than assuming cycle 2's Act 4 work already covered
it.

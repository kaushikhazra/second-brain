# Action

**Cycle 7. AC 24 — the session-end conformance scan.**

Cycle 6 finished the last mechanism-backed pair (AC 12, AC 26 via the hook). What
remains splits into skill-judgment criteria with no designed proof route yet (AC 5, 11,
13, 15–17, 20–22 — leave these alone; `assumption.md` never promised a mechanism for
them and inventing one isn't this cycle's job) and AC 24, which — unlike those — is
concrete: `CLAUDE.md`'s own loop-engineering section already names
`session-end/verify_memory.py` as "the seed" for this kind of check, and `session-end`
currently has no such script.

Read the issue's criteria fresh (`gh issue view 2 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-6.md`. Re-read `assumption.md` fresh.

## 1. Solve the actual design question first: how does a SCAN see a violation?

AC 24's text: "A direct store made outside the four skills is found by the session-end
conformance scan and reported by id." The hook (cycle 6) prevents a *future* one; this
scan is about *detecting* one that happened — different job, and it can only work from
what's actually recorded on a memory, since synaptra doesn't tag a memory with "which
skill wrote this."

Investigate before designing: what does `/create-memory` actually pass as `source` on
every store (check the skill and cycle 2's `check_create_memory.py` runs for the
convention already in use)? If `/create-memory` has a consistent, identifiable
`source` marker and an ad-hoc direct call would plausibly NOT set it the same way, the
scan is: list recent active memories, flag any whose `source` doesn't match the known
marker, report by id. **If no such reliable signal exists, say so plainly** rather than
building a scan that can't actually distinguish a compliant store from a violation —
same discipline as AC 12/26 before the hook existed: a check that can't really test the
thing is worse than an honest "not provable this way yet."

## 2. Write `.claude/skills/session-end/verify_memory.py`

Stdlib + the venv's synaptra client (talking to the **live** store this time — this is
the one script in this story that's supposed to run against `.claude/synaptra-data`,
because its whole job is auditing what's actually there; still never write anything to
it, read-only). Scans memories from some recent window, reports any that look like a
direct-call violation by id, per whatever signal step 1 finds.

## 3. Wire it into `/session-end`'s own SKILL.md

`session-end` currently doesn't name any memory tool directly (confirmed cycle 6 — its
prose is high-level, "store the day's learnings," no literal `memory_store` string, so
AC 23's grep doesn't even see it). Add a step that runs the scan and surfaces its
findings, without inventing new session-end mechanics beyond that one step — this
loop's scope is issue #2, not a session-end rewrite.

## 4. Prove it with a script

`.claude/shared/memory/check_conformance_scan.py` (or extend `check_shapes.py` if it
fits the existing pattern better) — store one memory the "compliant" way (matching
whatever marker step 1 settled on) and one the "violation" way, against a **scratch**
store, run the scan against it, confirm it flags only the second by id. Never the live
store for this proof, even though the scan itself targets the live store in production.

## 5. Commit, push, log, write cycle 8's action.md, exit

If this lands and proves out, the number moves to 17/27 — the last one with a
plausible mechanism. What's left after this cycle is genuinely just the skill-judgment
list with no assigned route; say that plainly in `logs/cycle-7.md` rather than
inventing new mechanism-hunting busywork, and let a future cycle (or Velasari) decide
whether any of them get a scripted-agent pass like AC 8's planned one.

# Cycle 2

**Branch**: `feature/5-dream`, clean at start (cron-fired, not by hand). **Clock**:
2026-09-19 22:45 +0530 at start, 22:57 +0530 at close. Well inside the
2026-09-20 02:00 +0530 fail-safe.

Read `logs/cycle-1.md` first, then the issue's criteria fresh from GitHub —
unchanged.

## Act rewrites

**Act 2**: `memory_archive(id)` → `/delete-memory`. Added the AC 7 threshold as an
explicit rule, not just a hook backstop: retrievability below **0.2**, on neither
boot list, not the current handoff — stated as the condition Act 2 itself must
honor, before `memory_guard.py`'s protected-ids rule would ever need to refuse a
mistake.

**Act 4**: kept `memory_relate`/`memory_unrelate` as direct calls, held to
`/create-memory`'s own documented discipline (full uuids, closed `rel_type`
vocabulary) — **not** routed through invoking `/create-memory` as a skill call.
Checked this carefully rather than assuming: read `/create-memory`'s full text,
and its "Link it" step (step 6) only relates a memory it JUST created to others —
there is no standalone "relate two pre-existing memories" mode, and building one
would mean editing one of the four memory skills, which is out of this story's
declared scope. AC 6's own enforcement sentence supports this reading too — it
names `memory_archive`, `memory_update`, `memory_store` as the three forbidden
direct calls, not `memory_relate`/`memory_unrelate`. Added the AC 10 check
explicitly: `memory_get` both ids and confirm `state: active` before relating,
rather than trusting an id from an earlier step is still good.

**Act 5**: dropped the `self-learning-surface-map` update entirely (the concept
doesn't exist after #3/#4). The semantic-memory store now explicitly routes
through `/create-memory` (it already didn't name a raw tool, but was left
implicit — made explicit for consistency with the rest).

**AC 15**: new section, "Refuses to run during an active conversation" — an owner
message in this session within the last **10 minutes** refuses the dream, checked
before anything else, including the checkpoint.

**A genuine finding while testing AC 1/2 (below), fed back into the text**: the
skill said "ABORT... surface the error" for a row-count mismatch, but never
actually used the word "defect" — AC 2's own exact wording is "reported as a
defect, not a warning." A first headless run correctly aborted but never said
"defect" because the skill never told it to. Fixed: split the old combined step 5
into two — a mismatch is explicitly "a defect, not a warning," and a non-zero
command exit (AC 3) shows the command's own error text verbatim, as its own
separate step.

## `check_dream.py` — narrowed, then fully passing

`FORBIDDEN_CALLS` narrowed from six tools to four (`memory_archive`,
`memory_update`, `memory_store`, `memory_delete`) — removing `memory_relate` and
`memory_unrelate`, matching the Act 4 finding above. AC 15's regex made
whitespace-tolerant (`active\s+conversation` instead of a literal space) after a
false FAIL — the phrase was split across a markdown line-wrap in the skill's own
text (`active\nconversation`), which shouldn't matter and now doesn't. **4/4 pass**
against the rewritten skill.

**A real AC 23 regression, caught and fixed in the same pass**: Act 2's closing
sentence originally said "never a raw `memory_archive` or `memory_update` call" —
the literal substring `memory_update` tripped `check_shapes.py`'s AC 23 check
(issue #2's rule: no skill outside the four memory skills may contain that literal
text). Same class of self-inflicted regression issue #4 hit twice. Reworded to
"never a raw call to either's underlying tool" — no literal substring, same
meaning.

## AC 1 + AC 2 — headless run, with two false fails in the check script itself

`check_dream_gate_scripted_agent.py`: gives the dream skill's own checkpoint text
the two numbers a real checkpoint would already have (live count, backup manifest
count) and asks what it does — no live synaptra connection needed for this
specific judgement, and deliberately skips the ~190s real `cm backup create`
already verified mechanically in cycle 1.

**Mismatch (55 vs 1)**: first run correctly aborted but never said "defect" —
this is what surfaced the skill-text gap above. After the fix: correctly aborts,
explicitly calls it a defect, cites the exact 2026-08-12 incident the skill
documents. **PASS.**

**Match (55 vs 55)**: correctly proceeds — but the check script itself reported
FAIL twice before being fixed. First: a naive `"defect" in text` scan caught the
model's own **negated** mention ("this is not a defect") as if it were a report.
Fixed to exclude negated forms — then failed again the same way for "abort"
("no abort, no defect language" — also negated). **Rebuilt the check around the
model's own explicit `Decision:` statement** rather than scanning the whole reply
for keyword presence, since a correct answer legitimately explains and rules out
the failure modes by name. Re-ran: **PASS**, decision line correctly isolated
in both directions.

## Regression check

`check_shapes.py` 5/5 · `check_hooks.py` 27/27 · `check_session_start.py` 2/2 ·
`check_verify_memory.py` 12/12 · `check_heartbeat.py` 3/3 · `check_dream.py` 4/4 —
all pass.

## Criteria met, out of 17

Carried: AC 8, AC 14. New this cycle: **AC 1, AC 2** (headless run, verified
against the model's own decision statement, not naive keyword presence), **AC 6,
AC 7, AC 15** (script, `check_dream.py` against the skill's own text).

**7/17.**

## What moved

2/17 → 7/17. Two genuine bugs were caught this cycle, not just features added: a
real gap in the skill's own abort wording (no "defect" language, contradicting
AC 2's literal text) found BY the proof attempt, not before it — exactly what a
headless run is for; and a check script that could pass on the wrong evidence
(a negated mention read as a positive report) twice in the same cycle, fixed both
times before trusting its result.

## Assumptions changed

None reversed. Assumption.md's framing of Act 4 ("relate becomes `/create-memory`'s
relate step") is interpreted here as "held to the same discipline `/create-memory`
documents," not "routed through invoking the skill," since the skill has no mode
for relating two pre-existing memories — noted here for velasari to correct if
that reading is wrong.

## Next

`action.md` rewritten for cycle 3: AC 3's own headless run (a non-zero command
exit, not yet proven — only text added); AC 9 (retype via `cm` CLI, read back);
AC 16 (an abort leaves the store exactly as it was — scratch store, seed, force
abort, diff `memory_list` before/after); AC 17 (synaptra unreachable, stops before
any backup). AC 4, 5, 11, 12, 13 (report contents, cron confirm) remain after
that.

# Action

**Cycle 1. Establish the baseline, then land the shapes file and the first skill.**

First, record the baseline in `logs/cycle-1.md` before writing anything: the branch, the
output of the AC 23 grep as it stands today (it will list `dream` and `heartbeat`), the
list of skills present, and `cm --help` from the venv so the CLI's real flags are known.

Then, in this order:

1. **The shapes file.** Read Velasari's `memory-shapes.md` in full. Write
   `.claude/shared/memory/memory-shapes.md` for a second brain: four shapes, the fork,
   the create/read/update/delete sections for each, the synaptra specifics, the reserved
   tag table. Strip every named person, persona and incident. Keep every rule. Where a
   rule was justified by an incident, keep the justification as a mechanism ("a corrected
   fact with an uncorrected copy elsewhere is worse than either alone"), not as a story.

2. **`/create-memory`.** Same treatment. It must: recall first (AC 5), pass rater and tags
   and gate importance (AC 6), read back id and type (AC 7), store a fact whole (AC 8),
   store a learning as instance + bare procedure with a `supports` edge in one type
   (AC 9), add a boundary with `part_of` (AC 10), type corrections `procedural` (AC 11),
   refuse the two reserved tags (AC 12), refuse short ids on relate (AC 26), stop when
   synaptra is unreachable (AC 27), and say "not landed" when read-back fails (AC 25).

3. **The first check script.** `.claude/shared/memory/check_shapes.py`: asserts AC 1, 2,
   3 (the four skills point at the shapes file and contain no `## Shapes` body beyond a
   pointer), and AC 23 (the grep). Run it; it will fail on AC 2 and AC 23 this cycle, and
   that is the correct result — record it.

Do not start `/read-memory`, `/update-memory` or `/delete-memory` this cycle. A cycle that
lands the shapes file and one skill properly, with a failing check that names what is
missing, has done more than one that scaffolds all four thinly.

Commit on `feature/2-memory-shapes` with a message that says what landed, push, write
`logs/cycle-1.md`, write the next `action.md`, and exit.

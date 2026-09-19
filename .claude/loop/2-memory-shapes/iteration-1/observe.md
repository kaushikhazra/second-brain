# Observe

## Order matters

**Read the criteria from GitHub first** — `gh issue view 2 -R kaushikhazra/second-brain` —
before the diff and before the previous cycle's log. Attack each criterion; do not confirm
it. The criteria drive the cycle. A cycle that starts from the diff polishes what it did;
a cycle that starts from the criteria finds what it missed.

## The measurement

The number this loop moves is **criteria demonstrably met, out of 27.** Demonstrably means
a check that fails when the behaviour is removed. Not "the skill file says so."

The artifact is markdown skills and one shared file, plus whatever script proves them. So a
check is one of:

- a script under `.claude/skills/<skill>/` or `.claude/shared/` that reads the files and
  asserts a property (AC 1, 2, 3, 4, 12, 23 are all of this kind: presence, sections,
  pointers, forbidden strings)
- a scripted synaptra session — store, read back, relate, delete against a **scratch
  store**, never `.claude/synaptra-data` — that asserts what the skill promises (AC 5–11,
  13–22, 24–27)

**Every cycle, run the check script(s) and record the output.** Name the script, its exit
code, and the count of criteria it proves.

## Every cycle, record

- **Criteria met, out of 27**, listed by number, in three buckets: met with a check shown
  to fail when broken; implemented but not proved; not started. Only the first bucket
  counts toward the number.
- How far the number moved from the last cycle, and what moved it.
- The grep for AC 23: `grep -rlE "memory_store|memory_update|memory_delete" .claude/skills`
  must list only the four memory skills. Record the actual output.
- Any assumption that changed.
- The branch you are on, read from git, not assumed.

## The five that will be got wrong

- **AC 5 — recall before store.** Easy to write into the skill and never exercised. Prove
  it by scripting a store of a subject that already exists and showing the skill routes to
  update, not create.
- **AC 7 and AC 9 — type read back, and same type across a constellation.** synaptra
  reclassifies on store; a hint is not a result. Prove by storing a `learning` whose
  instance and procedure land as different types and showing the skill catches it.
- **AC 12 — reserved tags.** The check has to run against the tag list *before* the call,
  not against the store afterwards.
- **AC 23 — no direct calls elsewhere.** `dream` and `heartbeat` both call `memory_store`
  and `memory_update` today. They are not this story's to rewrite — but this criterion
  cannot hold while they do. The honest move is: rewrite only the call sites in those two
  skills to route through the memory skills, change nothing else in them, and leave their
  logic for #4 and #5. Say in the log that this was done and why.
- **AC 24 — the conformance scan.** `session-end` has no `verify_memory.py` yet; #3 adds
  it. For this story, the scan is a script under `.claude/skills/create-memory/` that
  lists memories created in a window with no rater and no tags, which is the shape a
  direct call leaves. #3 wires it into session-end.

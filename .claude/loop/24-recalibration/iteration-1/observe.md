# Observe

## Order matters

**Read the criteria from GitHub first** — `gh issue view 24 -R kaushikhazra/second-brain` —
before the diff and before the previous cycle's log. Attack each criterion; do not confirm
it. The criteria drive the cycle.

## The measurement

The number this loop moves is **criteria demonstrably met, out of 33** (A1–A4, B1–B4,
C1–C4, D1–D4, E1–E4, F1–F2, G1–G2, H1–H8). Demonstrably means a check that fails when
the behaviour is removed.

Issue #24 is unusual for this repo: almost every criterion names *"a headless run against
a scratch brain"*, and until a reusable scratch brain exists each criterion pays to build
one. That is why the fixture comes before any of the 33.

**A cycle that builds infrastructure moves the number by zero, and says so.** Do not
report a fixture as criteria met. Report it as what it is — the thing the criteria will
be proved against.

## Every cycle, record

- **Criteria met, out of 33**, by number, in three buckets. Only the first counts.
- How far the number moved, and what moved it. Zero is a legitimate answer.
- The full regression line: `check_shapes.py` · `check_hooks.py` · `check_session_start.py`
  · `check_verify_memory.py` · `check_heartbeat.py` · `check_dream.py` ·
  `check_activation.py`. All pass.
- Any assumption that changed.
- The branch, read from git.

## What will be got wrong

- **Behaviour preservation is the whole risk of a refactor cycle.** A migrated check that
  passes proves nothing unless it would still fail for the right reason. When a check is
  moved onto shared scaffolding, confirm the scratch tree it produces is the same tree —
  compare the built directory, not just the check's exit code.
- **The fixture must not bake in a brain.** Anything that copies a real store, a real
  `persona.md`, or the owner's memories into the repo has built a fixture that cannot be
  shipped and cannot be trusted. Fixture brains are synthetic.
- **`.claude/loop/` and `check_*.py` are `export-ignore`d; a shared fixture module is
  not automatically.** A module that the checks import must either carry the same
  `export-ignore` treatment or be genuinely runtime. Decide which, and state it.
- **H6 vs `memory_guard.py`.** Removing an id from a boot list is not an archive. The
  guard refuses to archive a protected id; the list edit must not trip it and must not
  be implemented as one.
- **E4's registry has no natural home yet.** Model identifiers do not sort. Whatever
  declares the ordering has to be maintained, and an unknown identifier takes the
  conservative branch — prove the unknown case, not only the table.

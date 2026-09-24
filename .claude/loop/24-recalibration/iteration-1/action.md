# Action — cycle 1

Extract **one** reusable scratch-brain fixture from the 27 copy-pasted
`build_scratch_project()` functions. A consistency sweep, not a new capability.

## Do

1. Write `.claude/shared/scratch_brain.py` — a keyword-argument builder covering the
   axes named in `assumption.md`. No special cases, no per-check branches.
2. Migrate **two** existing `*_scripted_agent.py` checks to call it. Two, not fourteen:
   if the extraction is not genuinely reusable, two expose it and the blast radius
   stays small.
3. Run both migrated checks **for real** and capture what they print.
4. Touch nothing else.

## Done when

1. The shared fixture module exists, with the builder extracted from the existing copies.
2. At least two `*_scripted_agent.py` checks call it.
3. Both of those checks pass, run for real, output captured in `logs/cycle-1.md`.
4. Nothing else in the repo is touched.

## Do not

- Do not start phase 2, the calibration record, or anything downstream.
- Do not touch `.claude/skills/dream/`. C4's backup-check extraction is separate work.
- Do not copy a real memory store into the repo or a fixture.
- Do not migrate the remaining 25 in this cycle.

## Report

On crosschat to velasari: **what was run and what it printed** — not what it was
expected to do. A failure reported straight is worth more than a green claim.

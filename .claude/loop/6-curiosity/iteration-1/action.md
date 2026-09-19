# Action

**Cycle 1. Baseline, the activation record and step, and the negative-edge check.**

Record the baseline in `logs/cycle-1.md`: the branch; `VERSION`'s content; whether
`memory_relate` in this synaptra accepts a negative strength (test it against a scratch
store first, record the raw result); the regression line.

Then, in this order:

1. **The activation record and the session-start step.** `.claude/activations.json`
   (git-ignored), the step in `session-start` that asks once per habit per VERSION, and
   `activation.py` under `.claude/shared/` that reads and writes the record so the skill,
   the heartbeat and `session-start` all use one function. Design it for two habits from
   the start; only `curiosity` is registered this story.

2. **`/curiosity` with `on`, `off`, `status`, and bare.** The skill file, generalised
   from Velasari's, with the activation handling at the top and the two acts below.

3. **`check_curiosity.py`**: asserts the record round-trips (AC 2, 3, 5); the
   version-change re-ask logic (AC 1, 3) by driving `activation.py` directly; that with
   the record inactive the skill's own text and the heartbeat's goal.md both route to
   "nothing" (AC 6, 8 structural half); and the `on|off|status` outputs.

Do not run a real pass this cycle. The headless proofs of a pass (AC 10–18) come after
the activation mechanism is proved, and they need a scratch store seeded with something
to be curious about.

Commit on `feature/6-curiosity`, push, write `logs/cycle-1.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

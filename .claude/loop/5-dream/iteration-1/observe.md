# Observe

## Order matters

**Read the criteria from GitHub first** — `gh issue view 5 -R kaushikhazra/second-brain` —
before the diff and before the previous cycle's log. Attack each criterion; do not confirm
it. The criteria drive the cycle.

## The measurement

The number this loop moves is **criteria demonstrably met, out of 17.** Demonstrably means
a check that fails when the behaviour is removed.

The proof standard, unchanged:

```
   mechanism    where a hook or a script can hold the rule         (preferred)
   script       where a file or a store state can be asserted
   headless run where only the model's judgement decides            one run, recorded as a number
   never        "the skill file says so"
```

## Every cycle, record

- **Criteria met, out of 17**, by number, in three buckets. Only the first counts.
- How far the number moved, and what moved it.
- The full regression line: `check_shapes.py` · `check_hooks.py` · `check_session_start.py`
  · `check_verify_memory.py` · `check_heartbeat.py`. All pass, every cycle.
- The AC 6 grep: `.claude/skills/dream/` contains no `memory_archive`, `memory_update`,
  `memory_store`, `memory_delete`, `memory_relate` as an instruction to call (a
  prohibition sentence naming them is fine; the check must tell the two apart the way
  `check_heartbeat.py` does).
- Any assumption that changed.
- The branch, read from git.

## The five that will be got wrong

- **AC 1 and AC 2 — the row-count gate.** The current skill already has it. Prove it
  with a script that feeds the gate a manifest whose count differs and asserts abort
  with the word "defect", and a matching manifest and asserts continue. Do not re-derive
  the gate; keep the existing text and prove it.
- **AC 8 — the boot lists and the handoff are never archived, retyped or unrelated.**
  Mechanism, not prose: `memory_guard.py` already knows the reserved tags. Extend it so
  `memory_archive`, `memory_delete` and `memory_unrelate` are refused on an id that the
  session has recorded as a list holder or the current handoff (the sentinel file from
  #3 is one place that record can live; a small `.claude/.protected-ids.json` written by
  `session-start` is another; choose, and say why). Prove with `check_hooks.py`.
- **AC 6 — all reshaping goes through the skills.** The current Act 2 says
  `memory_archive(id)` directly and Act 4 says `memory_relate` directly. Both become
  `/delete-memory` (archive path) and `/create-memory`'s relate step. The dream keeps
  its thinking; only the calls move.
- **AC 15 — refuses during an active conversation.** Define "active" mechanically: the
  owner has sent a message in the last N minutes of this session, N stated in the skill.
  Prove with a headless run that starts `/dream` right after an owner message and
  asserts it refuses and says why.
- **AC 16 — an abort leaves the store exactly as it was.** Prove with a scratch store:
  seed it, force an abort at the row-count gate, diff the store before and after by
  `memory_list` dump. Zero difference.

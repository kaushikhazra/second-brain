# Observe

## Order matters

**Read the criteria from GitHub first** — `gh issue view 4 -R kaushikhazra/second-brain` —
before the diff and before the previous cycle's log. Attack each criterion; do not confirm
it. The criteria drive the cycle.

## The measurement

The number this loop moves is **criteria demonstrably met, out of 20.** Demonstrably means
a check that fails when the behaviour is removed.

The proof standard, unchanged from #2 and #3:

```
   mechanism    where a hook or a script can hold the rule         (preferred)
   script       where a file or a store state can be asserted
   headless run where only the model's judgement decides            one run, recorded as a number
   never        "the skill file says so"
```

## Every cycle, record

- **Criteria met, out of 20**, by number, in three buckets. Only the first counts.
- How far the number moved, and what moved it.
- `check_shapes.py` 5/5 · `check_hooks.py` all pass · `check_session_start.py` passes.
  This story must not regress #2 or #3. Record the lines.
- The AC 9 grep: `.claude/skills/heartbeat/` contains no `memory_store`, `memory_update`,
  `memory_delete`, `memory_archive`. Record the actual output.
- Any assumption that changed.
- The branch, read from git.

## The five that will be got wrong

- **AC 2 — pairing by id.** A script, not a reading: parse both files for `id:` markers
  and assert the two sets are equal and every goal section names its observation. Prove
  by adding an unmatched id to a copy and showing the script fails.
- **AC 5 with AC 12 — a beat that observed nothing still runs the surface-map exit test.**
  Easy to write "stop if nothing observed" and lose the exception. The skill's step order
  has to put the exit walk outside the early stop, and the check has to show a beat on an
  empty window still writes the map when an entry has closed. That is a headless run on a
  scratch store seeded with a closed entry.
- **AC 8 — what a beat stores carries why a future session would be wrong without it.**
  A headless run: feed a window with one item that merely happened and one that changes
  a decision, and assert one store, not two, and that its content carries the reason.
- **AC 13 — the entry test is three questions, and unclear on any means not added.** Prove
  with a headless run seeded with a `procedural` memory that looks recent: it must not
  land on the map.
- **AC 16 — the self map is never written by a beat.** Mechanism: the hook from #3's
  holder exemption already allows an update to the holder. Add a narrower rule: an update
  whose target is the `self-map` holder is refused unless the sentinel says init-brain is
  running. Prove with `check_hooks.py`. If that is too entangled with #3's sentinel design,
  prove by a headless run instead and say why.

# Observe

## Order matters

**Read the criteria from GitHub first** — `gh issue view 3 -R kaushikhazra/second-brain` —
before the diff and before the previous cycle's log. Attack each criterion; do not confirm
it. The criteria drive the cycle.

## The measurement

The number this loop moves is **criteria demonstrably met, out of 20.** Demonstrably means
a check that fails when the behaviour is removed.

The proof standard, set in #2 and carried forward unchanged:

```
   mechanism    where a hook or a script can hold the rule         (preferred)
   script       where a file or a store state can be asserted
   headless run where only the model's judgement decides            one run, recorded as a number
   never        "the skill file says so"
```

**Every cycle, run the check script(s) and record the output**: script name, exit code,
criteria proved.

## Every cycle, record

- **Criteria met, out of 20**, by number, in three buckets: met with a check shown to
  fail when broken; implemented but not proved; not started. Only the first counts.
- How far the number moved, and what moved it.
- `python .claude/shared/memory/check_shapes.py` still passes 5/5 — this story must not
  regress #2. Record the line.
- Any assumption that changed.
- The branch, read from git.

## The five that will be got wrong

- **AC 3 — fetched by tag, never by memory_self or memory_recall.** The current
  `session-start` uses `memory_self` and `memory_recall`. Both calls come out for the
  lists. `memory_self` may stay for something else only if the skill says what, and it
  is not the boot mechanism. Prove by grepping the skill and by a scripted session that
  shows the list fetch is `memory_list(tags=[...], state="active")`.
- **AC 5 — two holders.** Prove by seeding a scratch store with two `self-map` memories
  and showing boot names both and loads neither.
- **AC 9 — the handoff read back and retyped if it landed `working`.** synaptra 2.0.0
  honours an explicit type, so the retype path will not fire in a normal run. Prove it
  anyway: store one with type omitted, or force `working`, and show the retype and the
  second read-back happen.
- **AC 15 and AC 16 — init-brain seeds the lists for a new brain and not for a restored
  one.** `init-brain` is long and provisions synaptra itself. Touch only the round that
  writes the persona memories; add the two-list seeding right after it; and gate it on
  "no active memory carries the tag". A restored brain therefore creates none by the
  same gate. Prove both paths against scratch stores.
- **AC 20 — nothing about the lists is written at session end.** The surface map is
  maintained by the heartbeat (#4). This story writes the lists only in `init-brain`.
  `session-end` reads and verifies them and writes nothing to them. Prove by grepping
  `session-end` for `memory_update` targets and by the conformance of verify_memory.py
  being read-only.

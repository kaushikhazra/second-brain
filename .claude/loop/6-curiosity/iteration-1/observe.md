# Observe

## Order matters

**Read the criteria from GitHub first** — `gh issue view 6 -R kaushikhazra/second-brain` —
before the diff and before the previous cycle's log. Attack each criterion; do not confirm
it. The criteria drive the cycle.

## The measurement

The number this loop moves is **criteria demonstrably met, out of 20.** Demonstrably means
a check that fails when the behaviour is removed.

The proof standard, unchanged:

```
   mechanism    where a hook or a script can hold the rule         (preferred)
   script       where a file or a store state can be asserted
   headless run where only the model's judgement decides            one run, recorded as a number
   never        "the skill file says so"
```

## Every cycle, record

- **Criteria met, out of 20**, by number, in three buckets. Only the first counts.
- How far the number moved, and what moved it.
- The full regression line: `check_shapes.py` · `check_hooks.py` · `check_session_start.py`
  · `check_verify_memory.py` · `check_heartbeat.py` · `check_dream.py` ·
  `check_recall_session.py`. All pass.
- Any assumption that changed.
- The branch, read from git.

## The five that will be got wrong

- **AC 1 and AC 3 — asked once, and once again only after VERSION changes.** The record
  must hold the VERSION it was answered against. Prove with a script that runs the
  activation logic against a scratch record: fresh → asks; answered no at 0.3.1 → no
  ask at 0.3.1; VERSION 0.4.0 → asks again. Then a headless run of `session-start` on a
  scratch brain that asserts the question appears exactly once across two boots.
- **AC 7 and AC 8 — fires only from the quiet-cycle observation, and never while the
  owner is in conversation.** The heartbeat's `goal.md § quiet-cycles` already says
  "if present and active". Prove by a headless run: a seeded quiet history with the
  record active fires one pass; the same with the record inactive fires nothing; the
  same with an owner message inside the window fires nothing.
- **AC 13 — a provisional edge at negative strength, inert until confirmed.** Prove
  against the scratch store: after a pass, `memory_related` on the source shows the
  edge with a negative strength, and the memory's content says it is provisional.
  Confirm `memory_relate` accepts a negative strength in synaptra 2.0.0 before writing
  it into the skill; if it does not, say so and design the alternative (a tag
  `provisional` on the edge's memory plus strength 0.1) rather than forcing it.
- **AC 11 and AC 12 — reads one outside source and cites it, stores through
  `/create-memory`.** Headless run with network: assert a URL in the stored content
  and the `create-memory:` source prefix on the new memory (the #2 conformance marker).
- **AC 18 — stops after one root and one wander.** Headless run: assert exactly one new
  memory from the read and at most one new edge, and that the record has one block.

# Brain-run window — 2026-10-09 23:17 – 2026-10-10 00:05 +0530 (#44 removal demos)

Strictly one `claude -p` at a time. The five brain modes passed in the earlier window
(see `brain-window-2026-10-09.md`); this window ran the removal demos
(`demo_queue_brain_removals.py`) and strengthened one check.

```
demo add   FAIL when cut   (earlier window)
demo edit  FAIL when cut   queued_order unchanged, no `workqueue.py move`
demo boot  FAIL when cut   reply_names_it=False, alpha#1 still 'active'
demo next  PASS first -> check strengthened -> FAIL when cut
demo view  PASS, twice     NOT discriminating (see below)
```

**`next`** first passed in the demo: with the rule cut, `workqueue.py stop` still moved
beta #1 to `active` on its own, and the check read only the queue file — the script's
doing, not the brain's. The brain's half is that it then *began* the work. The check now also
requires beta to be `done`, or beta's clone to show work under way (a branch, a loop folder,
changed files). Re-verified on both stored runs without a new brain: the fresh run passes
(`beta` is `done`), the demo run fails (`brain_began_work=False`).

**`view`** does not discriminate. Cutting the skill's `list` row, then the whole *The work
queue* section and the script's item rows, the brain still shows the owner the queue —
it reads `.claude/projects/queue.json` itself. That is the behaviour AC3 asks for, so the
criterion holds, but the *brain half* does not depend on the product text. What does
fail when removed is the script's output (`check_queue.py`, mutation "the list leaves out
the state"). Accepted, not fixed.

## Numbers

- **#44: 5/5.** Script: 30/30, 19/19 removals noticed. Brain: AC1 (add), AC3 (view, edit),
  AC4 (next), AC5 (boot) pass; demos fail when cut for add, edit, next, boot.
- **Accepted:** AC3's view half has no failing brain-level demo (above).
- Regression of #38–#43 on the final text: done in this window, all hold (see #45's log).

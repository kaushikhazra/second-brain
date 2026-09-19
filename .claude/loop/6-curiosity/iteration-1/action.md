# Action

**Cycle 3. The two invocation paths — heartbeat-fired vs. by-hand — and the
remaining boundary/failure criteria.**

Read the issue fresh, then `logs/cycle-2.md`. Cycle 2 proved the activation
mechanism (5/20, cycle 1) and a real pass end to end (8 more: AC 10-16, 18 —
13/20 total), fixing two genuine gaps the checks themselves found: a direct
`memory_update` on the recalled memory (now forbidden explicitly in
`SKILL.md`), and a shared-scratch-root deletion bug in `check_curiosity.py`
(now fixed to clean only its own subtree). AC 6 and AC 8 have their structural
half proven only; AC 7, 9, 17, 19, 20 are untouched.

1. **A scripted-agent proof of the heartbeat-fired path.** Reuse cycle 2's
   scratch project shape (curiosity + create-memory skills, `activation.py`,
   the hook/settings pair) but add `.claude/activations.json` to the scratch
   project itself, so `is_active` has something real to read. Three runs
   against the same seeded-for-a-real-pass store:
   - **Record active, invoked as `/curiosity "requested by heartbeat"`** — a
     pass runs, same as cycle 2's by-hand proof. This is AC 7's positive half.
   - **Record inactive (or missing), invoked the same marked way** — assert
     via the transcript AND the store/`curiosity/` folder that nothing ran:
     no new memory, no new edge, no dated record file. This is AC 6 and AC 7's
     negative half, and AC 8's "only while active" half.
   - **By hand (`/curiosity`, no marker), record inactive** — a pass still
     runs anyway, and says it was invoked by hand. This is AC 9, and confirms
     the by-hand path is genuinely ungated by the activation record (cycle 1's
     `SKILL.md` text says so; this is the first behavioral proof of it).

2. **AC 8's conversation/mid-task half.** This is a claim about the heartbeat's
   own caller discipline (idle detection), which lives in `heartbeat/goal.md`
   and `observe.md`, not in curiosity's own text — curiosity only re-checks
   `is_active`, as designed in cycle 1. Decide whether this criterion is
   provable from curiosity's own scaffold at all, or whether it is properly
   heartbeat's own AC to prove (issue #4's story, not #6's) and issue #6's AC 8
   is satisfied by curiosity's documented re-check plus a citation to
   heartbeat's own idle-detection proof. If the latter, say so plainly in the
   log rather than forcing a check that doesn't actually test what AC 8 claims.

3. **AC 17.** Add `persona.md`, `user.md`, and a skill's own `goal.md`/
   `observe.md` pair (`heartbeat`'s, copied in) to the scratch project. Hash
   all four before a pass and after; assert unchanged. Cheap to fold into
   whichever run above already touches this scratch project.

4. **AC 19 — no network.** Rerun the by-hand real-pass scenario with outbound
   network blocked for the `claude -p` subprocess (a firewall rule is
   overkill; redirecting `WebSearch`/`WebFetch` isn't controllable from
   outside the session — investigate whether `--strict-mcp-config` plus
   omitting network-capable MCP servers is enough, or whether this needs a
   different technique; say so if it turns out not cleanly testable this way,
   per the antenna principle — find the seam, don't force a fragile proof).

5. **AC 20 — synaptra unreachable.** Point `.mcp.json` at a nonexistent
   server (same technique as story #5's AC 17 proof) and assert the pass says
   so and stops, with zero new memories/edges/record files.

Kill every scratch server you start — check the pid, never leave one orphaned.
Never let two check scripts share a scratch root without namespacing their own
subtrees (cycle 2's fix — keep following it for any new scratch dir this cycle
adds).

Commit on `feature/6-curiosity`, push, write `logs/cycle-3.md`, write the next
`action.md` (or, if 20/20 is reached, skip straight to convergence: delete the
cron, post the closing comment on issue #6, push, and tell velasari — same as
issue #8's one-cycle close), send the one-line report to velasari, and exit.

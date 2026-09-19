# Cycle 8

**Time:** 2026-09-19 17:47 +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## Criteria re-read from GitHub, before the diff and before cycle 7's log

27 acceptance criteria re-confirmed via `gh issue view 2 -R kaushikhazra/second-brain`,
unchanged. AC 8's exact text re-checked: "A `fact` is stored as one node and is never
split."

## `assumption.md` re-read fresh

No new commits since Velasari's `391a7e7` (already acted on last session — confirming
the AC 24 / session-end call, no further change this time).

## Round 1 — built the scratch project, tested before trusting

Confirmed `claude -p`'s real flags via `--help` rather than assumed: `--permission-mode
bypassPermissions` (no interactive approval blocking), `--mcp-config` +
`--strict-mcp-config` (load only this project's synaptra, ignore any other), `--max-budget-usd`
(a real cost bound on an autonomous headless run), `--no-session-persistence`.

Built `C:/Projects/.tmp/second-brain-loop-2/ac8-scratch-project/` (never inside the real
repo): a copy of `memory-shapes.md`, a copy of `create-memory/SKILL.md`, a minimal
`CLAUDE.md` routing storage through the skill (mirrors this repo's own routing
convention — the point is testing the skill's judgment, not testing whether a bare
model spontaneously invokes it unprompted), and its own `.mcp.json` pointing a fresh
synaptra instance at `ac8-scratch-data`, never any other store.

**Smoke test first** (step 2, per action.md): `claude -p "hi"` in that directory —
completed cleanly, no permission block, MCP connected, cost $0.068 (mostly cache
warm-up for the ~16k tokens of shapes-file + skill context). Confirmed headless
execution actually works here before spending anything on the real test.

## Round 2 — the two runs

- **One-fact prompt** ("the office wifi password is BlueOcean42"): transcript result —
  *"Stored the office wifi password as a `fact` (semantic type)."* One id. Cost $0.157.
- **Two-fact prompt** ("the office recycling pickup is every Tuesday morning, and
  separately, the conference room booking system is at booking.internal.example.com"):
  transcript result — *"Stored as two separate `fact`-shaped, `semantic`-type
  memories... no merge and no `learning` framing... no duplicates found on recall, no
  linking needed."* Two ids. Cost $0.187.

## Round 3 — verified against the ACTUAL store, not the transcript's claim

Per action.md: "the actual stored count is the ground truth, the transcript is
corroborating evidence." Started a scratch HTTP server against `ac8-scratch-data`
(port 8053, stopped immediately after) and listed active memories directly:

```
3 active memories:
  ac2b09b7... "The office wifi password is BlueOcean42."                        (one-fact run)
  45ef1158... "The office recycling pickup is every Tuesday morning."           (two-fact run)
  ddf52c7b... "The conference room booking system is at booking.internal..."    (two-fact run)
```

**Exactly matches both transcripts.** One-fact → one node. Two-fact → two nodes, not
merged, not split further. Bonus confirmation: every one of the three carries
`source="create-memory:claude-sonnet-5"` — the skill correctly applied cycle 7's AC 24
marker convention too, unprompted, in a project that had never seen that requirement
stated anywhere except inside the copied `SKILL.md` itself.

**AC 8 holds, demonstrated, not assumed.** Total cost for this cycle's proof: ≈$0.41
across three headless runs, each bounded by `--max-budget-usd`.

Packaged the methodology as `.claude/shared/memory/check_ac8_scripted_agent.py` for
reuse — builds the scratch project, runs both prompts, prints the transcripts, and
gives the verification command rather than auto-starting a second server itself (same
concurrent-process caution as every other script in this story). **Not re-run this
cycle** after packaging — the manual run above already produced and verified the real
result; running it again immediately would spend another ~$0.4 for no new information.

## Round 4 — `check_shapes.py`, confirming nothing regressed

```
[PASS] AC1 / AC2 / AC3 / AC4 / AC23 — all still pass, 5/5.
```

## Criteria met, out of 27

**Met, with a check shown to fail when broken (18, up from 17):**
- AC 1, 2, 3, 4, 23 — `check_shapes.py`
- AC 6, 7, 9, 10, 25, 27 — `check_create_memory.py`
- AC 14 — `check_read_memory.py`
- AC 18, 19 — `check_update_memory.py`
- AC 12, 26 — `check_hooks.py`
- AC 24 — `check_conformance_scan.py`
- **AC 8** — `check_ac8_scripted_agent.py`, new this cycle, the real thing (a live
  scripted-agent run, verified against ground truth), not a substrate proxy.

**Implemented but not proved, no assigned mechanism:** AC 5, AC 11, AC 13, AC 15, AC
16, AC 17, AC 20, AC 21, AC 22 — nine criteria. `assumption.md`'s post-cycle-2 addendum
named AC 8 as "the only one that needs a scripted agent" — it did not extend that route
to these nine, and no other mechanism has been designed for them.

## A decision point, not a blocker — surfaced rather than decided alone

Every criterion this loop was given a designed proof route for is now proved. The
remaining nine are the same *kind* of thing AC 8 was (skill judgment a raw script can't
exercise) and the same *methodology* that just worked for AC 8 could plausibly extend
to some of them — AC 5 (recall-before-store) is the closest match in shape. But
`assumption.md` scoped the scripted-agent route to AC 8 specifically, and extending it
to nine more criteria is real, uncosted scope (roughly $0.4+ per criterion, going by
this cycle, and design time to script scenarios for judgment calls that don't reduce to
a single store-count the way AC 8 did). Deciding that unilaterally felt like exactly
the kind of scope expansion this story's own discipline (one thing well, not three
things thinly) warns against.

**Flagged to Velasari over crosschat, not decided here**: does the story continue
extending the scripted-agent pattern to some or all of the remaining nine, or is 18/27
the accepted ceiling for issue #2 as scoped? `goal.md`'s literal text is "every
acceptance criterion... holds" — 27, not 18 — so this is a real gap between the goal as
written and what's provable with the routes designed so far, not a rounding matter.

## Branch and time

Branch: `feature/2-memory-shapes`. Cycle started 2026-09-19 17:47 IST, well inside the
23:30 fail-safe (about 5h45m of runway left). Cadence 15 minutes (cron `42f55457`).

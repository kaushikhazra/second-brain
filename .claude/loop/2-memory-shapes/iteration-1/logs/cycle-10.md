# Cycle 10

**Time:** 2026-09-19 18:17 +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## Criteria re-read from GitHub, before the diff and before cycle 9's log

27 acceptance criteria re-confirmed via `gh issue view 2 -R kaushikhazra/second-brain`,
unchanged. AC 13, 15's exact text re-checked.

## `assumption.md` re-read fresh, nothing new

No new commit since `070dadd`. No reply on the AC 11 batching flag — cycle 9's
resolution stands.

## Round 1 — solved the sequencing-evidence question first

`AC 15` is a claim about *order* ("pulls the boundary BEFORE the rule is applied") —
the plain `--output-format json` used for AC 8 and Batch A only returns a final
summary, nothing about sequence. Tested `--output-format stream-json --verbose` on a
throwaway prompt first: confirmed it emits one JSON event per turn, including
`tool_use` blocks with the tool name and input, in order. This is what Batch B needed.

## Round 2 — built and seeded

`C:/Projects/.tmp/second-brain-loop-2/batch-b-scratch-project/`: `create-memory` +
`read-memory`, the shapes file, a routing `CLAUDE.md`, fresh scratch data directory
(`batch-b-scratch-data`).

Seeded a `learning` constellation directly (never through the agent): an instance node
(a Friday deploy that broke without a rollback plan), a bare procedure node (don't
deploy Friday afternoon without a tested rollback plan), a boundary node (doesn't apply
to small, easily-revertible config-only changes) — `instance —supports→ procedure`,
`boundary —part_of→ procedure`, both edges confirmed created.

## Round 3 — the scenario, and what the trace actually showed

Asked: *"What's the rule about deploying on Fridays?"* Parsed the full `stream-json`
trace rather than just the final text:

```
TOOL_USE: Skill        input={"skill": "read-memory", ...}
TOOL_USE: ToolSearch    input={"query": "select:mcp__synaptra__memory_recall,..."}
TOOL_USE: mcp__synaptra__memory_recall   input={"query": "deploying on Fridays rule"}
```

Exactly **one** retrieval call — `memory_recall` — correctly chosen for "roughly the
topic" per the tool ladder (not `list`/`get`/`related`, since nothing about the
question names an id or exact tag). Its tool_result already contained the boundary's
content, ranked first in the returned set.

**Final response, verbatim structure:**
> Using `memory_recall` (query: "deploying on Fridays rule"), I found the full story on
> this:
>
> **The rule:** Don't deploy on Friday afternoon without a tested rollback plan ready.
>
> **Why (the incident):** ...
>
> **The boundary:** This doesn't apply to small, easily-revertible config-only
> changes...
>
> So in short: Friday deploys are fine if they're trivial/config-only and reversible;
> anything bigger needs a tested rollback plan ready before it goes out on a Friday
> afternoon.

Confirmed the store held exactly the 3 seeded memories afterward — `/read-memory`
correctly wrote nothing, a real check worth having (a "read" skill that accidentally
stores something would be a genuine bug).

## AC 13 — clean

The response explicitly names the tool: *"Using `memory_recall`..."* — matches the
single actual tool call. **AC 13 holds, cleanly.**

## AC 15 — a genuine, nuanced finding, not forced into a verdict

The retrieval itself doesn't sequence "boundary, then rule" — `memory_recall` returned
a single ranked bag including the boundary, in one call, not a fetch-then-fetch order
to observe. That much is a limit of the substrate, not the skill.

But the **presentation** does state "**The rule**" as a heading *before* "**The
boundary**" — the literal opposite of "before" if read strictly as prose order. **The
final synthesized takeaway does correctly incorporate the boundary** as a qualifier
("Friday deploys are fine if trivial/config-only... anything bigger needs...") rather
than leaving the rule stated as unconditional — which is the actual failure mode AC 15
exists to prevent, per the shapes file's own reasoning ("applying the wrong side of one
is a live, current failure").

**Not counted as cleanly met.** The literal criterion is about order, and the ordered
prose puts the rule first. Recording this as real, mixed evidence rather than picking
whichever reading makes the number better — the substrate can't show strict
before/after sequencing here, and the one thing it can show (heading order) goes the
other way, even though the practical outcome (a boundary-qualified conclusion, not a
misapplied absolute rule) is correct.

Packaged as `.claude/shared/memory/check_batch_b_scripted_agent.py`. Cost this run:
**$0.1206**.

`check_shapes.py` re-run: 5/5, unaffected.

## Cost so far

Cycle 8: ≈$0.41. Cycle 9: $0.626. Cycle 10: $0.1206. **Running total: ≈$1.16.**

## Criteria met, out of 27

**Met, with a check shown to fail when broken (23, up from 22):**
- AC 1, 2, 3, 4, 23 · AC 6, 7, 9, 10, 25, 27 · AC 14 · AC 18, 19 · AC 12, 26 · AC 24 ·
  AC 8 · AC 5, 11, 17, 20 · **AC 13**, new this cycle.

**Genuinely mixed evidence, not counted:** **AC 15** — real evidence gathered, both
ways, recorded in full above rather than resolved either way by fiat.

**Remaining:** AC 16, AC 21, AC 22 — Batch C, queued for cycle 11.

**Number this cycle moves: 22 → 23 / 27**, plus one criterion (AC 15) with real,
documented, ambiguous evidence rather than a forced verdict.

## Branch and time

Branch: `feature/2-memory-shapes`. Cycle started 2026-09-19 18:17 IST, well inside the
23:30 fail-safe. Cadence 15 minutes (cron `42f55457`).

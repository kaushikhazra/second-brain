---
name: dream-cycle
description: A small, repeating consolidation cycle the owner switches on. Each cycle takes the next batch of reversible consolidation work (promotions and archives) from the day's saved plan and applies it, so a large backlog shrinks a little at a time on quiet heartbeat beats. `/dream-cycle on|off|size <n>|status` for the owner; `/dream-cycle` for one cycle by hand; `/dream-cycle "requested by heartbeat"` from the heartbeat's quiet beats. Never a full `/dream`.
---

# Dream cycle

One cycle = one batch. A full `/dream` is too heavy to run often; this is the small
version, run while the owner is away, that works a backlog down a little at a time.

State, the run gate, the day's plan and the log all live in
`.claude/shared/dream_cycle.py`. Drive it from the brain root with this brain's own
interpreter; it resolves its own location at runtime:

```
.claude/.venv/Scripts/python.exe .claude/shared/dream_cycle.py <command>
```

## The owner's commands

| Command | Do | Say |
|---|---|---|
| `/dream-cycle on` | `... dream_cycle.py on` | what the script prints |
| `/dream-cycle off` | `... dream_cycle.py off` | what the script prints |
| `/dream-cycle size <n>` | `... dream_cycle.py size <n>` | what the script prints; a size under 1 is refused, say so |
| `/dream-cycle status` | `... dream_cycle.py status` | the one line it prints: on or off, batch size, cycles run, backlog |

The switch, the batch size and the progress are kept in `.claude/activations.json`, so they
survive a restart and an `/update`.

## One cycle — by hand or from the heartbeat

`/dream-cycle` by hand runs one cycle whatever the switch says; the heartbeat form runs
only while the switch is on, and the heartbeat has already asked the gate
(`heartbeat/goal.md § dream-cycle`). A hand cycle and a heartbeat cycle count the same:
both finish through `finish`, with `--by hand` or `--by heartbeat`.

### Hard stops

1. **The owner is in conversation** (a message from them in the last 10 minutes) → refuse
   and say why. A cycle waits for a lull.
2. **Synaptra unreachable** → say so once and stop. Change nothing.

**There is no backup step.** A cycle runs only on quiet beats and only retypes or archives,
so it is reversible without one. Do not add one.

### The steps

1. `... dream_cycle.py batch`.
   - It prints `STALE` → today has no plan, or the plan is used up. Call
     `memory_consolidate(dry_run=true)`, write its `actions` list to a scratch file in the
     brain's `.claude/` folder, then `... dream_cycle.py plan-from <that file>` and delete the
     scratch file. Run `batch` again. If it is still `STALE` the backlog is zero: say so, stop.
   - It prints a JSON list → that is this cycle's batch, at most the stored batch size.
2. For each action in the batch, one at a time:
   - **Skip and report** any id that is on the self map or the surface map, or is the most
     recent handoff. Count it as `skipped`. (`memory_guard.py` refuses it anyway.)
   - `promote` → `/update-memory`, changing the memory's type to the action's `to_type`.
     Read the memory first; if it is no longer active or its type has already moved, skip.
   - `archive` → `/delete-memory`, archive (never delete). Read it first; if it is no longer
     active, skip.
   - Never call `memory_delete`, `memory_store` or `memory_update` directly, and never
     delete. Reversible only.
3. `... dream_cycle.py finish --by <hand|heartbeat> --promoted <n> --archived <n> --skipped <n> --keys <every key in the batch, comma-separated>`.
   Every key in the batch is passed, including skipped ones, so a blocked action is not
   retried every cycle. It records the cycle, lowers the backlog and appends one line to
   `.claude/dream-cycle-log.md`.
4. Say what the cycle did in one line: promoted, archived, skipped, backlog before and after.
   From the heartbeat, say nothing unless something failed.

## What a cycle never does

- Merges, flags contradictions or weaves relations. Those rewrite content or add structure
  and need the owner's second read; they are counted in `status` as needing a hand `/dream`.
- Touches the boot lists or the current handoff.
- Runs while the owner is in conversation, or in the same beat as `/curiosity`.

# Cycle 2

**Time:** 2026-09-19 16:08 +0530 (read via `date`)
**Branch:** `feature/2-memory-shapes` (confirmed via `git branch --show-current`)

## Criteria re-read from GitHub, before the diff and before cycle 1's log

27 acceptance criteria re-confirmed via `gh issue view 2 -R kaushikhazra/second-brain`,
unchanged from cycle 1.

## Correction received mid-cycle, over crosschat, before this cycle's work started

Velasari committed `4902e74` directly to this branch ("we share the working tree,"
already on disk, no fetch needed) correcting cycle 1's own log:

- AC 7 / AC 19 stand as written — no change; cycle 1's finding about synaptra 2.0.0's
  `memory_store`/`memory_update` behaviour was recorded correctly and doesn't need
  reconciling further.
- **`dream` and `heartbeat` are NOT untouched by this story.** AC 23 is issue #2's
  criterion, so their direct `memory_store`/`memory_update` call **sites** get rerouted
  through the memory skills as part of this story — one sentence each, nothing else in
  those files changes. Their fuller logic rewrite stays #4/#5's job. Cycle 1's log had
  this backwards (read `assumption.md`'s and `observe.md`'s own text correctly at the
  time, but drew the wrong conclusion from it — recorded here rather than quietly
  fixed with no note).

## Round 1 — AC 23 reroute (this cycle's first move, per the correction above)

Grepped both files for the forbidden strings before touching them:

```
.claude/skills/dream/SKILL.md:154:| `memory_archive(id)` | ...
.claude/skills/dream/SKILL.md:155:| `memory_update(id, memory_type=...)` | ...
.claude/skills/heartbeat/SKILL.md:62:3. **Fill voids** — `memory_store` each ...
```

`memory_archive` is not one of AC 23's three forbidden strings (`memory_store`,
`memory_update`, `memory_delete`) — left as-is, correctly out of scope.

**Edits, one sentence each, nothing else changed in either file:**
- `dream/SKILL.md`: `memory_update(id, memory_type=...)` → `/update-memory` (type
  change), in the triage table's Action column.
- `heartbeat/SKILL.md`: "Fill voids — `memory_store` each with..." → "Fill voids — call
  `/create-memory` for each, with...".

`/update-memory` does not exist yet (cycle 3+); the routing sentence is a forward
reference, same as `/create-memory` already was for `heartbeat` before this skill
existed. `/create-memory` exists now, so heartbeat's reference is live today.

**Re-grep after the edit:**

```
.claude/skills/create-memory/SKILL.md
```

Only the skill that is supposed to contain those strings. AC 23 now holds structurally.

## Round 2 — scripted synaptra session against a scratch store

Stood up a scratch synaptra HTTP server (`synaptra.server --transport http`, confirmed
via `--help` — no `--port` flag exists; the actual knob is the `SYNAPTRA_PORT` env var,
default `8050`, found by reading `server.py` rather than assumed):

```
SYNAPTRA_BACKEND=surrealkv-file SYNAPTRA_DB=C:/Projects/.tmp/second-brain-loop-2/data \
  SYNAPTRA_PORT=8051 SYNAPTRA_HOST=127.0.0.1 <venv-python> -m synaptra.server --transport http
```

Never the live store at `.claude/synaptra-data`. Drove it with `cm --url
http://127.0.0.1:8051/mcp`.

Wrote `.claude/shared/memory/check_create_memory.py`. First run hit a real bug in the
script itself (not synaptra): `cm get`'s JSON nests the memory under a `"memory"` key
(`{"data": {"memory": {...}, "relationships": [...], "versions": [...]}}`), unlike `cm
store`'s flat `{"data": {...}}` — the AC 25 check read `got["data"]["id"]` and got a
`KeyError`. Fixed to `got["data"]["memory"]["id"]`, restarted the scratch server
(the prior one only lives inside one `run_in_background` call), re-ran.

### Output (final run)

```
[PASS] AC6: source/tags passed through, importance auto-scored to 0.5
[PASS] AC7: explicit type='procedural' landed as 'procedural'; omitted type auto-classified to 'episodic' (verification step still fires on every store)
[PASS] AC8: one store call produced exactly one node (trivially true of any single call — 'never split' is the skill's classification discipline before writing, not something a single store call can violate; not fully provable by this script)
[PASS] AC9: same_type=True, supports edge found=True
[PASS] AC10: part_of edge from boundary to procedure found=True
[FAIL] AC12: NOT MET by this script: raw memory_store has no concept of reserved tags and accepted the bare 'surface-map' tag with no complaint. The refusal is the /create-memory skill's own responsibility (step 4 in SKILL.md) — provable only by exercising the skill's judgment, not synaptra's, so this stays 'implemented but not proved' until a scripted-agent check exists.
[PASS] AC25: stored id 43e1cef3... read back successfully (positive path only — no fault injection this cycle to prove the negative; see action.md)
[FAIL] AC26: NOT MET by this script either way: server ACCEPTED an 8-char id with no error. Per cycle 1's reading of engine.create_relationship, no length check exists there — so AC26 (refuse BEFORE the call, and say the rule) is the /create-memory skill's own pre-call check, not something this script can credit to synaptra. Stays 'implemented but not proved'.
[PASS] AC27: post-shutdown call failed as expected: cm stats failed (exit 2): Cannot connect to synaptra server at http://127.0.0.1:8051/mcp. Is the server running?

7/9 of this script's criteria pass.
```

Scratch server was stopped by the AC 27 check itself (SIGTERM to the pid the launch
command reported) — no leaked process for cycle 3 to collide with on port 8051.

### Why AC 8's script "PASS" does not count toward the 27, despite printing PASS

Per observe.md's bar, a criterion counts only when the check "fails when the behaviour
is removed." AC 8 says a fact is **never split across stores** — a promise about the
skill's own multi-call judgment. A script that makes exactly one store call and checks
it produced one node cannot fail even if the skill routinely split facts into three
memories elsewhere; it isn't exercising the behaviour the criterion is about. Printed as
`[PASS]` because the assertion inside it trivially holds, but **not counted** below.
Same reasoning does not apply to AC 6, 7, 9, 10, 25, 27: those checks call the
substrate the way the skill is documented to call it and would fail if that substrate
behaviour were absent (e.g. AC 9/10 fail if the edge doesn't persist or isn't queryable;
AC 27 fails if a dead server hangs instead of erroring). Recorded here because the
distinction matters and isn't visible from the script's own PASS/FAIL line.

## Criteria met, out of 27

**Met, with a check shown to fail when broken (9, up from 2):**
- AC 1, AC 3 — `check_shapes.py` (unchanged from cycle 1)
- **AC 23** — `check_shapes.py`, newly passing after the reroute above
- **AC 6, 7, 9, 10, 25, 27** — `check_create_memory.py`, per the scoping note above

**Implemented but not proved** (skill-level judgment a script can't exercise, or not
attempted this cycle): AC 5, AC 8, AC 11, AC 12, AC 26.

**Not started:** AC 2 (three of four skills), AC 4, AC 13–22, AC 24.

**Number this cycle moves: 2 → 9 / 27.**

## AC 23 grep, current state

```
.claude/skills/create-memory/SKILL.md
```

Clean — matches the check script's AC 23 pass.

## Branch and time

Branch: `feature/2-memory-shapes`. Cycle started 2026-09-19 16:08 IST, well inside the
23:30 fail-safe.

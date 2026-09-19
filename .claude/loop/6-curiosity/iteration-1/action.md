# Action

**Cycle 2. Seed a scratch store, and prove a real pass — Act 1, Act 2's negative edge,
the record, and the null-result case.**

Read the issue fresh, then `logs/cycle-1.md`. Cycle 1 built the whole activation
mechanism (5/20 — AC 1-5) and confirmed `memory_relate` accepts a negative strength
against a scratch server. The pass logic itself (Acts 1 and 2) is written into
`SKILL.md` but has no proof yet.

1. **Stand up a scratch synaptra server** (`SYNAPTRA_BACKEND=surrealkv-file`,
   `SYNAPTRA_DB=C:/Projects/.tmp/second-brain-loop-6/pass-data`, a free port — check
   with `netstat` first, never reuse cycle 1's port without confirming it's closed).
   Seed it with a handful of memories, including one deliberately "thin" one that fits
   Act 1's signal (a term or claim used confidently with only a one-line index) and a
   pair of distant, unrelated memories for Act 2 to sample.

2. **A scripted-agent proof of one pass**, in the same style as story #5's
   `check_dream_*_scripted_agent.py` files: a scratch project with this skill's files,
   `activation.py`, a `.mcp.json` pointed at the scratch server, run via
   `claude -p ... --permission-mode bypassPermissions --mcp-config .mcp.json
   --strict-mcp-config --output-format stream-json --max-budget-usd <N>
   --no-session-persistence`, invoked as `/curiosity` (by hand, so AC 9's marker rule
   doesn't gate it). Assert against the SCRATCH STORE and the SCRATCH `curiosity/`
   folder afterward, never the transcript's claim alone:
   - **AC 10** — the transcript names what was recalled; the recalled memory's id is
     real (fetchable via `cm get`).
   - **AC 11 / AC 12** — the new memory stored has a `create-memory:` source prefix
     (the #2 conformance marker) and its content contains a URL.
   - **AC 13** — `cm related` on the source shows a new edge with `strength < 0` to
     some target, and the new memory's content says the connection is provisional.
   - **AC 14** — `curiosity/YYYY-MM-DD.md` exists in the scratch project root, with a
     `## R1` block.
   - **AC 18** — exactly one new memory from Act 1, at most one new edge from Act 2 (a
     rejection is a legitimate zero), and the record has exactly one block.

3. **AC 15 — the null-result case.** A second scripted-agent run against a store
   seeded so Act 1 finds nothing worth chasing (or Act 2's only candidate pair fails
   the structural-isomorphism test). Assert the record says so and no new memory or
   edge was created.

4. **Update `check_curiosity.py`** (or add a sibling `check_curiosity_pass_scripted_agent.py`
   next to it, matching story #5's naming split between structural and scripted-agent
   checks) with whatever of the above can be asserted as a script rather than only a
   headless run — the scratch-store state after each run (memory count, edge count,
   file contents) is script-tier, stronger than the transcript's own claim.

Do not attempt AC 7, AC 8's behavioral half, or AC 9 this cycle unless the same
scratch setup makes one of them free to check alongside the above — if not, they wait
for a cycle built around the two invocation paths specifically (by-hand vs.
heartbeat-fired), since that needs a *second* scripted session simulating the
heartbeat's own gate, not just one pass.

Kill the scratch server when done — check the pid, never leave it orphaned running
into cycle 3.

Commit on `feature/6-curiosity`, push, write `logs/cycle-2.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

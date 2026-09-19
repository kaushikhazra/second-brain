# Assumptions

Standing inputs. May change between iterations — when one does, say so in that cycle's
Observe.

- **The source is Velasari's skill tree, on this machine.** Read, do not copy blindly:
  - `C:/Projects/ai-persona/Velasari/.claude/shared/memory/memory-shapes.md`
  - `C:/Projects/ai-persona/Velasari/.claude/skills/create-memory/SKILL.md`
  - `C:/Projects/ai-persona/Velasari/.claude/skills/read-memory/SKILL.md`
  - `C:/Projects/ai-persona/Velasari/.claude/skills/update-memory/SKILL.md`
  - `C:/Projects/ai-persona/Velasari/.claude/skills/delete-memory/SKILL.md`
- **Those files are written for one persona and one owner.** Everything that names
  Velasari, V, Kaushik, a CM memory id (`4067a9fa`, `e9eb468a`, `44808862` and the like),
  a date-stamped incident, or `cognitive-memory` is either generalised or dropped. The
  rules survive; the anecdotes that earned them do not ship. A second brain is a template:
  it has an **owner** and a **brain**, not a named person.
- **The store is synaptra, not cognitive-memory.** Tools are `mcp__synaptra__memory_*`,
  same names and same arguments. The CLI is `cm`, installed with synaptra under
  `.claude/.venv`.
  **Corrected after cycle 1, from the installed engine (synaptra 2.0.0):** an explicit
  `memory_type` on store is honoured as given; classification runs only when the type is
  omitted. `update_memory` in the engine applies a type argument. The MCP tool surface
  may not expose it. So the read-back after every store (AC 7) still matters for the
  omitted-type path and for any later version that reclassifies; and AC 19 stands as
  written, type changes go through `cm update <id> --type <type>`, which is verified to
  exist. The shapes file states the verified behaviour and marks it version-specific.
- **Reserved tags are `self-map` and `surface-map`.** They are defined here, in #2, even
  though the lists themselves arrive in #3. The shapes file carries the table; the
  holders' ids are unknown until #3 creates them, so the rule in this story is "one
  holder each, and a memory about a list takes the `-design` form".
- **Shapes file lives at `.claude/shared/memory/memory-shapes.md`.** The four skills point
  at it and restate none of it.
- **The check scripts use synaptra's Python, from the venv, and a scratch data directory
  under `C:/Projects/.tmp/second-brain-loop-2/`.** Never the live store at
  `.claude/synaptra-data`. If a check needs a running MCP server, start one against the
  scratch directory and stop it when the check ends.
- **`dream` and `heartbeat` keep their logic, and THIS story reroutes their call sites.**
  Cycle 1 read this as "untouched"; it is not. AC 23 is a criterion of #2 and cannot hold
  while those two files name `memory_store` or `memory_update`. The edit is narrow: each
  sentence that tells the assistant to call `memory_store`, `memory_update` or
  `memory_archive` directly becomes "through `/create-memory`" (or update / delete), and
  nothing else in either file changes. No restructuring, no new steps. Their full rewrite
  is #4 and #5. Do this in cycle 2 or 3, not last.
- **`CLAUDE.md`'s Synaptra section is in scope for AC 4.** Replace the *Store / Update /
  Relate* bullets with routing to the four skills; keep the tool list and the DB/install
  paragraphs.
- **Branch `feature/2-memory-shapes`, cut from `main` at ad3ec00** (after PR #9). Commit
  on the branch as you go, one commit per cycle, and push. Do not merge.
- **Nothing in this loop touches `persona.md`, `user.md`, `init-brain`, `session-start`,
  `session-end`, `local-agent` or `agent-creator`.**

- **Added after cycle 2 — how to prove a criterion the substrate does not enforce.**
  Two routes, in this order of preference:
  1. **Make it mechanism.** AC 12 (reserved tags refused) and AC 26 (short id on relate
     refused) are exactly what a `PreToolUse` hook is for. Add a hook in
     `.claude/settings.json` that inspects `mcp__synaptra__memory_store` /
     `memory_update` tag lists for `self-map` / `surface-map` and
     `mcp__synaptra__memory_relate` ids for anything shorter than a full uuid, and
     blocks the call with the rule stated. Then the check is a script that invokes the
     hook with a bad payload and asserts it exits non-zero, and with a good payload and
     asserts it passes. That fails when the hook is removed, which is the standard.
     Keep the refusal text in the skill too, so the assistant knows why it was blocked.
  2. **Scripted agent, only where mechanism is impossible.** AC 8 (a fact stored whole,
     never split) is a judgement the model makes. Prove it with one headless run:
     `claude -p` in a scratch project directory that carries only the shapes file and
     `/create-memory`, given a two-fact paragraph and a one-fact paragraph, asserting
     from the transcript that the first became two stores and the second one. Run it
     once per cycle that touches the skill, record the result as a number, and treat a
     model that fails it as a recorded number rather than a failed cycle, the way Axiom
     #75 recorded AC 15 and 16 per model.
  The hook is a settings change, so it is part of this story's artifact; commit it with
  the skill. `.claude/settings.json` exists already; add to it, do not replace it.

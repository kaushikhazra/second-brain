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
  `.claude/.venv`; `cm update <id> --type <type>` is how a type is changed, because
  `memory_update` ignores `memory_type`. Verify this against the installed synaptra before
  writing it into a skill: `cm --help`.
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
- **`dream` and `heartbeat` keep their logic.** Only their direct calls to `memory_store`
  / `memory_update` / `memory_archive` are rerouted through the four skills, so AC 23 can
  hold. Their rewrite is #4 and #5.
- **`CLAUDE.md`'s Synaptra section is in scope for AC 4.** Replace the *Store / Update /
  Relate* bullets with routing to the four skills; keep the tool list and the DB/install
  paragraphs.
- **Branch `feature/2-memory-shapes`, cut from `main` at ad3ec00** (after PR #9). Commit
  on the branch as you go, one commit per cycle, and push. Do not merge.
- **Nothing in this loop touches `persona.md`, `user.md`, `init-brain`, `session-start`,
  `session-end`, `local-agent` or `agent-creator`.**

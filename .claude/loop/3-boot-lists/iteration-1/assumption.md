# Assumptions

Standing inputs. May change between iterations — when one does, say so in that cycle's
Observe.

- **The source is Velasari's skill tree, on this machine.** Read, do not copy blindly:
  - `C:/Projects/ai-persona/Velasari/.claude/skills/session-start/SKILL.md` — steps 3, 4,
    4a are the boot lists and the handoff; the rest is that persona's own infra
  - `C:/Projects/ai-persona/Velasari/.claude/skills/session-end/SKILL.md`
  - `C:/Projects/ai-persona/Velasari/.claude/skills/session-end/verify_memory.py` — the
    boot-list half; this repo already has a conformance half from #2
- **Same generalisation rule as #2.** No named persona, owner, CM ids, dates or incidents
  ship. Rules survive as mechanism. An **owner** and a **brain**, never a named person.
- **The store is synaptra 2.0.0 over stdio, spawned per session.** There is no standing
  HTTP endpoint for the live store, and a second process on `.claude/synaptra-data` is a
  concurrency risk. So, as #2's `verify_memory.py` already does: the live session fetches
  with `memory_list` through its own connection, writes the JSON to a file, and the
  script runs over the file. Keep that shape. Extend `verify_memory.py`; do not replace
  it: it gains the two-list checks (one holder each, uuids only, count ≤ cap, every id
  resolving) beside the conformance scan it already has. Resolution of ids is done by
  the session (`memory_get` per id) and written into the same JSON the script reads.
- **Reserved tags are `self-map` and `surface-map`**, already refused on any other memory
  by `.claude/hooks/memory_guard.py` from #2. ⚠ That hook will also refuse the tag on the
  *holder* itself. The hook needs one exemption: a store or update carrying the tag is
  allowed when no other active memory already carries it, or when the id being updated
  is the current holder. Extend `memory_guard.py` for that, and extend
  `check_hooks.py` to prove the exemption and the refusal both.
- **Self map holds `identity` memories only. Surface map cap is 25, a ceiling.** `working`,
  `episodic`, `semantic` only on the surface map; that rule is enforced by the heartbeat
  in #4, not here. Here `session-start` only reports a type it did not expect.
- **The handoff is typed `episodic`** and tagged `end-of-day`, `handoff`,
  `resume-next-session`, `<YYYY-MM-DD>`. It goes through `/create-memory`, not a direct
  call (#2's AC 23 still holds after this story).
- **`session-start` keeps everything it does today that is not identity grounding or
  handoff pickup** — persona adoption, user profile, synaptra health, the heartbeat cron,
  the repair path. Replace step "ground identity via memory_self" with the two list
  fetches; replace the recall-based handoff pickup with the tag fetch. Update the
  frontmatter description to match.
- **`init-brain` is touched in exactly one place**: after the round that stores the
  persona memories, seed the self map (holding those ids) and an empty surface map, gated
  on "no active memory carries the tag". Nothing about provisioning changes.
- **Checks run against scratch stores under `C:/Projects/.tmp/second-brain-loop-3/`**, the
  same way #2's scripts did (a scratch synaptra process on its own data directory).
  Never the live store.
- **Branch `feature/3-boot-lists`, cut from `main` at c778024** (after PR #10). One commit
  per cycle, pushed. No PR, no merge.
- **Nothing in this loop touches `heartbeat`, `dream`, `curiosity`, `local-agent`,
  `agent-creator`, or the four memory skills.**

# Assumptions

Standing inputs. May change between iterations — when one does, say so in that cycle's
Observe.

- **This story EDITS the existing `/dream`; it does not replace it.** The current
  `.claude/skills/dream/SKILL.md` already carries the convergence rule, the pre-dream
  checkpoint with the row-count gate, the six acts, the interrupted-dream procedure and
  the pitfalls. Most of that is right and stays. What changes: the direct calls become
  skill calls (AC 6); the boot lists and handoff become protected (AC 7, 8); Act 5 stops
  updating a `self-learning-surface-map` prose memory, which no longer exists after #3
  and #4 (the surface map is the id-list holder and the heartbeat's to maintain; a dream
  never writes it); the refusals in AC 14, 15, 17 are added; the report in AC 11–13 is
  made explicit.
- **Velasari's dream is the reference for the intent, not the text.**
  `C:/Projects/ai-persona/Velasari/.claude/skills/dream/SKILL.md`. Read it for the
  convergence rule's shape and for what a dream must not do. Same generalisation rule:
  no named persona or owner, no CM ids, no dated incidents.
- **The `cm` CLI reaches the store how?** #4 found `cm` speaks HTTP only (`--url`), while
  this brain's synaptra runs over stdio per session. The current dream text says to set
  `SYNAPTRA_BACKEND` and `SYNAPTRA_DB` from `.mcp.json` before `cm backup create`, which
  implies backup works at the file level, not over HTTP. **Verify this in cycle 1 before
  anything else**: run `cm backup create` against a scratch data directory with the env
  set and no server running, and read the manifest. If it works file-level, the
  checkpoint stands as written. If it needs a server, the checkpoint must start a
  scratch-mode server or the skill must say the backup is taken with the MCP servers
  live, as the current fallback paragraph already does. Record which.
- **Protected ids.** The two list holders and the most recent handoff. Their ids are
  known to the session after `/session-start` (#3 fetches them). The mechanism for AC 8
  needs those ids somewhere a hook can read: choose a small JSON file under `.claude/`
  written by `session-start` (git-ignored, machine-local, rewritten each boot) unless the
  #3 sentinel already fits. Extend `memory_guard.py`; extend `check_hooks.py`.
- **The threshold in AC 7** is the one the skill states; keep it as a number in the
  skill (retrievability below 0.2, matching `memory_consolidate`'s own archive line) so
  the criterion is checkable.
- **"Active conversation" for AC 15** is: an owner message in this session within the
  last 10 minutes. State the number in the skill.
- **The heartbeat cron** is whatever `session-start` creates; the dream deletes it by
  listing crons and recreates it exactly as `session-start` defines. Prove AC 5 and AC 13
  by a headless run that asserts CronList before, during and after.
- **Checks run against scratch stores under `C:/Projects/.tmp/second-brain-loop-5/`.**
  Never the live store. A dream check that creates a backup writes it under the same
  scratch root.
- **Branch `feature/5-dream`, cut from `main` after PR #12.** One commit per cycle,
  pushed. No PR, no merge.
- **Nothing in this loop touches `heartbeat`, `session-end`, `init-brain`, `curiosity`,
  `local-agent`, `agent-creator`, or the four memory skills**, except: `session-start`
  may gain the protected-ids write (a few lines), and `memory_guard.py` plus
  `check_hooks.py` gain the AC 8 rule.

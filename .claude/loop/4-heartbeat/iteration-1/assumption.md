# Assumptions

Standing inputs. May change between iterations — when one does, say so in that cycle's
Observe.

- **The source is Velasari's heartbeat, on this machine.** Read, do not copy blindly:
  - `C:/Projects/ai-persona/Velasari/.claude/skills/heartbeat/SKILL.md` — the loop, 54 lines
  - `C:/Projects/ai-persona/Velasari/.claude/skills/heartbeat/observe.md`
  - `C:/Projects/ai-persona/Velasari/.claude/skills/heartbeat/goal.md`
- **Same generalisation rule as #2 and #3.** No named persona, owner, CM ids, dates or
  incidents ship. Rules survive as mechanism. An **owner** and a **brain**.
- **Sections that ship and sections that do not.** Velasari's observe/goal pair carries
  six ids. Ship four: `cm-capture` (rename to `capture`), `correction`, `quiet-cycles`,
  `surface-map`. Drop two: `break-due` and `timer` are one owner's habits and one owner's
  tracker, not a template's. The issue's criteria name exactly the four that ship.
- **The current SB heartbeat is replaced, not edited.** It dispatches a Haiku sub-agent,
  keeps a `self-learning-surface-map` prose memory rebuilt by domain, and stores
  continuations as its own thing. All of that goes. The new shape: the beat runs inline
  (the window only exists in the main context), the surface map is the id-list holder
  from #3 maintained by the exit test, and continuations are ordinary memories typed
  `episodic` that the capture section stores when they carry a commitment. The
  `working`-decay warning in the current file is true and stays, as one line in
  `goal.md § capture`.
- **The surface map holder is written with `memory_update` passing CONTENT ONLY, never
  `tags`.** The hook's holder exemption from #3 keys on the tag list; an update that
  omits `tags` does not touch it. Re-read `.claude/hooks/memory_guard.py` before writing
  the map step, and state in `goal.md` that the write passes content only. ⚠ AC 9 says
  no direct `memory_update` in the heartbeat folder — so the map write goes through
  `/update-memory`, whose "not for tidiness" rule has to admit this one caller: a map
  write is the maintenance the list exists for. Add that carve-out to `/update-memory`
  in one sentence.
- **The exit walk is cheap by construction**: the map's ids were fetched at boot by
  `session-start` (#3), so a beat re-reads only the ones it needs to judge closure on.
- **Quiet-cycle count lives in the session's own context**, previous beats are visible to
  the next; nothing is written to a file for it. The count resets when curiosity is not
  active (#6 will provide the activation; until then `goal.md § quiet-cycles` says: if
  `/curiosity` is not present or not active, do nothing and reset).
- **The cron interval stays whatever `session-start` sets** (30 minutes today). Not this
  story's to change.
- **Checks run against scratch stores under `C:/Projects/.tmp/second-brain-loop-4/`.**
  Never the live store.
- **Branch `feature/4-heartbeat`, cut from `main` at 6e060f1** (after PR #11). One commit
  per cycle, pushed. No PR, no merge.
- **Nothing in this loop touches `dream`, `session-start`, `session-end`, `init-brain`,
  `local-agent`, `agent-creator`, or the four memory skills**, except the one-sentence
  carve-out in `/update-memory` named above, and `CLAUDE.md`'s routing row for the
  heartbeat if its description changes.

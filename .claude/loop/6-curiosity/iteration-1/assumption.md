# Assumptions

Standing inputs. May change between iterations — when one does, say so in that cycle's
Observe.

- **The source is Velasari's curiosity, on this machine:**
  `C:/Projects/ai-persona/Velasari/.claude/skills/curiosity/SKILL.md`, 174 lines. The
  two acts (go to the root and read outside; wander by structural isomorphism and lay a
  negative-strength edge), the one-root-one-wander bound, the duplicate check at sampling
  time, the record format, and the pitfalls all ship. Everything that names the persona,
  the owner, dates, and the history of scoring is dropped; the rule "no scoring" ships
  as a rule without its story.
- **Activation is new and is this story's.** The CLAUDE.md rule (§ Issues, last
  paragraph) defines it. The record is a git-ignored JSON at `.claude/activations.json`
  holding, per habit, `{answered_at_version, active}`. `/session-start` gains one step:
  read `VERSION`, read the record, and for each habit with no entry or an entry at a
  different version, ask once with AskUserQuestion; on yes set active; on no or no
  answer set inactive and print the one-line hint; write the record. Non-interactive
  sessions (headless) count as no answer. #7 (news) will add its habit to the same
  record and the same step; design the step so a second habit is one more entry, not a
  second block of prose.
- **`/curiosity on|off|status`** is the skill's own argument handling: `on` and `off`
  write the record and confirm; `status` prints active or inactive and the version it
  was answered at. Bare `/curiosity` runs one pass by hand and says it was by hand.
- **The heartbeat hands off through `goal.md § quiet-cycles`**, which already reads
  "if present and active". "Active" means the record says so; make the sentence say
  where it reads that. One-line edit to the heartbeat's goal.md; nothing else there.
- **The record folder is `curiosity/` at the brain root**, one file per day, blocks
  numbered `## R{n}`, rejections recorded too. Add `curiosity/` to nothing in
  `.gitignore`: the owner's records are theirs to commit or not.
- **Negative-strength edges.** Velasari's CM accepts them. Verify synaptra 2.0.0 does
  (`memory_relate` with strength −0.4) against a scratch store in cycle 1 before writing
  the rule.
- **Outside reads use the session's web tools** (WebSearch, WebFetch). A headless proof
  run therefore needs network; if none, record the criterion as blocked by environment,
  not failed.
- **Checks live at `.claude/skills/curiosity/check_curiosity.py`** and use scratch
  stores under `C:/Projects/.tmp/second-brain-loop-6/`.
- **CLAUDE.md gains one routing row** for `/curiosity` and the activation step is named
  in `session-start`'s row.
- **Branch `feature/6-curiosity`, cut from `main` after PR #14.** One commit per cycle,
  pushed. No PR, no merge.
- **Nothing else is touched** beyond: `session-start` (the activation step),
  `heartbeat/goal.md` (one sentence), `.gitignore` (the record file), `CLAUDE.md` (rows).

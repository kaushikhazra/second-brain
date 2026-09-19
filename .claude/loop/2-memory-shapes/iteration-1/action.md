# Action

**Cycle 8. AC 8's scripted-agent run — the last criterion with a designed proof route.**

Cycle 7 closed AC 24 and confirmed every remaining gap is skill-judgment. Of those, only
AC 8 has an assigned mechanism (`assumption.md`'s Route 2): "one headless run: `claude
-p` in a scratch project directory that carries only the shapes file and
`/create-memory`, given a two-fact paragraph and a one-fact paragraph, asserting from
the transcript that the first became two stores and the second one."

Read the issue's criteria fresh (`gh issue view 2 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-7.md`. Re-read `assumption.md` fresh — check first
whether Velasari responded to cycle 7's flagged session-end tension; if she did,
reconcile with that before anything else this cycle.

## 1. Build the scratch project

A directory under `C:/Projects/.tmp/second-brain-loop-2/ac8-scratch-project/` (never
inside the real repo) carrying only:
- `.claude/shared/memory/memory-shapes.md` (copy of the real one)
- `.claude/skills/create-memory/SKILL.md` (copy of the real one)
- `CLAUDE.md` or equivalent minimal instruction, if `claude -p` needs one to load the
  skill at all — check whether a bare skill directory with no CLAUDE.md is enough
  before adding one; don't build more scaffold than `claude -p` actually requires.
- Its own `.mcp.json` pointing a synaptra instance at a **scratch** data directory
  distinct from `C:/Projects/.tmp/second-brain-loop-2/data` (the one cycles 2–7's other
  scratch scripts reuse) — a clean store for this run, so an old probe memory can't be
  mistaken for one this run produced.

## 2. Confirm `claude -p` actually invokes skills and MCP tools headlessly

Do not assume. A one-line smoke test first: does a bare `claude -p "hi"` in that
directory even load `.claude/skills/`? Does it connect the scratch `.mcp.json`'s
synaptra server without an interactive approval prompt blocking it forever? If
permissions or approval prompts block a headless run from ever completing, that is the
finding — record it and figure out the flag or config that unblocks it (there almost
certainly is one; check `claude -p --help` and `claude --help` for a
permission-mode/auto-approve flag before assuming this is a dead end).

## 3. Run it twice

- **Two-fact paragraph**: a short prompt containing two independently-recallable facts,
  asking the assistant to remember it. Expect `/create-memory` to produce two stores
  (per the shapes file's own fact rule: "If it contains two facts that could be recalled
  independently, it is two memories").
- **One-fact paragraph**: a comparable prompt with exactly one fact. Expect one store.

After each run, query the scratch synaptra store directly (`cm list --state active`)
rather than trusting the transcript alone — the actual stored count is the ground
truth, the transcript is corroborating evidence.

## 4. Record the number, whatever it is

Per `assumption.md`: "treat a model that fails it as a recorded number rather than a
failed cycle." If the two-fact case produces one store, or three, that is the finding —
write it down plainly in `logs/cycle-8.md`, do not retry until it produces the expected
number, and do not treat a genuine miss as this cycle having failed. The loop's job is
to find out, not to make AC 8 pass by construction.

## 5. Commit, push, log, write cycle 9's action.md, exit

If this genuinely can't run headlessly in one cycle (step 2's smoke test fails and no
quick fix is found), say so plainly, record what was tried, and leave AC 8 in the
unproved list with a clearer reason than before — that is still real progress on the
question, even without a passing number. Do not spend a second cycle re-attempting the
same blocked approach without a new idea.

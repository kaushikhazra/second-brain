# Observe

## Order matters

**Read the criteria from GitHub first** — `gh issue view 8 -R kaushikhazra/second-brain` —
before the diff and before the previous cycle's log. Attack each criterion; do not confirm
it. The criteria drive the cycle.

## The measurement

The number this loop moves is **criteria demonstrably met, out of 12.** Demonstrably means
a check that fails when the behaviour is removed.

This story is mostly a script, so most criteria are provable by a plain test: build a
scratch transcript directory shaped like `~/.claude/projects/<encoded-root>/` with a few
synthetic JSONL sessions, run the script against it, assert the output. The proof standard
is unchanged; the headless-run route should be needed for at most one or two criteria
here, if any.

## Every cycle, record

- **Criteria met, out of 12**, by number, in three buckets. Only the first counts.
- How far the number moved, and what moved it.
- The full regression line: `check_shapes.py` · `check_hooks.py` · `check_session_start.py`
  · `check_verify_memory.py` · `check_heartbeat.py` · `check_dream.py`. All pass.
- Any assumption that changed.
- The branch, read from git.

## The five that will be got wrong

- **AC 1 and AC 8 — this project only.** Velasari's source script searches every
  project under `~/.claude/projects/`. This one must resolve the brain root (walk up to
  the directory holding both `.claude/` and `CLAUDE.md`, the way `session-start` step 0
  does), encode it the way Claude Code names transcript directories, and search only
  that directory. Prove by seeding two project directories in the scratch tree and
  showing the other one is never read: assert by output AND by a file-access trace
  (e.g. the script logs which files it opened in a verbose mode).
- **AC 2 — newest first.** Prove with three seeded sessions of known timestamps.
- **AC 5 — an invalid regex is reported with the error and nothing is searched.** Prove
  with `(` as the pattern and assert the error text and zero files opened.
- **AC 9 — reads and writes nothing.** Prove by hashing the scratch tree before and after
  a run and by asserting no file is created anywhere under the brain root.
- **AC 10 — works with synaptra unreachable.** The script imports nothing from synaptra
  and the skill calls no memory tool. Prove by running the script with the venv absent
  from PATH and with a broken `.mcp.json` in the scratch project.

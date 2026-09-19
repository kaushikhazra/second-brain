# Action

**Cycle 1. Baseline, the encoding, the script scoped to this project, and the first
checks.**

Record the baseline in `logs/cycle-1.md`: the branch; the real transcript directory name
for this brain under `~/.claude/projects/` (read it, do not guess); the regression line.

Then, in this order:

1. **Port the script.** `.claude/skills/recall-session/tools/search.py` from Velasari's,
   with: a `brain_root()` that walks up; an `encode_root()` with the verified encoding;
   `PROJECTS_DIR` narrowed to that one directory; a `--verbose` flag that prints each
   file opened; an explicit error for an invalid regex before any file is touched; an
   explicit message naming the directory when it does not exist; a parse failure that
   names the file and continues. Keep the search, context, limit, slice and role logic
   as they are.

2. **The skill.** `SKILL.md` with the invocation resolved from the skill directory, the
   defaults stated, the two modes, and the "call memory recall first" rule kept as a
   sentence.

3. **`check_recall_session.py`.** Build the scratch tree with three sessions of known
   dates in this brain's encoded directory and one session in a second, decoy directory.
   Assert: matches come back newest first (AC 2); the decoy is never opened (AC 8, via
   `--verbose`); no match says so and names the directory (AC 4); `(` is reported and
   opens nothing (AC 5); a missing directory is named (AC 11); a corrupt JSONL line is
   named and the other sessions still match (AC 12); the tree's hash is unchanged after a
   run (AC 9).

Commit on `feature/8-recall-session`, push, write `logs/cycle-1.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

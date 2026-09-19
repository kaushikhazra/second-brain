# Assumptions

Standing inputs. May change between iterations — when one does, say so in that cycle's
Observe.

- **The source is Velasari's `recall-session`, on this machine:**
  `C:/Projects/ai-persona/Velasari/.claude/skills/recall-session/SKILL.md` and
  `tools/search.py`. The script is good; its two defects for a template are: it searches
  ALL projects (this story scopes it to one), and the skill invokes it by a frozen
  absolute path (this story resolves the script relative to the skill's own directory).
  Same generalisation rule as before: no named persona or owner.
- **Transcript location.** Claude Code writes session JSONL files under
  `~/.claude/projects/<encoded-root>/`, where the encoding replaces path separators and
  the drive colon with `-` (observed on this machine: `C--Projects-second-brain` for
  `C:\Projects\second-brain`). Verify the exact encoding against the real directory for
  this brain before writing it into the script, and make the encoding a single function
  with a test.
- **Brain root resolution.** Walk up from the current directory to the first directory
  holding both `.claude/` and `CLAUDE.md`. Never hardcode.
- **Python.** The script runs on the brain's own venv Python
  (`.claude/.venv/Scripts/python.exe`) or any Python 3.12+; it imports only the standard
  library. The skill states how it is invoked without a frozen path: `python
  <skill-dir>/tools/search.py`, with `<skill-dir>` resolved at runtime.
- **Defaults stated in the skill:** context 2 turns before and after; limit 20 matches;
  excerpt capped at 40 lines. AC 3 requires the default to be stated; keep Velasari's.
- **AC 7's listing of existing sessions** is by session id and date, newest first, and
  is the same listing the no-match case can offer.
- **Checks live at `.claude/skills/recall-session/check_recall_session.py`** and build
  their scratch transcript tree under `C:/Projects/.tmp/second-brain-loop-8/`. They never
  touch `~/.claude/projects/` for real.
- **CLAUDE.md gains one routing row** for `/recall-session`.
- **Branch `feature/8-recall-session`, cut from `main` after PR #13.** One commit per
  cycle, pushed. No PR, no merge.
- **Nothing else is touched.** No memory skill, no heartbeat, no dream, no session skills.

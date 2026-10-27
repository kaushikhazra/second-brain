# Cycle 1 — #83

**Reproduced on 1.6.1.** With `CLAUDE_CONFIG_DIR` set and a transcript under it, search.py looked only in
`~/.claude/projects/`: 5 of 6 criteria failed (the sixth was already true).

**Fix.** `resolve()` in `search.py` uses `$CLAUDE_CONFIG_DIR/projects` when the variable is set and non-empty,
else `~/.claude/projects`. SKILL.md says so.

**Criteria held: 6 of 6** (`checks/recall-session/check_config_dir.py`); 3 removals each fail their named
ACs. Regression: check_recall_session 12/12.

**Accepted, not fixed.** The layout under `CLAUDE_CONFIG_DIR` is taken from `brain-claude-sandbox.bat`'s
use of it and Claude Code's documented behaviour; not checked against a live transcript there.

# Assumptions — #83

- With `CLAUDE_CONFIG_DIR` set, Claude Code keeps transcripts at `<it>/projects/<encoded cwd>/` (the same
  layout as `~/.claude/projects/`). `brain-claude-sandbox.bat` already sets it.
- Fail-safe deadline: one cycle.

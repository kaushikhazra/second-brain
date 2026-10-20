# Assumptions — #75

- Hooks run under Git bash on Windows (the existing `$CLAUDE_PROJECT_DIR` syntax already depends on it).
- Both guards are stdlib only.
- `.claude/.venv` is rebuilt by update and move repair; `.claude/.python` persists.
- Fail-safe deadline: one cycle.

# Cycle 1 — #75

**Reproduced on 1.6.1.** `python` off PATH, the settings.json hook command exits 127 —
a non-blocking error — so the guard never runs and the tool call proceeds.

**Fix.** `src/.claude/hooks/run_guard.sh` starts the guard on `.claude/.venv`, else the
standalone interpreter under `.claude/.python`, found from the script's own location.
No interpreter: stderr names the guard, exit 1 (a visible hook error). settings.json now calls
`sh "$CLAUDE_PROJECT_DIR/.claude/hooks/run_guard.sh" <guard>.py`. `.gitattributes` pins `*.sh` to LF.

**Criteria held: 7 of 7** (`checks/guard/check_guards_own_python.py`); each of 4 removals
(bare python back in settings, no standalone fallback, hardcoded brain path, silent exit 0) fails
its named AC. `$CLAUDE_PROJECT_DIR` expansion under Git bash is proved by the same run, launched
from another cwd.

**Not green, unrelated:** `guard/check_guard.py` AC 8 (release notes vs absent scorecard) fails;
11 of 12 hold. It reads no file this change touched.

**For Kaushik.** The repo's own `.claude/settings.json` SessionStart hook still uses bare `python`
(development repo, not the product). The check relies on Git bash; a PowerShell-shelled hook
would not expand `$CLAUDE_PROJECT_DIR` — same as before.

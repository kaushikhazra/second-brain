# Cycle 1 — #49

**Result: 5 of 5 criteria held.** Check: 6 PASS (AC 1-5, cap/redact). Removal demos:
all 6 make the check FAIL.

**Change:** `open_issues` returns `(issues, cause, error_line)`; `error_line` takes the
first non-empty stderr line, scrubs token-shaped strings, caps at 200 chars, and says
`(no error output)` when empty. `cmd_issues` prints `ERROR: <line>`; told-once stays keyed
on the cause. SKILL.md and heartbeat goal updated.

**Not run:** `check_monitor.py` (needs a scratch brain and live agents); only
`py_compile` on the changed script plus the new check.

## For Kaushik

- AC 1 says the line is "unaltered"; the orchestrator's instruction (cap ~200 chars, strip
  credentials) alters it in those two cases only. Normal lines pass through as printed.
- Failure causes from exceptions (`OSError`/timeout) use the exception text as the line.
- The NOT_SIGNED_IN pre-check (no credentials, no `gh` call) has no tool output, so it
  reports `(no error output)`.

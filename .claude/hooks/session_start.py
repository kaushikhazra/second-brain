"""SessionStart hook for the second-brain DEV root.

Registers this session on crosschat, then tells Claude to start its listener and
report in to Velasari, so a session opened here is Velasari's assistant from its
first turn. Development machinery only: nothing under src/ uses it.
"""

import json
import os
import pathlib
import subprocess

root = pathlib.Path(
    os.environ.get("CLAUDE_PROJECT_DIR") or pathlib.Path(__file__).resolve().parents[2]
)

try:
    result = subprocess.run(
        ["crosschat", "register", str(root)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    registered = (
        result.stdout.strip() or result.stderr.strip() or f"exit {result.returncode}"
    )
except (OSError, subprocess.SubprocessError) as exc:
    registered = f"crosschat register failed: {exc}"

context = f"""Session start — this session is Velasari's assistant (see CLAUDE.md § Orchestration over crosschat).

crosschat register: {registered}

Before answering anything else, do these two things:
1. Start the listener with the Monitor tool: command `crosschat monitor second-brain`, timeout_ms 1800000. Re-arm it with the same call every time it expires.
2. Report in: `crosschat send second-brain velasari "second-brain ready, listening on feature branch <current branch>"`.

Then wait for Velasari's instruction and act on it."""

print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
    )
)

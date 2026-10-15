# Action

Backlog item 4 (cycle 6): prove the structural criteria with checks that fail when the behaviour is removed. Put them in `guard/` (or `checks/` style if the repo has one for hooks; look at `checks/` first), one script `guard/check_guard.py`, exit non-zero on any failure, printing PASS/FAIL per AC.

- **AC 1**: read `src/.claude/settings.json`; assert a PreToolUse entry whose matcher covers both `Bash` and `PowerShell` and whose command runs `command_guard.py`. Then run the hook as a subprocess with a PreToolUse JSON payload for `tool_name: Bash` and for `tool_name: PowerShell`; both must return a `permissionDecision`. Shown to fail by: removing the matcher entry, and by a payload for another tool returning nothing.
- **AC 3**: a plainly safe command (`ls`, `git status`) returns `allow`.
- **AC 4**: a plainly risky command (`rm -rf /var/www`) returns `deny`, and the reason names the question tripped (delete/overwrite/production/exfil wording from `SAYS`).
- **AC 5**: an install (`pip install requests`) returns `ask`.
- **AC 6**: run the hook as a fresh process 20 times; assert median wall time under a stated bound (measure first, then pick the bound; record the number) and that it imports only stdlib (`python -I -X importtime` or inspect `sys.modules`; no numpy/sklearn/torch).
- **AC 7**: assert `guard/generate.py` draws from no file outside the repo (no `commands.jsonl`, no `~/.claude`), and that no file under the repo contains a path with `cmd-guard-dataset`. Removing-the-behaviour demo: a temporary generator line reading the owner file must fail the check.

For each, run the check, then break the behaviour once and confirm the check fails; record both in the log. Commit and push. Report the count to velasari.

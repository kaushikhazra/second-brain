# Action

Cycle 1's constraint: AC 1 fails because the brain has no rule for where projects go — it cloned beside itself.

Build the `manage` skill: `src/.claude/skills/manage/SKILL.md` and `scripts/projects.py` (clone / list / locate, brain root resolved from the script's own location). Route it from the Session Lifecycle table in `src/CLAUDE.md` and add `projects/` to `src/.gitignore`. The clone reports path and default branch, refuses to re-clone, and removes any partial folder on failure with a message distinct per cause (unreachable, no access, not a git repo).

Then extend `checks/multi-project/check_clone.py` with modes for AC 2 (reply names path + default branch), AC 3 (`git status` of the brain shows nothing under `projects/`), and AC 4 (second request for the same URL: no re-clone, reply names the path). Check whether this machine has a GitHub SSH key (`ssh -T git@github.com`) for AC 1's SSH half. Run every mode fresh.

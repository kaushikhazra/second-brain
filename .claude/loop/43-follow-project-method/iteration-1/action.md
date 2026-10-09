# Action

AC3 and AC5 on beta (no method), and the product text AC4 needs a footing for.

Product, in `src/.claude/skills/manage/SKILL.md` (a section before *Code host and issue tracker*): (a) the method — a project's own wins; where its record states none, loop engineering: the issue's criteria are the goal and the loop lives in the project's `.claude/loop/{issue}-{slug}/`, never the brain's; (b) the branch — work only on a feature branch in the project, cut from its default branch, never commit to the default branch, never merge, the owner merges; (c) closing — a comment on the issue in the project's tracker saying *N of N criteria met* and what proved each.

Checks in `check_method.py`, mode `loop` (AC3): beta #1 with a yes — `projects/sb-sandbox-beta/.claude/loop/1-<slug>/` exists with the goal holding the issue's criteria, and the brain's own `.claude/loop/` stays empty. Mode `close` (AC5): after the work, the beta issue carries a comment matching `N of N criteria met` with a line per criterion saying what proved it; the check removes its own comment afterwards. Beta only: no other repo is touched.

Removal demos in `demo_method_removals.py`: ac3 (loop forced into the brain's folder), ac5 (no comment at all). Extend ac4 to cut the new branch rule too.

Then one full regression pass — `src/` changes this cycle: `check_diligence.py --all`, `check_clone.py --all`, `check_context.py --all`, `check_tracker.py --all`, `check_monitor.py --all`, and `check_method.py --all`.

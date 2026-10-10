# Action

BUILD-ONLY mode is in force (`../../queue.md`, *BUILD-ONLY mode*): **no `claude -p`**, script checks only, behaviour-pending criteria listed and not counted.

What exists: the skill section *Doing the work on an issue* in `src/.claude/skills/manage/SKILL.md` (method, loop in the project's `.claude/loop/{issue}-{slug}/`, feature branch and never merge, the closing comment *N of N criteria met*), and the brain-spawning checks `check_method.py` / `demo_method_removals.py` — do not run them.

Do now, one cycle:
1. Read issue #43 and decide, per criterion, whether a script check can prove it without a brain. AC1 (the brain tells the owner the method), AC2 (follows the project's method), AC3 (loop in the project), AC4 (feature branch, never merges), AC5 (the closing comment) are all behaviours of a brain; the skill text is their only product. Where the product has a script-checkable half (e.g. the learned record's method line that AC1 and AC2 read from), write `checks/multi-project/check_method_static.py` — plain Python asserts on `src/`, no LLM — that fails when that text or line is removed. Do not assert on what the brain says.
2. Run that check (no spawn), plus the earlier **script-only** checks if any exist; do not run any check that calls `claude`.
3. Mark #43 DONE-build in `../../queue.md` with AC1–AC5 each listed as proven-earlier-by-brain-run (cycle 1–2 evidence for AC1, AC2, AC4) or behaviour-pending (AC3, AC5, and AC4's re-run on the new skill text). Comment on GitHub issue #43 listing the behaviour-pending criteria; leave it **open**. Report to velasari.
4. Then #44 next cycle, from its own `loop.md`.

# Action

AC1 is met. Take AC2 and AC4 together, both on alpha: the owner says yes to alpha #1, and the check inspects the project afterwards. AC2 — spec files (requirement, design, task) exist under `.claude/specs/` and were written before any change under `src/` (compare commit order or file times), and no `.claude/loop/` folder was created in alpha. AC4 — all work is on a feature branch in alpha (never `main`), `main` is untouched, and nothing was merged (no merge commit anywhere, the feature branch not folded into `main`).

Alpha already carries `feature/1-*` branches from #42's runs: have the check delete them on the remote first and create its own branch names unmentioned. Then removal demos for AC2 and AC4 (replace the rule with its opposite, as in #42).

Then AC3 and AC5 on beta (no method): the loop in `projects/sb-sandbox-beta/.claude/loop/{issue}-{slug}/` with the issue's criteria as the goal, and the closing comment *N of N criteria met* on the beta issue with what proved each. These need product changes in `manage/SKILL.md`; read what the brain did on its own before writing them.

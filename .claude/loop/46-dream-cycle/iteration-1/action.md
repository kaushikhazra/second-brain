# Action — cycle 4

Constraint from cycle 3: 8/11. `/dream-cycle` does not exist; AC 4, 9, 10 need it, and AC 1-3
need an owner-facing command.

1. Read `gh issue view 46` (criteria) first.
2. Write `src/.claude/skills/dream-cycle/SKILL.md`: subcommands `on`, `off`, `size <n>`,
   `status`, and the run itself (`requested by heartbeat` or by hand). The run: load or
   refresh the day's plan (`dream_cycle.plan_is_stale`; refresh with
   `memory_consolidate(dry_run=true)`), take `next_batch`, apply each `promote` through
   `/update-memory` (type change) and each `archive` through `/delete-memory` (archive),
   skip boot-list ids and the current handoff and report them, `mark_applied`, then
   `record_cycle` and write one log entry. Archive, never delete. No backup (Kaushik).
   Refuse while the owner is in conversation. Hand and heartbeat runs count the same.
3. Add the skill to `src/CLAUDE.md`'s lifecycle table and structure table.
4. Extend the check: SKILL.md exists, names the three subcommands plus run, never calls
   `memory_delete`/`memory_store`/`memory_update` directly, never mentions a backup step.
5. Record criteria met out of 11, commit and push, report on crosschat.

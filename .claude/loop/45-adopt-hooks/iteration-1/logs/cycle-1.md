# Cycle 1 — 2026-10-09 ~16:57–17:25 +0530 — DONE-build (build-only mode)

**Branch:** `feature/multi-project`. Issue #45 read first: 5 criteria, issue open.
**Mode:** BUILD-ONLY (`../../queue.md`): no `claude -p`, script checks only.

## How the brain's hooks are registered (read first)

`src/.claude/settings.json` carries the brain's own hooks (one `PreToolUse` guard,
`memory_guard.py`, command rooted at `$CLAUDE_PROJECT_DIR`). A project's hooks live in
its own `.claude/settings.json` / `settings.local.json`, in the same shape; #39's
`hooks_of` already lists them for the learned record.

## Decision: where an adopted hook goes

The brain's **`.claude/settings.local.json`** — machine-local, so a brain update that
replaces the shipped `settings.json` leaves it alone, like `projects/` and the per-project
records. The hook's command is rewritten to start from `$CLAUDE_PROJECT_DIR` +
`projects/<name>/` (an absolute path of the project or of the brain becomes the same),
so it follows the brain folder through a rename or move. What was adopted is remembered
in `.claude/projects/adopted-hooks.json`; the settings entry is found again by event,
matcher and command.

## Action taken

**Product**
- `src/.claude/skills/manage/scripts/projecthooks.py`: `list <project>` (numbered,
  read-only), `adopt <project> <n>`, `adopted`, `remove <id>`. A hook with the same event,
  matcher and command as one the brain already has is `DUPLICATE`; the same event and
  matcher with a different command is `CONFLICT`; both are reported with the existing
  hook and add nothing. `ADOPTED` prints `APPLIES_TO: every project in this brain`.
- `projects.py`: `hook_entries` factored out of `hooks_of` so both read a project's hooks
  one way; `hooks_of` prints what it always did.
- `manage/SKILL.md`: section *A project's hooks*; the take-in line now says hooks stay
  "not adopted" until the owner names one. `src/CLAUDE.md` routing row and the skill
  description cover listing, adopting and removing hooks.

**Check** — `checks/multi-project/check_hooks.py` (no brain, no LLM): drives the script
in a small brain (`C:/Projects/.tmp/second-brain-loop-45/`) with a settings file carrying
one brain hook and a project carrying three. AC5 expands `$CLAUDE_PROJECT_DIR` to the
renamed brain the way Claude Code does when a hook fires, and runs the adopted command:
it exits 0 and writes its log under the renamed folder. Seven static wiring rules on the
skill text. `--self-test` mutates the script once per behaviour and removes each wiring
rule.

## Observation

```
check_hooks.py            23/23 pass  (16 script scenarios + 7 wiring rules)
check_hooks.py --self-test 14/14 removals noticed (7 script mutations + 7 wiring)
check_queue.py            30/30 pass  (rerun: projects.py changed)
check_method_static.py    13/13 pass  (rerun: the manage skill changed)
```

Every mutation fails the criterion it targets; some also fail neighbours that depend on
it (a hook that is never written breaks the later steps), which is expected.

## Numbers

| AC | Proven by script | Behaviour-pending |
|----|------------------|-------------------|
| 1 | `list` shows the three hooks numbered, adopted: no; nothing is written; #39's record lines unchanged | a brain lists on request and never adopts unprompted (a brain run proved the "not adopted" half for #39 on older text) |
| 2 | `adopt` adds to `settings.local.json`, prints `APPLIES_TO: every project in this brain`, command rooted at `$CLAUDE_PROJECT_DIR/projects/<name>` | a brain says it plainly, in its words |
| 3 | `adopted`, `remove` take it out and leave the others; unknown id refused | a brain removes on request |
| 4 | duplicate and conflict reported, nothing added, file byte-identical | a brain reports them and does not add another way |
| 5 | no absolute brain path in the settings; after the folder is renamed the adopted command, with `$CLAUDE_PROJECT_DIR` expanded, runs and writes under the new folder | Claude Code itself firing it in a live session after a rename |

- **DONE-build: yes.** Counted by the loop: none of the five as *met* (each has a brain
  or live-session half pending); the script half of all five is proven.
- GitHub issue #45 left **open**, with a comment listing the pending halves.
- Regressions: no brain run (build-only). `src/` changed again: **#38–#44's brain
  regression is owed** on the final skill text.

## For Kaushik

- **Conflict means same event and same matcher, different command.** Claude Code allows
  several hooks on one event and matcher; the issue says a conflict is reported, not
  added, so the stricter reading is the one built. The owner can remove the other first.
- **Adopted hooks run from the project's folder** (`projects/<name>/.claude/hooks/…`),
  they are not copied. If the project is deleted, the adopted hook stops working, and
  Claude Code will report the failing command. `remove` takes it out.
- **A rewritten absolute path** covers the project's folder and the brain's folder in
  either slash style. A path outside both (a tool in `C:\tools`) is kept as written; it
  does not move with the brain, and the script does not warn about it.
- The `settings.local.json` write keeps whatever else the file holds (permissions); it
  replaces the file whole via a temp file, so a crash leaves the old one.

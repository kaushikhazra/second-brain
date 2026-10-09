# Cycle 1 — 2026-10-09 ~16:42–16:55 +0530 — DONE-build (build-only mode)

**Branch:** `feature/multi-project`. Issue #44 read first: 5 criteria, issue open.
**Mode:** BUILD-ONLY (`../../queue.md`): no `claude -p`, script checks only.

## Decision: where the queue persists

`<brain root>/.claude/projects/queue.json` — machine-local, beside the per-project
records (`.claude/projects/<name>.json`) that #39–#42 already keep there. Found from the
script's own location (`projects.brain_root()`), so renaming the brain leaves it found.
Written whole to a temp file and swapped in (`os.replace`), so a session ending
mid-write leaves the previous queue.

## Action taken

**Product** (what #44 asks for, as written):
- `src/.claude/skills/manage/scripts/workqueue.py`: `add`, `list [--all]`, `move`,
  `remove`, `finish`, `stop`, `recover`. One `active` item at most, across every
  project; waiting items in approval order; finish / stop / remove of the active item
  starts the first queued one; `recover` turns an item still `active` at the start of a
  session into `interrupted`, prints an `INTERRUPTED:` line for it, keeps it on the
  list, and moves on. (Named `workqueue.py`, not `queue.py`: a script called `queue`
  in a folder on `sys.path` would shadow the standard library's `queue`.)
- `manage/SKILL.md`: section *The work queue* (what each status means for the brain);
  the yes step now puts the item on the queue and begins only if it starts.
- `session-start/SKILL.md`: step 6a runs `recover` and has the brain say each cut-off
  item in the report.
- `src/CLAUDE.md` routing row and the skill description: viewing, reordering or
  removing queue items route to `/manage`.

**Check** — `checks/multi-project/check_queue.py` (no brain, no LLM): drives the script
one process per command in a small brain under `C:/Projects/.tmp/second-brain-loop-44/`
(the two scripts from `src/`, the `CLAUDE.md`/`.claude/` marker, two git folders as
projects), plus static wiring rules on the two skill files. `--self-test` mutates the
script once per behaviour and removes each wiring rule, and requires the check to fail.

## Observation

```
check_queue.py            30/30 pass  (19 script scenarios + 11 wiring rules)
check_queue.py --self-test 19/19 removals noticed (8 script mutations + 11 wiring)
check_method_static.py    13/13 pass  (rerun: the manage skill changed again)
```

One check of mine was wrong, not the script: after the first `recover` the next item had
started, so a second `recover` in the same breath rightly marked *that* one interrupted
as well. "Reported once" is now tested after the running work has ended, and shows the
old interrupted item is not reported again.

## Numbers

Script-proven: the **mechanics** of all five criteria.

| AC | Proven by script | Behaviour-pending (needs a brain) |
|----|------------------|-----------------------------------|
| 1 | one active across projects; a second add never starts while one runs | a brain never starts work while another item is active |
| 2 | queued items in approval order; same issue not queued twice | — |
| 3 | list shows project / issue / state; move; remove; running item immovable | a brain shows the owner the queue and acts on "move that up" |
| 4 | finish, stop and remove-of-active each start the next | a brain begins the item that started |
| 5 | state survives separate processes and a renamed brain; interrupted reported once and kept | a brain runs `recover` at boot and tells the owner |

- **DONE-build: yes.** Not counted as met by the loop: AC1, AC3, AC4, AC5 each have a
  brain half still pending; AC2 is fully a script behaviour and is proven.
- GitHub issue #44 left **open**, with a comment listing the pending halves.
- Regressions: none run (build-only). `src/` changed: #38–#43's brain regression is owed.

## For Kaushik

- `recover` treats "still active at session start" as "cut off". That is right for one
  brain on one machine, which is what #44 states; two live sessions on one brain folder
  would mark each other's running item interrupted.
- An interrupted item is not auto-restarted: the queue moves on and the item is listed as
  `interrupted` until the owner re-approves it (`add` again) or removes it. Restarting a
  half-done build without asking seemed the worse default; the criterion only asks that
  it be reported and not lost.
- `remove` on the running item stops it (kept as `stopped`, reason "removed by the
  owner") and starts the next. The issue says "remove items"; this is the reading that
  leaves one active at a time.

# Action

**Cycle 6. The `PreToolUse` hook for AC 12 and AC 26 — `assumption.md`'s Route 1.**

Cycle 5 finished the four skills, the shapes file, and `CLAUDE.md`'s routing (AC 1–4,
23 all pass by script). What's left splits into: skill-judgment criteria needing either
a mechanism (AC 12, AC 26 — this cycle) or a scripted-agent run (AC 8, and arguably AC
5/11/13/15 — a later cycle), and AC 24 (session-end's conformance scan — untouched,
also a later cycle). This cycle does exactly one thing well rather than three things
thinly: the hook.

Read the issue's criteria fresh (`gh issue view 2 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-5.md`. Re-read `assumption.md` fresh — its post-cycle-2
addendum is the spec for this cycle; re-read it rather than working from memory of it.

## 1. Confirm the hook mechanism before writing one

Do not assume `PreToolUse` hooks work the way a general Claude Code doc might describe
them without checking this project's own setup. `.claude/settings.json` currently has
no `hooks` key at all (confirmed cycle 5) — this is a genuinely new addition, not an
edit to something existing. Find a real example in this machine's other Claude Code
projects or the product docs before writing the schema from memory; a wrong hook
schema that silently fails to fire is worse than no hook, because the check script
would then be validating a hook that never runs against the real tool calls.

## 2. Write the hook

Two checks, one hook (or two hooks — decide based on what the schema actually
supports):

- **AC 12**: on `mcp__synaptra__memory_store` or `mcp__synaptra__memory_update`, if the
  call's `tags` includes `self-map` or `surface-map`, block it and state the rule
  (`-design` suffix exists for a reason to write about the list).
- **AC 26**: on `mcp__synaptra__memory_relate`, if `source_id` or `target_id` is
  shorter than a full uuid (36 chars, hyphenated), block it and state the full-uuid
  rule.

Keep the refusal text in `/create-memory` too (already there) — the hook is the
backstop, not the only place the rule is stated, same relationship AC 23's conformance
scan (AC 24) will have to the skills once that's built.

## 3. Prove it with a script that invokes the hook directly

Per `assumption.md`: "the check is a script that invokes the hook with a bad payload
and asserts it exits non-zero, and with a good payload and asserts it passes." Write
`.claude/shared/memory/check_hooks.py` (stdlib, no synaptra import needed — this tests
the hook script itself, not a live store) with one bad/good pair per criterion.

## 4. Run `check_shapes.py` too

Confirm nothing regressed (it shouldn't — this cycle doesn't touch skills or
`CLAUDE.md`).

## 5. Commit, push, log, write cycle 7's action.md, exit

If AC 12 and AC 26 both land and prove out, the number should move to 16/27. Next
cycle's candidates, to weigh with fresh eyes rather than decided here: AC 24 (the
session-end conformance scan — concrete, no new mechanism type needed) or the
scripted-agent run for AC 8 (and possibly bundling AC 5/11/13/15 into the same headless
run, since `assumption.md` describes one run per cycle that touches the skill, not one
run per criterion).

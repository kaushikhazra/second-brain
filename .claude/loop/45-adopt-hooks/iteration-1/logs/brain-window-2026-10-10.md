# Brain-run window — 2026-10-09 23:17 – 2026-10-10 00:05 +0530 (#45, and the regression pass)

Second window, strictly one `claude -p` at a time, foreground or a single background chain.
`rl-status.json`: 2% at the start, 26% at the end.

## #45 — brain and live halves (new: `check_hooks_brain.py`)

Scratch brain from `src/` with `sb-sandbox-alpha` cloned into `projects/` (it carries one
`SessionStart` hook, `mark_session.py`).

```
list      AC1 PASS  names mark_session / SessionStart; brain settings unchanged; no local settings, no registry
adopt     AC2 PASS  command 'python "$CLAUDE_PROJECT_DIR/projects/sb-sandbox-alpha/.claude/hooks/mark_session.py"'; says it applies to every project
remove    AC3 PASS  settings and registry emptied on request
dup       AC4 PASS  asked twice -> reported as already there, file byte-identical
conflict  AC4 PASS  brain already has a SessionStart hook -> reported, nothing added
live      AC5 PASS  brain folder renamed after adopting; a real `claude -p` session in the renamed folder
                    fired it: .tmp/alpha-hook-fired.log = '2026-10-09T23:20:27 alpha hook fired'
```

Removal demos (`demo_hooks_brain_removals.py`), each cutting skill text and/or script:

```
list      FAIL when cut   (listing adopts: settings.local.json and registry appear)
adopt     FAIL when cut   (says_every_project=False)
remove    FAIL when cut   (hook and registry entry remain)
dup       FAIL when cut   (file changed; after hiding `adopted: yes` from the listing too)
conflict  FAIL when cut   (hook added, no conflict reported; after adding "adopt at once, do not compare")
live      FAIL when cut   (command written with the absolute path: log_exists=False after the rename)
```

Two demos passed at first because the brain behaved well on its own — `dup` saw `adopted:
yes` in the listing and stopped; `conflict` read the brain's settings and declined. Both
were repeated with the route that let it stop taken away, as in #42.

## Regression of #38–#42 on the final skill text (one pass)

```
#38  7/7   check_clone.py --all     (AC5 failed first: see below)
#39  6/6   check_context.py --all
#40  6/6   check_tracker.py --all
#41  7/7   check_monitor.py --all
#42  5/5   check_diligence.py --all  (6 modes)
```

**#38 AC5** failed on the first run, and the product was fine. The brain wrote "I couldn't
reach the host, so the project wasn't taken in …"; the check's `lead_paragraph` looks for
the first paragraph mentioning take / taking / clone / `projects/`, did not recognise
"taken", and judged the second paragraph instead. `taken` added to that heuristic; the
curly apostrophe is allowed in the three failure patterns as well. Re-verified on the same
stored events: pass. No product change.

## Numbers

- **#45: 5/5**, each with a brain or live run that passes and a removal demo that fails;
  the script half is `check_hooks.py` (23/23, 14/14 removals noticed).
- Regression: **#38–#42 hold** on the final text.

## For Kaushik

- **Side effect found and cleaned:** with #43's closing-comment rule in the skill, the
  `yes` run of #42's check made the brain post a "2 of 2 criteria met" comment on
  `sb-sandbox-alpha` #1 — three of them over the day. Deleted (they were the loop's); the
  sandbox issues #1 and #2 on both repos are open and comment-free, as seeded. #42's check
  does not delete what the brain posts; it will add one again next run.
- Sandbox remotes still carry nine `feature/*` branches on alpha and two on beta; the
  `protected_branch_guard` hook blocks deleting them from here.
- Adopting a hook leaves it **running from the project's folder** (see cycle 1's notes).

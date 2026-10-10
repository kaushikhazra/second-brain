# Cycle 3 — 2026-10-09 ~13:45–14:40 +0530 — GOAL MET

**Branch:** `feature/multi-project`. Issue #42 read first: 5 criteria, unchanged.

## Action taken

- `check_diligence.py`: new mode `changed` — the recorded `updated_at` for alpha #2 is
  moved back (the tracker moving on is simulated; the sandbox issue is shared), a fresh
  session raises the issue again, and the brain must walk it through and ask to start,
  with nothing created.
- `demo_diligence_removals.py`: demo `ac3c` — `CHANGED_SINCE` forced to `no` in the script
  and the skill told to stay quiet whatever has changed.
- Full pass, once.

## Observation

```
full pass   present PASS   no PASS   again PASS   changed PASS   vague *   yes PASS
removal     ac3c FAIL  (walked_through_again=False)
earlier     ac1 ac2 ac3a ac3b ac4 ac5 all FAIL when cut (cycle 2)
regression  #38 #39 #40 #41 — run in cycle 2 after the last change to src/; src/ not
            touched since (git status: only checks/ changed)
```

\* vague failed once on `asks_for_criteria=False`. The reply was right: "I need the
criteria before this can start … Give me those, or add them to the issue". The check's
pattern wanted the word "criteria" within 40 chars after give/add/tell. Widened to
need/provide/write/supply and 60 chars; re-verified against the same events: PASS. The
ac4 demo's stored reply still FAILS under the widened pattern (`cannot_converge=False
offers_to_start=True`), so the check did not get weaker where it matters.

## Numbers

- **Criteria met: 5/5.** UI-pending: none.
  | AC | Proven by |
  |---|---|
  | 1 | `present` — fails with the walk-through cut (ac1) |
  | 2 | `present`, `no` — fails with the gate cut everywhere it is stated (ac2) |
  | 3 | `no` (recorded: ac3a), `again` (not re-asked: ac3b), `changed` (re-asked on change: ac3c) |
  | 4 | `vague` — fails with the rule replaced by its opposite (ac4) |
  | 5 | `yes` — fails with branch and method not stated (ac5) |
- Moved: 4 → 5 (AC3's changed-issue half).
- **Cycles: 3** (cycle 1 stopped at the usage limit).

## For Kaushik

- **`changed` simulates the tracker moving on** by editing the recorded `updated_at`; it
  does not edit the sandbox issue. A real edit would change the shared issue on every
  run. The unproven part: that GitHub's `updatedAt` moves on a comment or a body edit —
  `cmd_issue` reads whatever the field says.
- **Sandbox pollution**: every `yes` run pushes a new feature branch to
  `sb-sandbox-alpha` (`feature/1-greet-lang`, `…-greet-language`, `…-greet-in-language`),
  and the brain now sees earlier ones. AC5 passed both times, but one demo run stopped
  to ask which branch to adopt. Delete them if it flakes.
- **Skill change in this loop**: the vague reply must say "this cannot converge" in
  those words (cycle 2). #42 as written, not a scope change.

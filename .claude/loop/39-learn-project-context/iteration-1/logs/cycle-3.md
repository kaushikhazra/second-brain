# Cycle 3 — 2026-10-09 01:05 +0530

**Branch:** `feature/multi-project` (read from git). Issue #39 re-read: OPEN, criteria unchanged.

## Action taken

Cycle 2's constraint: AC 3, 4, 5, 6 had no check. No `src/` change this cycle.

`check_context.py` grew three modes:
- `nofile` (AC 3) — take beta in; the reply says there is no CLAUDE.md; the record
  has `claude_md: none`, the "No CLAUDE.md" line, Purpose from the README, Code from
  the structure (`notes.py`/`src/`).
- `hooks` (AC 6) — graded from `takein`: reply names `mark_session` and says not
  adopted; the brain's `.claude/settings.json` is byte-identical to `src/`'s, no
  `settings.local.json`; no `alpha-hook-fired.log` anywhere under the brain (checked
  after the `upstream` work session too).
- `upstream` (AC 4 + AC 5) — a local bare mirror of alpha is the upstream (the real
  sandbox is never pushed to); a commit there adds *"Every new function carries a
  docstring that starts with 'Returns'."* to CLAUDE.md; the scratch clone's origin
  points at the mirror; the owner asks for `farewell(name)`. Graded: the record's
  `claude_md` equals the mirror's new blob and mentions the docstring rule; in the
  tool trace, `projects.py learn` comes before the first Write/Edit in the project;
  the reply says it relearned; `.claude/specs/<feature>/requirement.md` exists in
  the clone; the reply names which rule applied (project's over the brain's).

## Observation (fresh build, all modes)

```
takein   [PASS] AC1  fingerprint, filled, method/conventions/purpose/.claude/hook
know     [PASS] AC2  from_record(planted)=True
nofile   [PASS] AC3  reply_says_no_claude_md record_marked purpose(README) code(structure)
hooks    [PASS] AC6  listed said_not_adopted settings_untouched hook_fired_logs=[]
upstream [PASS] AC4  record_matches_new_upstream learn_call=5 < first_project_edit=9 told_owner
         [PASS] AC5  specs=[farewell/requirement.md, design.md, task.md] told_which_applied
```

`upstream` reply: *"Project instructions had changed upstream. Before starting I
updated the clone and refreshed the brain's notes… I followed sb-sandbox-alpha's
rule (spec first) over the brain's own (loops)."* `farewell`'s docstring starts with
"Returns" — the new upstream rule was obeyed in the code.

**#38 regression:** first attempt crashed in the **check harness** —
`UnicodeEncodeError` printing a "→" to a redirected cp1252 stdout. Fixed: both check
scripts reconfigure stdout to UTF-8. Second attempt: 4/5 — AC 5 FAILED on
`unreachable also=['noaccess']`; the reply said *"…the address or the network, not
with access to the repo"*. A check misread (a ruled-out cause read as named), not a
product change. Widened the ruled-out-cause filter to contrastive `, not with/about/a…
<access|network|address>` clauses; a first, unrestricted version stripped "…, not a
git repository" from the not-git reply and broke that case — narrowed to clauses
naming access/network/address/permission. Re-verified on the same trace: 5/5, 7/7.

## Numbers

- **Criteria met: 2/6** — AC 1, AC 2 (fresh, demonstrated in cycle 2).
- **Passing, not counted:** AC 3, 4, 5, 6 — no fails-when-removed demonstration yet.
- UI-pending: none.
- Moved: 2 → 2. Zero, honestly: four checks exist and pass, none yet shown to fail.
- #38: 7/7 hold after two check-harness fixes. No product regression.
- Assumptions changed: none.

## For Kaushik

- The `upstream` session put the work on a new branch because *"a hook won't allow
  source edits on `main`"* — that is a hook from **your** `~/.claude`, which every
  scratch brain inherits. A real owner's brain wouldn't have it. Same for the
  "no-compound-commands" apologies that keep appearing in replies.
- Alpha's own instruction `python -m unittest` finds 0 tests (no `tests/__init__.py`).
  The brain noticed and said so. It is the sandbox's bug; I left the sandbox as is.
- The #38 checks have now flaked twice on reply wording. Each fix was checked against
  the earlier demo traces so discrimination was kept, but reply-text grading is the
  soft spot of these checks.

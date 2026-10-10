# Cycle 2 — 2026-10-09 00:53 +0530

**Branch:** `feature/multi-project` (read from git). Issue #39 re-read: OPEN, criteria unchanged.

## Action taken

Cycle 1's constraint: nothing was learned, only looked up, so AC 2 could not discriminate.

- **`manage` learns.** `projects.py` gained:
  - `learn <name>` — writes `.claude/projects/<name>.md` with a script-owned
    frontmatter fingerprint (commit, `CLAUDE.md` blob, README blob) and the hooks
    list, leaves `_(to fill…)_` prose sections, and prints the material
    (`CLAUDE.md` or "(none)", README, every `.claude/` file with markdown in full,
    hooks, top level);
  - `stale <name>` — fetch, compare the record's `claude_md` with
    `origin/HEAD:CLAUDE.md` → CURRENT / STALE / NO_RECORD;
  - `refresh <name>` — `pull --ff-only`, refusing to touch local work.
  - stdout forced to UTF-8: alpha's em dash printed as `?` under the Windows code
    page in the first sanity run.
- **`SKILL.md`:** learn right after CLONED; what fills each section; no CLAUDE.md →
  say so; hooks listed with "not adopted"; answer "what do you know" from the
  record; `stale` before any work, relearn on STALE; the project's rules win while
  working there, and the owner is told which rule applied.
- `src/CLAUDE.md` routing row + Structure; `.claude/projects/` gitignored.
- **`check_context.py`:** `--mode takein` (AC 1, graded on the record: fingerprint
  matches the clone, no unfilled section, method/conventions from CLAUDE.md, purpose
  from README, `.claude/` contents, hook listed). `--mode know` now plants
  `Codename: Juniper Kestrel.` in the record's Purpose only, then asks in a fresh
  session — the answer must carry it.

## Observation (fresh build)

```
takein  ($0.43) [PASS] AC1 record=True fingerprint_matches_clone=True unfilled=False
                       method=True conventions=True purpose(README)=True .claude/=True hook_listed=True
know    ($0.38) [PASS] AC2 purpose method conventions=[T,T,T] code tests from_record(planted)=True
```

The reply opened "Codename *Juniper Kestrel*" — answered from the record (2 reads in
the asking session, both of the record path family).

**Fails-when-removed:**
- AC 1 — stripped *Learning a project* from the scratch `SKILL.md`, re-ran `takein`:
  `[FAIL] record=False …`. The brain said "I haven't learned the project's instructions
  yet … I stopped rather than guess." Restored.
- AC 2 — without a record there is nowhere for the planted fact to come from; the
  mode refuses to run (`no learned record to ask about`). Cycle 1's baseline also
  showed the bare brain answering from files alone, which would now FAIL on
  `from_record=False`.

**#38 regression (`check_clone.py --all`, fresh, `src/` changed):** 5/5 modes PASS,
7/7 criteria. Take-in replies now carry the learned summary; no check disturbed.

## Numbers

- **Criteria met: 2/6** — AC 1, AC 2.
- UI-pending: none.
- Moved: 0 → 2. What moved it: `learn` + the record, and the planted-fact check.
- #38: 7/7 hold. No regression.
- Assumptions changed: none.

## For Kaushik

- The fingerprint is written by the script, the prose by the brain. A model asked to
  copy 40-character hashes would eventually slip; AC 4's staleness test leans on them.
- `stale` compares only `CLAUDE.md`. The issue names CLAUDE.md; a change to a
  project's `.claude/` rules would not trigger a relearn. Easy to widen if you want it.
- Before work, `refresh` fast-forwards the clone. That is the least surprising way to
  "relearn from upstream", but it does move the owner's working copy.

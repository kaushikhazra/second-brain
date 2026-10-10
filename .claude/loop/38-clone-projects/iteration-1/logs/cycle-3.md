# Cycle 3 — 2026-10-09 00:23 +0530

**Branch:** `feature/multi-project` (read from git). Issue #38 re-read: OPEN, criteria unchanged.

## Action taken

Cycle 2's constraint: AC 4's check could not discriminate; AC 5–7 had no check.

- **Product:** `normalise()` now maps HTTPS, `ssh://` and scp-style `git@host:o/r`
  to one `host/owner/name`, so the same repo by another spelling is one project.
- **Check:** `check_clone.py` grew `again` (HTTPS **and** SSH spelling; marker
  survives, no `git clone` in the tool trace, reply says "already", path named, not
  read as a failure), `fail` (3 causes), `list`, `relocate` (brain copied to
  `brain-moved/`; absolute paths must be under the *new* folder).

## Observation — and what the checks caught

| Mode | Result |
|---|---|
| https | PASS AC1 (HTTPS), AC2, AC3 |
| again | PASS AC4 — both spellings: `already`, path, 0 hand clones, marker survived |
| fail  | **FAIL ×2, then PASS** (see below) |
| list  | PASS AC6 — path + origin in a table |
| relocate | PASS AC7 — `brain-moved\projects\sb-sandbox-alpha` named in both turns, 1 clone |

**AC 5 caught three real defects, in order:**
1. The no-access reply led with the raw status code "**NO_ACCESS**". Fixed in
   `SKILL.md`: lead with the cause in plain words; the code is never shown.
2. **On no-access, the brain switched to HTTPS on its own and cloned
   `sb-sandbox-beta`**, a URL the owner never gave. The check failed on
   `projects != ['sb-sandbox-alpha']`. Fixed in `SKILL.md` § Do not: never retry
   with a different spelling; report, say what would work, let the owner choose.
   Stray scratch clone removed.
3. The brain itself reported `DETAIL` was git's *last* stderr line ("and the
   repository exists.") instead of the cause. Fixed in `projects.py`: first non-blank
   line.

Also a check fault, fixed: matching the cause on the lead *sentence* missed "I
couldn't take it in. GitHub … refused this machine's SSH key"; whole-reply matching
misread "not an access problem" as naming access. Now: first paragraph, minus
explicitly ruled-out causes. Final `fail` run after all fixes:
`unreachable own=True also=[] | noaccess own=True also=[] | notgit own=True also=[]`, projects=['sb-sandbox-alpha'].

Scratch `SKILL.md`/`projects.py` were synced from `src/` after each fix (diffed
identical); `https`/`again`/`list`/`relocate` ran **before** those fixes. The fixes
touch only failure paths and wording, but a full fresh rebuild is owed next cycle.

## Numbers

- **Criteria met: 4/7** — AC 1 (HTTPS), 2, 3, 5.
  - Fails-when-wrong shown: AC 1 (cycle 1 baseline), AC 3 (ignore rule removed),
    AC 5 (failed on the real substitution defect, passes once fixed), AC 2 rides on AC 1.
- **Passing, not yet counted:** AC 4, 6, 7 — no fails-when-removed demonstration yet.
- **Manual-test:** AC 1's SSH half (Kaushik's ruling, `multi-project-assumptions.md`).
- Moved: 3 → 4. What moved it: the `fail` mode, and the three fixes it forced.
- Earlier-issue checks: none. No regression.
- Assumptions changed: SSH clones are manual-test (added this cycle, per Velasari).

## For Kaushik

- Defect 2 is worth knowing about beyond this issue: left to itself, the brain
  "helpfully" routes around an access failure with a URL nobody gave it. The rule now
  lives in `manage/SKILL.md`; similar routing-around may show up in #40 (trackers).
- The `noaccess` case passes partly because the reply quotes git's
  "Permission denied" — the plain-words rule and the quoted detail both count.

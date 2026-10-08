# Cycle 2 — 2026-10-09 00:08 +0530

**Branch:** `feature/multi-project` (read from git). Issue #38 re-read: OPEN, criteria unchanged.

## Action taken

Cycle 1's constraint: the brain had no rule for where projects go.

- **Built `src/.claude/skills/manage/`** — `SKILL.md` (routing, STATUS → owner's words
  table) and `scripts/projects.py` (`clone` / `list` / `locate`). Brain root found by
  walking up from the script to the folder holding `.claude/` + `CLAUDE.md`; no path is
  stored anywhere — `projects/` itself is the registry. Clone probes with
  `git ls-remote --symref` before creating anything; failures classified
  `UNREACHABLE` / `NO_ACCESS` / `NOT_A_GIT_REPO` / `CLONE_FAILED` from git's real
  stderr (probed this cycle: `.invalid` host, missing GitHub repo, example.com, a
  non-URL, SSH without key). `GIT_TERMINAL_PROMPT=0` and SSH `BatchMode` so a missing
  credential fails instead of hanging.
- Routed from `src/CLAUDE.md` (Session Lifecycle + Structure); `projects/` added to
  `src/.gitignore`.
- **Bug found and fixed in passing:** on Windows git marks object files read-only, so
  `shutil.rmtree` raised `WinError 5` (hit by the check's own rebuild). The product's
  partial-folder cleanup had the same call with `ignore_errors=True` — it would have
  silently **left a partial folder**, breaking AC 5. Both now clear the bit and retry.
- `check_clone.py` gained `--mode again` and AC 2/AC 3 verification.

## Observation (all run fresh)

```
--mode https  ($0.20)  [PASS] AC1  origin == alpha HTTPS, HEAD resolves
                       [PASS] AC2  reply: "cloned to projects\sb-sandbox-alpha, default branch is main"
                       [PASS] AC3  untracked=[] committed=[] ignored=True
--mode again  ($0.04)  [PASS] AC4  marker_survived=True projects=['sb-sandbox-alpha'] path_named=True
```

Stream shows the brain invoked `projects.py` (3 references) — through the skill, not ad hoc.

**Fails-when-removed, demonstrated:**
- AC 1 — cycle 1's run with no capability: FAIL (cloned beside the brain).
- AC 3 — removed `projects/` from the scratch brain's `.gitignore`, re-verified:
  `[FAIL] AC3 untracked=['?? projects/sb-sandbox-alpha/'] ignored=False`. Restored.
- AC 2 — rides on AC 1 (requires the clone) plus reply text; with no capability the
  reply named a different path → would FAIL.
- **AC 4 — NOT demonstrated.** Without the ALREADY_MANAGED branch, `git clone` into an
  existing folder fails on its own, so the marker survives and a reply naming the path
  could still pass. The check is too weak to count.

## Numbers

- **Criteria met: 3/7** — AC 1 (HTTPS half), 2, 3. AC 4 passes but is not counted
  until its check discriminates.
- **Access-pending:** AC 1's SSH half — `ssh -T git@github.com` → `Permission denied
  (publickey)`; this machine has no GitHub SSH key. Not met, does not block.
- Moved: 0 → 3. What moved it: the `manage` skill.
- Earlier-issue checks: none exist. No regression.
- Assumptions changed: none.

## For Kaushik

- The SSH key gap also means SSH URLs will report `NO_ACCESS` on this machine — which
  is the correct, distinct message for AC 5, and I plan to use it as AC 5's
  "missing access" case.
- GitHub answers "Repository not found" for both a missing repo and a private one you
  cannot see. The skill reports that as `NO_ACCESS` ("no access, or it does not exist
  there") — git cannot tell them apart, so the message doesn't pretend to.

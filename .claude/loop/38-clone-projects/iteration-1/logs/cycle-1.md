# Cycle 1 — 2026-10-08 23:56 +0530

**Branch:** `feature/multi-project` (read from git).

## Action taken

As `action.md` asked: read issue #38, found where an owner's request becomes an
action, chose where `manage` lives, wrote the first check for criterion 1.

- **Routing today:** an owner's request reaches a skill only through the Session
  Lifecycle table in `src/CLAUDE.md` → `src/.claude/skills/<name>/SKILL.md`.
  Nothing there covers a repo URL.
- **Where `manage` lives (decided):** a new skill `src/.claude/skills/manage/`,
  `SKILL.md` plus `scripts/projects.py` (clone / list / locate). The script resolves
  the brain root from its own file location (`Path(__file__).parents[3]`), never a
  stored absolute path — that is what criterion 7 needs. One row added to the
  `src/CLAUDE.md` routing table; `projects/` added to `src/.gitignore` (criterion 3).
- **Check written:** `checks/multi-project/check_clone.py` — builds a whole scratch
  brain from `src/` (with its own git repo) under
  `C:/Projects/.tmp/second-brain-loop-38/brain`, sends the owner turn
  `Take this project in: <alpha HTTPS URL>` via `claude -p`, then inspects
  `projects/sb-sandbox-alpha/` (is a repo, origin == URL, HEAD resolves).

## Observation

Ran fresh: `--build`, `--run --mode https` ($0.53), `--verify --mode https`.

```
[FAIL] AC1: an HTTPS URL is cloned into projects/<repo-name>/: ... is_repo=False origin='' head=False
```

The brain, with no capability, cloned alpha **beside** itself
(`C:/Projects/.tmp/second-brain-loop-38/sb-sandbox-alpha`) and said "the brain has no
rule yet for where projects go". So the check discriminates: it fails with the
behaviour absent. Stray clone removed.

## Numbers

- **Criteria met: 0/7.** UI-pending: none named yet.
- Moved: 0 → 0. Expected — this cycle built the measuring stick, not the behaviour.
- Earlier-issue checks under `checks/multi-project/`: none exist (this is the first
  issue in the queue). No regression possible.
- Assumptions changed: none.

## For Kaushik

- `claude -p` inside the scratch brain also loads **your** global
  `~/.claude/CLAUDE.md` (the reply quoted your loop-engineering rule against alpha's
  spec-driven CLAUDE.md). A real owner's machine would not have it. The checks
  accept this for now; a fully isolated run would need `CLAUDE_CONFIG_DIR` the way
  `brain-claude-sandbox.bat` does, which costs a sign-in.
- The scratch brain's `/session-start` arms a heartbeat cron each run. Harmless in
  `-p` (dies with the process) but it is spend on every check run.
- AC 1 says "HTTPS or SSH". SSH proof depends on this machine having a GitHub SSH
  key; to be checked next cycle, else AC 1's SSH half goes access-pending.

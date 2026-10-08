# Cycle 1 — 2026-10-09 02:04 +0530

**Branch:** `feature/multi-project` (read from git). Issue #41 read first: 7 criteria.

## Action taken

`action.md` asked for the seen-record decision and the AC 4/5 check. Did that, plus
the capability and the AC 1–3 check, per the build-and-check-together pattern.

- **Where the seen record lives (decided):** `.claude/projects/<name>.json` beside the
  tracker settings — `monitor`, `seen_issues {number: title}`, `issues_failure`.
  Machine-local, gitignored, survives a restart, moves with the brain.
- **Pre-existing open issues** count as "not seen yet": the first beat after opt-in
  reports them once. This lets AC 4/5 be checked read-only on alpha's two seeded
  issues, as `action.md` asked.
- **`projects.py`:** `monitor <name> on|off` (refused for unsupported trackers),
  `monitored`, `issues` — reads open issues of monitored projects only, via `gh` /
  `glab` per tracker (no call when credentials are missing — so no GitLab host is
  ever contacted from here), prints `NEW:` / `CLOSED:` / `FAILURE … TELL_OWNER` /
  `RECOVERED:`, and updates the seen record.
- **`manage/SKILL.md`** *Monitoring*: ask once after take-in; never switch on unasked;
  what each `issues` line means for the owner.
- **Heartbeat:** new `project-issues` pair in `observe.md` / `goal.md` — runs every
  beat, breaks silence for new issues and first-time failures. `SKILL.md`: Synaptra
  unreachable now stops the **memory** work of a beat, not the beat — issue watching
  needs no memory (the check brains have no Synaptra, and a real owner's store can be
  down too).
- **`check_monitor.py`** (`scratch_brain.run_owner` gained `resume=`; new
  `session_id`, `final_text`): `optin` (alpha yes, beta no — the owner answers in the
  same conversation via `--resume`), `beat` (two cron-style beats, each a fresh
  session). Expected issues read live from GitHub, read-only.

## Observation (fresh)

```
optin [PASS] AC1  asked alpha=True beta=True
      [PASS] AC2a alpha.monitor=True beta.monitor=False
beat  [PASS] AC4  alpha_open=['1','2'] reported both with number+title, project named
      [PASS] AC3  alpha_seen=['1','2'] beta_seen=None beta_issue_in_reply=False
      [PASS] AC5a reported_again_on_beat_2 = none
```

Beat 1: *"New issues in monitored projects: sb-sandbox-alpha #1: User greets someone
in their own language / #2: User gets a clear error for an empty name"* — and it
skipped only the memory work (Synaptra absent), as now specified.

**Regressions:** #39 5/5, #40 4/4. #38 4/5 — AC 4's `again-ssh` reply said
*"sb-sandbox-alpha was already **taken in**"* and the failure-word `already taken`
(name clash) matched. Check misread; `already taken(?! in)`. Re-verified on the same
trace: PASS → 7/7. The cycle-4 demo phrases still match.

## Numbers

- **Criteria met: 0/7** — AC 1, 2a, 3, 4, 5a pass, none demonstrated; AC 2b, 5b, 6, 7
  have no check yet.
- UI-pending: AC 1 is an interactive question; proven here through `-p` + `--resume`,
  so not UI-pending.
- #38 7/7, #39 6/6, #40 6/6.
- Assumptions changed: none.

## For Kaushik

- I treated issues open at opt-in as unseen, so the owner hears about them once. The
  alternative — baseline them silently — is a one-line change if you prefer it.
- On a *re-request* of an already-managed project the brain asked again whether to
  monitor it (monitoring was off). Harmless, but it's a second ask; the criterion says
  "after taking a project in".
- The heartbeat change (memory down no longer stops the whole beat) touches a skill
  outside `manage`. It's the smallest change that lets issue watching run without
  Synaptra.

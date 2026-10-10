# Cycle 1 — 2026-10-09 01:29 +0530

**Branch:** `feature/multi-project` (read from git). Issue #40 read first: 6 criteria.

## Action taken

`action.md` asked for the AC 1 check only. Taking #39's lesson (build and check
together, demos after), this cycle built the capability and checks for all six.

- **`projects.py`** — `detect(p)`: code host from the remote URL, tracker from the
  project's own files (a Jira link in CLAUDE.md/README) else the host's own, with a
  `how` line (remote URL + `.gitlab-ci.yml` / `.github/`). Stored in
  `.claude/projects/<name>.json` beside the learned record: `detected` (rewritten on
  each `learn`), `override` (kept), `credentials_told`. New commands: `trackers`
  (GitHub, GitLab), `tracker <name> [--set field=value] [--clear]`. `learn` ends with
  the tracker block. Credentials are checked **locally only** (`gh auth status`,
  GITHUB_TOKEN; GITLAB_TOKEN or a glab config file) — no GitLab host is contacted.
- **`SKILL.md`** — *Code host and issue tracker*: say host, tracker and how on take-in;
  unsupported → still managed, monitoring and issue work unavailable; credentials
  notice once; override commands; answer tracker questions from `tracker <name>`.
  Routing row and description extended.
- **`check_tracker.py`** — GitLab and Bitbucket stand-ins are local bare repos reached
  through `url.<bare>.insteadOf=<gitlab.com / bitbucket.org URL>` passed to the brain's
  session as `GIT_CONFIG_*` env (new `extra_env` in `scratch_brain.run_owner`). The
  clone's origin stays the real-looking address; nothing leaves the machine. Modes
  `detect`, `trackers`, `override`, `restart`; `--all`.

## Observation

**First fresh run: 2/4 modes.** It caught a **product bug**: `origin_of()` used
`git remote get-url`, which *applies* `insteadOf` rewrites — the brain saw the mirror's
path (`C:/…`) and detected the host as "c:". Any owner with URL rewrites in their git
config would hit it. Fixed: `git config --get remote.origin.url`. The brain itself
diagnosed the cause in its reply. Also widened AC 4's wording (`monitor|watch` — "I can
only watch issues on GitHub and GitLab").

**Second fresh run: 3/4**, AC 1 FAILED on github: the reply said "worked out from the
repo's **address**". A check misread; added `address`. Re-verified on the same trace:

```
detect    [PASS] AC1 github gitlab(+.gitlab-ci.yml) bitbucket
          [PASS] AC4 managed origin=bitbucket.org said_unavailable
          [PASS] AC5a named_what_is_needed (glab auth login / GITLAB_TOKEN)
trackers  [PASS] AC3 GitHub + GitLab
override  [PASS] AC2 stored_override='gitlab' reply_confirms
restart   [PASS] AC6 alpha reported as GitLab, set by the owner
          [PASS] AC5b recorded_as_told, not repeated
```

**Regressions (re-run after the `origin_of` fix):**
- #39 `check_context.py --all`: 5/5, 6/6.
- #38 `check_clone.py --all`: 4/5 — AC 5's not-git case read the wrong paragraph: the
  reply joined a mid-turn line ("Booting the brain…; then I'll take the project in.")
  ahead of the answer. **Check fault, not product.** Failure causes are now graded on
  the turn's final message, first paragraph about the take-in. Re-verified on the same
  trace: PASS → 7/7.

## Numbers

- **Criteria met: 0/6.** All six pass fresh; none yet shown to fail with its behaviour
  removed.
- UI-pending: none. Access-pending: none (GitLab proven from the remote URL, per the
  assumptions).
- Moved: 0 → 0 counted (6 passing).
- #38 7/7, #39 6/6 — no regression.
- Assumptions changed: none.

## For Kaushik

- The `insteadOf` bug is real and outside the tests' world: corporate git configs often
  rewrite `https://` to SSH or to a mirror. Reading the configured URL is the right fix.
- Reply-text grading keeps costing a cycle's attention (third wording fix across #38–#40).
  Each fix was re-verified on the trace that tripped it. The object checks (files, git
  state, settings JSON) have not flaked once.
- "Credentials notice once" is per project and tracker. A second GitLab project would
  get the notice again. If you meant once per brain, it's a one-line change.

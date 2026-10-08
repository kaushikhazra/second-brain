# Cycle 1 — 2026-10-09 00:45 +0530

**Branch:** `feature/multi-project` (read from git). Issue #39 read first: 6 criteria.

## Action taken

As `action.md` asked: read #39 and #38's capability, decided where learned context
lives, wrote the AC 2 check.

- **Where learned context lives (decided): `.claude/projects/<name>.md`** in the brain
  — a learned record per project, gitignored, machine-local, moves with the brain.
  **Not Synaptra**, though `action.md` suggested memory: (a) AC 4 needs a fingerprint
  to compare against upstream, which a file holds exactly and a decaying memory does
  not; (b) every check brain runs with an empty MCP config — a Synaptra-only record
  would be untestable through the owner's door; (c) not under `projects/`, because
  #38's checks (and the folder-is-the-registry rule) treat every folder there as a
  project. Recorded under For Kaushik.
- **Shared check plumbing:** `checks/multi-project/scratch_brain.py` (build, run_owner,
  reply_text, tool_uses, report) for the remaining loops. `check_clone.py` still has
  its own copies — migrate when next touched.
- **`check_context.py --mode know`:** take alpha in (session 1), ask "What do you know
  about sb-sandbox-alpha?" in a fresh session 2; grade purpose, method, conventions,
  code and tests locations.
- `check_clone.py --all` added: the #38 regression in one call.

## Observation

**AC 2 baseline (no learning capability exists): PASS.**
`purpose=True method=True conventions=[True, True, False] code_at=True tests_at=True |
asked-session reads of the project: 5`. The brain answered by opening alpha's files on
demand (and found the take-in in its session history). **The check cannot fail with
learning removed** — so it proves nothing yet. Not counted.

**#38 regression (`check_clone.py --all`, fresh):** 4/5 modes on first verify. AC 4
FAILED on `again-ssh: reads_failed=True` — the reply was correct ("already manages
this project … didn't clone it again") but carried boot notes ("couldn't load the self
map"), and the failure-word list had a bare `couldn't`. **A check flake, not a product
regression** (no `src/` change since #38 closed). Fixed: failure words now name this
request's failures only (`different project`, `name clash`, `couldn't clone/take`, …).
Re-verified on the **same trace**: PASS. Confirmed the narrowed list still matches both
cycle-4 demo replies ("a *different* project", "name clash"), so the AC 4 removal demo
still fails. A first fix (lead-paragraph only) was rejected for that reason — it would
have blinded the check to the demo.

## Numbers

- **Criteria met: 0/6.** UI-pending: none named.
- Moved: 0 → 0. AC 2's check exists but does not discriminate.
- #38: 7/7 still hold (after the check flake fix). No regression.
- Assumptions changed: none.

## For Kaushik

- I chose a file record over Synaptra for learned project context (reasons above).
  If you want it in memory too, a pointer memory per project via `/create-memory` is
  a small add on top — the file stays the source the checks can see.
- AC 2 as worded is something a bare Claude does unaided by reading the files. The
  plan to make it discriminate: plant a fact only in the learned record, require it in
  the answer. That proves the brain answers from what it learned — but it grades the
  mechanism a little. If you'd rather accept "answers correctly" alone, AC 2 is
  already met.
- Session-start boot chatter lands in every `-p` reply. It made one #38 check flaky.

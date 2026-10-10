# Observe

## Order matters

**Read the criteria from the tracker first** — `gh issue view 38 -R kaushikhazra/second-brain` — before
the diff and before the previous cycle's log. Attack each criterion; do not confirm it.

## The measurement

The number this loop moves is **criteria demonstrably met, out of 7**.
Demonstrably means a check script under `checks/multi-project/` that fails when the
behaviour is removed, run fresh this cycle.

**How a check reaches the brain:** through the owner's door. A check builds a scratch
brain from `src/` under `C:/Projects/.tmp/second-brain-loop-38/`, drives it with
`claude -p` (and `--resume` for a follow-up answer), then inspects files, git state and
the reply text. ⛔ A check never imports or calls the brain's internal scripts directly
to prove a criterion — that grades the producer, not what the owner gets.

**UI-pending:** a criterion that can only be proven at the real terminal window is
reported as UI-pending, not met. It does not block convergence; it is named in the
closing comment.

## Every cycle, record

- **Criteria met, out of 7**, by number. UI-pending ones listed separately.
- How far the number moved, and what moved it. Zero is a legitimate answer.
- Every check under `checks/multi-project/` from earlier issues, re-run. **A criterion
  of an earlier issue that breaks is a regression, and this cycle's number counts it
  as zero progress.**
- Any assumption that changed.
- The branch, read from git.
- **For Kaushik** — anything you would have chosen differently, or a risk you saw.

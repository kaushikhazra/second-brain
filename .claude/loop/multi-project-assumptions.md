# Assumptions shared by the overnight multi-project loops (#38–#45)

Read every cycle. One file so the eight loops cannot drift apart.

## Settled

- **The product lives under `src/`.** A user receives `src/` and nothing else. A shipped
  file only ever contains paths relative to the brain's own root — never `src/`.
- **Checks live under `checks/multi-project/`**, standalone `check_*.py` scripts, run by
  hand. There is no test framework; do not add one.
- **Scratch lives under `C:/Projects/.tmp/second-brain-loop-<issue>/`.** Never in the
  repo, never in a system temp folder.
- **Test projects to clone:** `https://github.com/kaushikhazra/synaptra.git` (public,
  GitHub). GitLab is proven from a remote URL (`git remote set-url` on a local scratch
  repo to a gitlab.com address), not from a live GitLab API — there is no GitLab
  account to use tonight. A criterion that needs a live GitLab call is reported
  **access-pending** — treated like UI-pending: not met, does not block convergence,
  named in the closing comment.
- **Read-only towards every tracker** except the one closing comment on this repo's own
  issue (#38–#45). ⛔ Never create, edit, label, close or comment on issues in any other
  repo. ⛔ Never push to a cloned test project.
- **Never touch the live store.** `.claude/synaptra-data` is the owner's memory.
- **Zero hardcoding.** A component resolves its own location at runtime. Every
  relocation criterion is proven by copying the scratch brain to a renamed folder and
  re-running.
- **Nothing merges.** Kaushik merges `feature/multi-project` himself.

## When something is unclear

This run is unattended. **Do not stop to ask.** Take the option that changes the
brain's existing behaviour least, write the question and your choice in the cycle log
under **For Kaushik**, and carry on. Stop only for the stall cap or the fail-safe.

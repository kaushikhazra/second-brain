# Assumptions shared by the overnight multi-project loops (#38–#45)

Read every cycle. One file so the eight loops cannot drift apart.

## Settled

- **The product lives under `src/`.** A user receives `src/` and nothing else. A shipped
  file only ever contains paths relative to the brain's own root — never `src/`.
- **Checks live under `checks/multi-project/`**, standalone `check_*.py` scripts, run by
  hand. There is no test framework; do not add one.
- **Scratch lives under `C:/Projects/.tmp/second-brain-loop-<issue>/`.** Never in the
  repo, never in a system temp folder.
- **Test projects: two private sandboxes, and only these.** Kaushik's ruling: a live
  project is never a test project.

  ```
  sb-sandbox-alpha   https://github.com/kaushikhazra/sb-sandbox-alpha.git
                     CLAUDE.md states a method (spec-driven) · one SessionStart hook
                     (writes .tmp/alpha-hook-fired.log under the running project)
                     open issues: #1 language greeting · #2 empty name
  sb-sandbox-beta    https://github.com/kaushikhazra/sb-sandbox-beta.git
                     NO CLAUDE.md, README only, no hook
                     open issues: #1 delete a note · #2 "Notes list" — deliberately
                     vague, no criteria
  ```

  Local scratch repos built by a check are still fine for anything else (a GitLab
  remote URL, a conflicting hook).
- GitLab is proven from a remote URL (`git remote set-url` on a local scratch
  repo to a gitlab.com address), not from a live GitLab API — this machine has
  GitHub access only. GitLab (the office instance) sits behind a VPN this machine
  does not have, and there is no other GitLab account. ⛔ Do not try to reach any
  GitLab host. A criterion that needs a live GitLab call is reported
  **access-pending** — treated like UI-pending: not met, does not block convergence,
  named in the closing comment.
- **The two sandboxes are the loop's to change.** Create, edit, label, close and
  reopen their issues freely to stage what a criterion needs (a new issue appearing,
  one closing, one changing), and push branches to them. Leave each sandbox's
  `main` and its seeded issues as you found them at the end of the run.
- **Read-only towards every other tracker**, except the one closing comment on this
  repo's own issue (#38–#45). ⛔ Never create, edit, label, close or comment on issues
  in any other repo, and never push to any other repo.
- **Never touch the live store.** `.claude/synaptra-data` is the owner's memory.
- **Zero hardcoding.** A component resolves its own location at runtime. Every
  relocation criterion is proven by copying the scratch brain to a renamed folder and
  re-running.
- **Nothing merges.** Kaushik merges `feature/multi-project` himself.

## When something is unclear

This run is unattended. **Do not stop to ask.** Take the option that changes the
brain's existing behaviour least, write the question and your choice in the cycle log
under **For Kaushik**, and carry on. Stop only for the stall cap or the fail-safe.

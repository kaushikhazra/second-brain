# Assumptions

Standing inputs that must survive a rewrite of `action.md`.

## Settled

- **A session can read its own model.** Phase 0, settled by velasari before this loop
  opened: a `SessionStart` hook supplies `transcript_path`, and `message.model` is
  readable out of that transcript. Open question 1 in the issue is closed. A2 and E1
  do not collapse.
- **Phase order.** 1 fixture brain → 2 calibration record and boot check → 3 aged
  fixtures and the boot-list set measurement. The fixture is first because every
  criterion is proved against a scratch brain and none existed.

## About this repo, carried in from the survey

- There is **no test framework** — no pytest, no conftest, no CI. Checks are standalone
  `check_*.py` argparse scripts, run by hand.
- **27** `build_scratch_project()` copies existed at the start of this loop, across
  `.claude/shared/memory/` and `.claude/skills/*/` — not the ~14 the brief estimated,
  measured in cycle 1. Normalising string literals away yields 22 shapes, but nearly all
  of that spread is `black` line-wrapping; structurally there are about 5. **Do not
  re-derive the 22 and conclude the extraction was unsafe** — it is formatting noise.
  Two were migrated in cycle 1; **25 remain**. They differ on an enumerable set of axes: skills copied, `.mcp.json`
  healthy / deliberately broken / absent, `.claude/.venv` junction, `memory_guard` hook
  plus `settings.json`, `persona.md` + `user.md`, the `CLAUDE.md` prompt text, and extra
  shared files (`memory-shapes.md`, `activation.py`).
- `check_heartbeat_ac3_scripted_agent.py` writes a hash manifest after building. That is
  the check's own assertion setup, not fixture work.
- Scratch trees live at `C:/Projects/.tmp/second-brain-loop-N/`, never in the repo and
  never in a system temp folder.
- Scripted-agent checks cost real money — they shell out to `claude -p` with
  `--max-budget-usd`. Run the two migrations, not fourteen.

## Constraints from the orchestrator

- **Behaviour-preserving.** A check that passed before must pass after, unchanged in
  outcome.
- **Never copy a real memory store** — Velasari's or anyone's — into the repo or a
  fixture. Aged fixtures are built synthetically, in phase 3.
- **Do not touch `/dream`.** The C4 backup-check extraction is separate work and is not
  to be tangled with the fixture.

## Unsettled

- Where E4's model-ordering registry lives, and what it does when out of date.
- H2's declared factor. One observation (8:1) is not a threshold. Report the number,
  fail on a generous factor, tighten later.
- Whether the substrate version (`uv pip install synaptra`, unpinned) is in scope here
  or a separate issue — open question 3, unanswered.

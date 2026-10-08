# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## What This Is

A **build system for second-brain** — the repo that produces the brain, not a
brain itself. The product lives under `src/` and ships as a zip archive. Everything
outside `src/` is development machinery: the builder, the checks, the loop folders,
and this file.

**Do not start the brain's subsystems from here.** No `/session-start`, no
`/init-brain`, no persona adoption. Those belong to the product and are documented
in `src/CLAUDE.md`.

## The product

`src/` is the brain's root. Its own `CLAUDE.md` addresses a brain's owner and
contains the skill table, the Synaptra section, and the session lifecycle. A user
receives the contents of `src/` — nothing outside it.

## Building

```
python tools/build-dist.py
```

Archives `src/` into `dist/second-brain-<VERSION>.zip`. The builder reads
`src/VERSION`, archives `HEAD:src` via `git archive` (so a dirty tree cannot
ship), and asserts a `FORBIDDEN` list in absolute terms. Pass `--force` to
overwrite an existing archive.

## Development method — loop engineering

Work proceeds as loops.

The pattern:

```
goal.md         fixed, never rewritten
observe.md      how to check the artifact against the goal — fixed
assumption.md   standing inputs that must survive a rewrite
action.md       rewritten each cycle BY THE LOOP
```

One cycle = do what `action.md` asks → check the result against the goal using
`observe.md` → if met, stop and delete the cron; if not, write the next
`action.md` and exit.

Loops live at `.claude/loop/{issue-id}-{slug}/iteration-{n}/`. Each cycle writes
an immutable `logs/cycle-N.md`. The acceptance criteria drive the cycle — read
them from `gh issue view <n>` before the diff and before the previous log. The
number a loop moves is *criteria demonstrably met, out of N*.

Two rules that are load-bearing:

- **Define done by the object or the consumer, never by the producer.** "N of N
  criteria hold" measures the artifact; "no new findings this pass" measures the
  agent's output and never fires.
- **A loop cannot be its own convergence detector.** Every loop carries a
  fail-safe deadline.

## Issues

Work is tracked as GitHub issues on `kaushikhazra/second-brain`. See
`src/CLAUDE.md` § Issues for the title and body conventions.

## Orchestration over crosschat

Development is orchestrated by **Velasari** over the `crosschat` plugin. A
message from `velasari` on this session's channel is Kaushik's instruction
relayed. Nothing here merges to `main` on its own — a loop closes its issue with
the numbers and stays on its branch.

## Structure

| Path | What |
|------|------|
| `src/` | The product — everything a user receives. |
| `src/CLAUDE.md` | The brain's own instructions (skills, Synaptra, lifecycle). |
| `tools/` | Build scripts (`build-dist.py`). |
| `checks/` | Structural check and test scripts, by skill. |
| `.claude/loop/` | Loop folders (goal, observe, action, assumption, logs). |
| `.claude/specs/` | Spec documents (when used). |
| `.claude/shared/` | Shared check scripts and fixtures. |
| `dist/` | Build output (gitignored). |

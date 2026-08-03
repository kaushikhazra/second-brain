# AGENTS.md

Operational guidance for coding agents working in this repository. Companion to
`CLAUDE.md` — that file targets Claude Code and references slash-skills
(`/session-start`, `/e-spec:*`) which are **not invocable here**. Where you see
such a reference, read it as a plain-language instruction, not a command.

## What this repo is

A **second brain** — a personal AI-assistant workspace. `persona.md` defines who
the assistant is; `user.md` defines who it assists. Historically "not a
codebase", but it now carries real Python under `.claude/skills/*/scripts/`,
with unit tests. Treat that code as production code.

## Layout

| Path | What it is |
|------|------------|
| `persona.md`, `user.md` | Identity source of truth. Do not rewrite unless asked. |
| `.claude/skills/<name>/SKILL.md` | The skill's contract — what it does, how it is invoked. |
| `.claude/skills/<name>/scripts/` | Executable code belonging to that skill. |
| `.claude/specs/<feature>/` | requirement.md, design.md, task.md. |
| `.claude/synaptra-data/`, `.claude/.venv/`, `.claude/.python/` | Machine-local runtime. **Never commit.** |

## Hard rules

1. **Write files with the editor tools.** Do not construct file content through
   shell redirection — no heredocs (`cat <<EOF > f`), no `echo >`, no
   `Out-File`/`Set-Content`, no `python -c` writing files. If a write fails,
   report the exact error and stop; do not fall back to the shell.
2. **Absolute paths.** Do not `cd` inside commands; the working directory is
   already set.
3. **Report failures verbatim.** Exact error, path, parameters. A silent
   workaround hides the real bug.
4. **Do not invent scope.** If the brief is ambiguous, say so and stop. Do not
   pick a direction silently.
5. **Evidence, not adjectives.** Report file paths, sizes, exit codes, test
   counts, command output. "It works" is not a result.
6. **Never self-certify a live run you did not actually perform.** If a step
   needs a service you cannot reach, say it is unreachable — do not infer
   success from unrelated output or pre-existing files.

## Branching

Never commit directly on `master`. Work on `feature/*`, then a `--no-ff` merge
into `master`. **Do not push** unless explicitly told to — publishing is the
owner's call.

## Python conventions

- Standard library first. Add a dependency only when it earns its place, and
  record it in the owning skill's `requirements.txt`.
- Unit tests live beside the code they test (`test_<module>.py`) and run with
  `python -m unittest`.
- Match the surrounding file's style: module docstring, typed signatures,
  comments that explain *why* rather than restate the code.

## Machine constraints

- 16 GB RAM. Do not run heavy jobs in parallel.
- A local ollama may be running at `http://localhost:11434`. It is **machine-local**:
  if you are not executing on that machine, you cannot reach it, and any step
  requiring it must be reported as not-run rather than assumed.

## Design principles

SOLID / DRY / KISS, but three similar lines beat a premature abstraction. Build
only what the current step needs; defer speculative generality. Fix root causes
rather than routing around them. When correcting an inconsistency, grep the
whole repo and fix every occurrence.

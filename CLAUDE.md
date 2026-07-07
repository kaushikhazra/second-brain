# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A **second brain** — a personal AI-assistant workspace, not a codebase. There
is nothing to build, lint, or test. The assistant's identity and the user's
profile are defined in two files at the root.

## Session Lifecycle

Pure routing — each skill owns its own mechanics; follow the skill, don't
improvise or replicate its steps from here.

| When | Invoke |
|------|--------|
| First action of every new conversation | `/session-start` |
| User signals stopping for the day | `/session-end` |
| `persona.md` or `user.md` missing, or user asks to re-initialize | `/init-brain` |
| Never manually — cron-fired only (see the skill for the fallback rule) | `/heartbeat` |
| User asks for it, when memory feels flat or a major arc closed — never scheduled | `/dream` |

## Structure

| File | Purpose |
|------|---------|
| `persona.md` | The assistant's persona — who the AI is. |
| `user.md` | The user's profile — who the AI assists. |
| `.claude/skills/init-brain/` | Setup flow that creates the two files above — restores from cognitive memory first, interviews only a new brain. |
| `.claude/skills/session-start/` | Startup procedure — persona adoption, memory grounding, handoff pickup. |
| `.claude/skills/session-end/` | Shutdown procedure — kill crons, store learnings and the handoff memory. |
| `.claude/skills/heartbeat/` | Cron-fired consolidation cycle — silent cognitive-memory bookkeeping. |
| `.claude/skills/dream/` | Deep memory consolidation — graph reshaping, user-invoked. |

## Cognitive Memory

**What**: the persona's primary memory system — an MCP server with
biologically-inspired decay, multi-strategy retrieval, and consolidation. The
store of cross-conversation knowledge. (Identity-neutral on purpose: the
persona and user are whoever `persona.md` and `user.md` currently define.)

**Tools**: `memory_store`, `memory_recall`, `memory_get`, `memory_update`,
`memory_relate`, `memory_related`, `memory_unrelate`, `memory_list`,
`memory_archive`, `memory_restore`, `memory_delete`, `memory_stats`,
`memory_consolidate`, `memory_config`, `memory_self`, `memory_who`,
`memory_health`. (All prefixed `mcp__cognitive-memory__`.)

**CRITICAL — when to use**:

- **Recall**: **ALWAYS** use `memory_recall` when the user asks you to
  "remember", "recall", references a "secret", asks about past conversations,
  or asks "what did we do/build/discuss." This is a BLOCKING requirement —
  check cognitive memory BEFORE saying you don't know. Also use at the start
  of non-trivial tasks to check for prior context.
- **Self**: Use `memory_self` for identity grounding (operating principles,
  attention, blind spots). Fired by `/session-start`.
- **Store**: After completing significant work, learning something important
  about the user or a project, or when the user says "remember this." Pick
  the type by what the memory *is*: an event or milestone → `episodic`; a
  fact, decision, or preference → `semantic`; a workflow or how-to →
  `procedural`.
- **Update**: When a stored fact changes, update — don't duplicate.
- **Relate**: Link memories that are causally, temporally, or thematically
  connected.

**Memory types and decay**:

| Type | Use for | Decay rate |
|------|---------|------------|
| `working` | Transient task context, current session notes | Fast (hours) |
| `episodic` | Events, conversations, experiences, milestones | Moderate (days) |
| `semantic` | Facts, decisions, architecture knowledge, preferences | Slow (weeks) |
| `procedural` | How-to knowledge, workflows, processes | Very slow (months) |
| `identity` | Self-knowledge, core operating principles | Very slow |

**Rules**:

- Cognitive memory is for cross-conversation knowledge. The auto-memory
  system (the Claude Code harness's built-in per-user memory directory,
  indexed by its `MEMORY.md` — not a file in this project) is for
  lightweight session-to-session notes. Don't duplicate.
- Always include relevant `tags` — they enable filtered browsing (e.g.,
  `handoff`, `decision`, `preference`, a project name, a date).
- Set `importance` explicitly for significant memories (0.8+). Let the system
  auto-score routine ones.
- The system handles decay, reinforcement, and consolidation automatically.
  Don't manage memory lifecycle manually.

**DB**: `~/.cognitive-memory/memory.db` | **Code**: `C:/Projects/cognitive-memory/`
(both machine-local — on a new machine, install and reconfigure the
cognitive-memory MCP server before the memory steps will work)

**Backup CLI**: the cognitive-memory install also provides the `cm` command
(`cm backup create`, `cm backup verify --deep <path>`) used by `/dream`'s
pre-dream checkpoint. Machine-local like the paths above.

## Conventions

- Keep `persona.md` and `user.md` as the single source of truth for identity;
  update them (rather than this file) when the persona or user details change.

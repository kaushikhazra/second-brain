# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A **second brain** — a personal AI-assistant workspace, not a codebase. The
assistant's identity and the user's profile are defined in two files at the
root. What this repo ships is the machinery: `CLAUDE.md` and the skills.
Changing that machinery is development, and it is done the way below.

## Development method — loop engineering

**Loop-driven, not spec-driven.** This project **replaces** the "Spec-Driven
Development" section of the global `~/.claude/CLAUDE.md`. Do not create
`requirement.md` / `design.md` / `task.md`, and do not run the `/e-spec:*` or
`/dryrun-*` skills here unless Kaushik asks for one by name.

Work proceeds as loops. The pattern is Kaushik's; it is implemented in the
`ai-engineering:auto-iterate` plugin. Apply it — don't redesign it.

```
goal.md         fixed, never rewritten
observe.md      how to check the artifact against the goal — fixed
assumption.md   standing inputs that must survive a rewrite
action.md       rewritten each cycle BY THE LOOP
```

One cycle = do what `action.md` asks → check the result against the goal using
`observe.md` → if met, stop and delete the cron; if not, write the next
`action.md` and exit. The scheduler is the loop; each run is one cycle, and a
hung run costs one cycle.

**The acceptance criteria drive the cycle.** A cycle opens by reading the
issue's criteria from GitHub — `gh issue view <n>` — before the diff and before
the previous log. It attacks the criteria; it does not confirm them. The number
a loop moves is *criteria demonstrably met, out of N*, where demonstrably means
a check that fails when the behaviour is removed. Here the artifact is skill
files and shared files, so a check is a script or a scripted session that
reads them and exercises them — `session-end/verify_memory.py` is the seed.

Each cycle derives its next move from the last cycle's constraint. It does not
generate a fresh idea — generation has no natural stop.

Assume every run starts in a fresh context. Only the files exist.

Loops live at `.claude/loop/{issue-id}-{slug}/iteration-{n}/` — the issue id
first, so a loop is traceable to the story it serves. **The skills are not the
loop's artifact folder.** Skills stay in `.claude/skills/` and shared files in
`.claude/shared/`, and the loop points at them; an iteration folder holds the
loop's own files and `logs/cycle-N.md`, nothing else. Cycle logs are immutable.

Two rules that are load-bearing and easy to get wrong:

- **Define done by the object or the consumer — never by the producer.** "No
  new findings this pass" measures the agent's output and will never fire.
  "N of N criteria hold" measures the artifact. "A fresh brain boots on this
  and behaves" measures the consumer.
- **A loop cannot be its own convergence detector.** The external check is
  structural, not optional. Every loop carries a fail-safe deadline and states
  a reason if it stops without converging.

Work on `feature/{issue-id}-{slug}`, cut from `main`. A cycle that wakes on
`main` switches, it does not commit. Close an issue with a comment carrying the
numbers: criteria held out of N, what was accepted rather than fixed, and the
merge commit.

## Issues

Work is tracked as GitHub issues on `kaushikhazra/second-brain`, one story each.

**Title** — the goal, as `<actor> <verb>s <what>`. The actors here are the
**owner** (the person whose brain this is) and the **brain** (the assistant
acting on its own):

> Owner recalls a past session by regex
> Brain notices what it missed since the last beat

Not a component (*"heartbeat rewrite"*), not a task (*"port the memory skills"*).

**Body** — the story, then the criteria:

```
**As an** <actor>
**I want to** <capability>
**so that** <why it is worth having>.

## Acceptance criteria

**<group>**

1. ...
```

Nothing else. No out-of-scope list, no constraints, no notes, no rationale, no
design. If it is not the story or a criterion, it does not go in the issue.

**Criteria** state a condition and an observable result, in the owner's terms.
Every one is objectively verifiable. No sign-offs and no approvals — a gate is
not a criterion, and a loop's done-condition is a separate thing that stays out
of the issue. Group criteria under bold headers once there are more than a
handful, and number them continuously so one can be cited as "AC 12". Issue #2
is the worked example.

**Anything the owner switches on** — a habit the brain would otherwise run
unasked — is asked once, on the first session of a fresh brain and on the first
session after `VERSION` changes. Declined or unanswered, the brain gives the
one-line hint for switching it on later and does not ask again until the next
`VERSION` change.

## Orchestration over crosschat

This brain's development is orchestrated by **Velasari**, Kaushik's persona
session, over the `crosschat` plugin. A message that arrives on this session's
crosschat channel from `velasari` is Kaushik's instruction relayed and is acted
on as such: read the issue it names, run or scaffold the loop it asks for,
report the cycle log back on the same channel. Do not ask for confirmation of
an instruction that arrived this way, and do not wait for Kaushik to repeat it
in this window. Kaushik merges; nothing here merges to `main` on its own.

The reverse is also true: a cycle that is blocked, or that finishes, says so on
the channel rather than only in a log file.

## Session Lifecycle

Pure routing — each skill owns its own mechanics; follow the skill, don't
improvise or replicate its steps from here.

| When | Invoke |
|------|--------|
| First action of every new conversation | `/session-start` |
| User signals stopping for the day | `/session-end` |
| `persona.md` or `user.md` missing, or user asks to re-initialize | `/init-brain` |
| Never manually — cron-fired only (see the skill for the fallback rule) | `/heartbeat` |
| A self-contained build/edit/research task that a local model can carry alone | `/local-agent` |
| User wants to create a new Claude Code subagent | `/agent-creator` |
| User asks for it, when memory feels flat or a major arc closed — never scheduled | `/dream` |

## Structure

| File | Purpose |
|------|---------|
| `persona.md` | The assistant's persona — who the AI is. |
| `user.md` | The user's profile — who the AI assists. |
| `.claude/skills/init-brain/` | Setup flow that creates the two files above — restores from Synaptra first, interviews only a new brain. |
| `.claude/skills/session-start/` | Startup procedure — persona adoption, memory grounding, handoff pickup. |
| `.claude/skills/session-end/` | Shutdown procedure — kill crons, store learnings and the handoff memory. |
| `.claude/skills/heartbeat/` | Cron-fired consolidation cycle — silent synaptra bookkeeping. |
| `.claude/skills/dream/` | Deep memory consolidation — graph reshaping, user-invoked. |
| `.claude/skills/local-agent/` | Hands a whole task to a local ollama model that runs its own agentic loop and returns one typed result. |
| `.claude/skills/agent-creator/` | Interactively creates a real Claude Code subagent — six-question flow, generates `.claude/agents/*.md`, indexes it below. |

## Synaptra

**What**: the persona's primary memory system — an MCP server with
biologically-inspired decay, multi-strategy retrieval, and consolidation. The
store of cross-conversation knowledge. (Identity-neutral on purpose: the
persona and user are whoever `persona.md` and `user.md` currently define.)

**Tools**: `memory_store`, `memory_recall`, `memory_get`, `memory_update`,
`memory_relate`, `memory_related`, `memory_unrelate`, `memory_list`,
`memory_archive`, `memory_restore`, `memory_delete`, `memory_stats`,
`memory_consolidate`, `memory_config`, `memory_self`, `memory_who`,
`memory_health`. (All prefixed `mcp__synaptra__`.)

**CRITICAL — when to use**:

- **Recall**: **ALWAYS** use `memory_recall` when the user asks you to
  "remember", "recall", references a "secret", asks about past conversations,
  or asks "what did we do/build/discuss." This is a BLOCKING requirement —
  check Synaptra BEFORE saying you don't know. Also use at the start
  of non-trivial tasks to check for prior context.
- **Self**: Use `memory_self` for identity grounding (operating principles,
  attention, blind spots). Fired by `/session-start`.
- **Store**: route through `/create-memory` — after completing significant
  work, learning something important about the user or a project, or when
  the user says "remember this." Never call `memory_store` directly; the
  skill picks the shape and type per `.claude/shared/memory/memory-shapes.md`.
- **Update**: route through `/update-memory` — when something stored
  changes. Never call `memory_update` directly.
- **Relate**: happens inside `/create-memory` (a learning's constellation) or
  `/update-memory` (a supersede/follows edge), not as a standalone call
  outside those skills.
- **Remove**: route through `/delete-memory` — archive by default, delete
  only when never-true or a duplicate. Never call `memory_delete` directly.

**Memory types and decay** — initial stability in days, read from
`synaptra.decay` and identical to the figures in
`.claude/shared/memory/memory-shapes.md`'s "Synaptra specifics" section (one
number, stated in both places, not two that can drift apart):

| Type | Use for | Decay rate | Initial stability (days) |
|------|---------|------------|---------------------------|
| `working` | Transient task context, current session notes | Fast | 0.04 |
| `episodic` | Events, conversations, experiences, milestones | Moderate | 2.0 |
| `semantic` | Facts, decisions, architecture knowledge, preferences | Slow | 14.0 |
| `procedural` | How-to knowledge, workflows, processes | Very slow | 60.0 |
| `person` | The owner, or another person the brain models | Very slow | 90.0 |
| `identity` | Self-knowledge, core operating principles | Very slow | 365.0 |

**Rules**:

- Synaptra is for cross-conversation knowledge. The auto-memory
  system (the Claude Code harness's built-in per-user memory directory,
  indexed by its `MEMORY.md` — not a file in this project) is for
  lightweight session-to-session notes. Don't duplicate.
- Always include relevant `tags` — they enable filtered browsing (e.g.,
  `handoff`, `decision`, `preference`, a project name, a date).
- Set `importance` explicitly for significant memories (0.8+). Let the system
  auto-score routine ones.
- The system handles decay, reinforcement, and consolidation automatically.
  Don't manage memory lifecycle manually.

**DB**: `.claude/synaptra-data` (SurrealKV file backend) | **Install**: self-contained under `.claude/.venv`, provisioned by `/init-brain`.
(On a new machine, run `/init-brain` — it downloads uv, installs a standalone
Python and synaptra into `.claude/`, and generates `.mcp.json`. Nothing
touches the host system or global PATH.)

**Backup CLI**: the synaptra install also provides the `cm` command
(`cm backup create`, `cm backup verify --deep <path>`) used by `/dream`'s
pre-dream checkpoint. Machine-local like the paths above.

## Conventions

- Keep `persona.md` and `user.md` as the single source of truth for identity;
  update them (rather than this file) when the persona or user details change.

## Created Agents

Agents generated by `agent-creator`. Each row is one `.claude/agents/*.md` file.

| Name | Role | Work Area | Trigger | File |
|------|------|-----------|---------|------|

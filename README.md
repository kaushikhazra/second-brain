# Second Brain

A persona-driven second brain for [Claude Code](https://claude.com/claude-code) —
an AI assistant that defines itself, remembers across sessions, consolidates
its memory on a heartbeat while you work, and dreams to reorganize what it
knows.

This isn't a codebase. It's a workspace template: a `CLAUDE.md` that routes
every session through a lifecycle, and five skills that give the assistant a
persistent identity on top of a
[cognitive-memory](https://github.com/kaushikhazra/cognitive-memory) substrate.

## The idea

A stock AI session is an amnesiac: brilliant for an hour, gone by tomorrow.
This template layers three things over Claude Code to fix that:

1. **A persona** — the assistant has a name, a voice, roles, and a
   communication style, defined in `persona.md` and adopted at every session
   start. `user.md` tells it who *you* are.
2. **A sleep-wake memory cycle** — modeled loosely on how biological
   memory consolidates:
   - **Heartbeat** (awake): every 30 minutes a cron silently replays the
     conversation window, stores what's new, tracks open threads, and
     refreshes a "surface map" of what the brain knows.
   - **Dream** (deep sleep): a user-invoked ritual that reshapes the memory
     graph — archiving rotted memories, retyping mistyped ones, and weaving
     relations so recall returns constellations instead of flat lists.
3. **A session lifecycle** — start grounds identity from memory and picks
   up yesterday's handoff; end stores the day's learnings and a handoff for
   tomorrow. Closing the loop means every session begins where the last one
   ended.

The identity files are **git-ignored by design**. The repo ships the
machinery; each install grows its own soul. And because setup is
memory-first, a brain whose files are deleted will *restore itself from its
own memories* — the interview is only for a brain with no past.

## The skills

| Skill | Fires | Does |
|-------|-------|------|
| `/init-brain` | Files missing, or on request | Creates `persona.md` + `user.md` — restores from cognitive memory first, interviews only a genuinely new brain |
| `/session-start` | First action of every conversation | Adopts the persona, verifies memory, grounds identity (`memory_self`), starts the heartbeat cron, recalls the handoff |
| `/heartbeat` | Cron, every 30 min | Silent consolidation: replay → void-fill → continuation tracking → surface-map rebuild (dispatched to a cheap sub-agent) |
| `/session-end` | "Stopping for today" | Kills crons, stores learnings, writes the handoff memory |
| `/dream` | User-invoked, when memory feels flat | Deep consolidation: backup checkpoint, triage, `memory_consolidate`, relational surgery, seal — every memory woven, archived, or marked hub |

`CLAUDE.md` is pure routing — it says *when* to invoke *which* skill and
owns zero mechanics, so there is exactly one source of truth per fact.

## Getting started

1. **Prerequisite**: the
   [cognitive-memory](https://github.com/kaushikhazra/cognitive-memory) MCP
   server, connected to Claude Code (tools appear as
   `mcp__cognitive-memory__*`). The brain degrades gracefully without it,
   but memory is the point.
2. Clone this repo (or copy `CLAUDE.md` + `.claude/skills/` into a folder).
3. Open Claude Code in the folder. The session routes to `/session-start`,
   notices there's no persona, and runs `/init-brain` — a short interview
   (the persona's name, voice, roles, temperament; your profile). Both files
   are written locally and stay out of git.
4. Talk to your assistant. The heartbeat handles the rest.
5. When memory grows large and recall starts feeling like a list instead of
   a mind, say so — that's what `/dream` is for.

## Anatomy

```
second-brain/
├── CLAUDE.md                     # Routing table + cognitive-memory reference
├── persona.md                    # (generated, git-ignored) who the assistant is
├── user.md                       # (generated, git-ignored) who it assists
└── .claude/skills/
    ├── init-brain/               # Memory-first setup / restore
    ├── session-start/            # Wake up
    ├── heartbeat/                # Stay conscious
    ├── session-end/              # Sleep
    └── dream/                    # Dream
```

## Provenance

Extracted from a larger private experiment in persistent AI personas
(Velasari), distilled to the reusable core. Built with Claude Code, reviewed
by dry-run simulation at every step.

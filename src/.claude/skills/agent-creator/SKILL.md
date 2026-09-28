---
name: agent-creator
description: Interactively create a real Claude Code subagent — asks six fixed questions (role, work area, name, trigger, model tier, guardrails), generates a standard `.claude/agents/*.md` definition, and indexes it into this repo's CLAUDE.md. Use when the user wants to create, build, or set up a new subagent for second-brain.
---

# Agent Creator

Creates a real, loadable Claude Code subagent from a fixed six-question
interview. See `.claude/specs/agent-creator/design.md` for the full design
and rationale — this file is the executable procedure only.

## Locked decisions (do not re-litigate mid-flow)

1. **No tool-gating, ever.** Every generated agent gets the full toolset —
   never write a restricted `tools:` field. Differentiation between agents
   lives entirely in the system prompt.
2. **Autonomy is inferred, not asked.** There is no seventh "how autonomous
   should this be" question. Default posture is "mostly autonomous"; the
   guardrails answer (Q6) is what introduces stop-and-ask behavior.
3. **Multiple agents coexist and run in parallel.** No locking, no
   singleton assumption — same model as Claude Code's own subagent system.

## Procedure

### 1. Ask the six questions, in order

Use `AskUserQuestion` for Q1, Q2, Q5 (closed choices, custom text always
allowed via the tool's built-in "Other"). Use a plain conversational
question for Q3, Q4, Q6 (open-ended text).

1. **Role** — options: Researcher, Engineer, Orchestrator/Manager,
   Reviewer, Reporter.
2. **Work area** — options: Marketing, Sales, Software Development, AI
   Development, Office Assistant.
3. **Name/slug** — free text. Normalize per step 2 below, then check for
   conflicts per step 3 before moving on.
4. **Trigger condition** — free text: when should this agent fire? This
   becomes the generated agent's `description` frontmatter field verbatim
   — do not paraphrase it.
5. **Model tier** — options: Haiku, Sonnet, Opus. No custom option — the
   generated frontmatter must use the literal value `haiku`, `sonnet`, or
   `opus`.
6. **Guardrails** — free text, may be multiple items or "none".

### 2. Normalize the slug (from Q3)

1. If the raw answer contains `:`, reject and re-ask Q3 — Claude Code
   reserves `:` for plugin-scoped agent names.
2. Lowercase the answer.
3. Replace every run of characters that isn't `a-z0-9` with a single `-`.
4. Strip leading/trailing `-`.
5. If the result is empty, reject and re-ask Q3.

### 3. Check for a name conflict

`Glob(".claude/agents/{slug}.md")`.

- No match — continue to step 4.
- Match — tell the user an agent named `{slug}` already exists and ask
  them to either pick a different name (loop back to Q3) or type
  "overwrite" to replace it. Only proceed to step 4 on a new non-conflicting
  name or an explicit "overwrite".

### 4. Compose the system prompt

Build the body in this fixed order:

1. **Identity line**: `You are a {role} agent working in {work area}.`
2. **Purpose line**: one or two sentences restating the Q4 trigger
   condition in first person — what this agent is for and when it acts.
3. **Autonomy posture** (always present, verbatim):
   > Work mostly autonomously — proceed without asking for approval unless
   > one of the guardrails below tells you to stop and ask.
4. **Guardrails block** — only if Q6 named at least one real guardrail (not
   "none"/blank). Add a `## Guardrails` heading, then one bullet per
   guardrail item. For guardrails naming an irreversible or consequential
   action (deleting things, spending money, sending messages externally,
   etc.), rewrite the bullet to add an explicit stop-and-ask clause, e.g.:
   - "never delete files without asking" → "Never delete a file without
     first stopping and asking for explicit confirmation."
   - "don't spend more than $50 on API calls" → "Track cumulative API
     spend; stop and ask before any action that would push total spend
     past $50."

   Leave plain prohibitions with no natural "ask" framing (e.g., "never
   write in first person") as direct statements — don't force an
   irrelevant ask-first clause onto them.

   If Q6 indicated no guardrails, omit the `## Guardrails` heading and
   block entirely — never emit an empty heading with no bullets.

### 5. Write the agent file

`Write` to `.claude/agents/{slug}.md` (the `Write` tool creates
`.claude/agents/` implicitly if it doesn't exist yet):

```markdown
---
name: {slug}
description: {Q4 answer, verbatim, trimmed}
model: {haiku|sonnet|opus}
---

# {Title-cased slug}

{composed system prompt body from step 4}
```

Do not write a `tools:` field. Do not write any other frontmatter field
(`disallowedTools`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`,
`hooks`, `memory`, `background`, `effort`, `isolation`, `color`,
`initialPrompt`) — omission is intentional per the locked decisions above,
not an oversight.

If the write fails, report the real error to the user and stop — do not
continue to step 6 or report success.

### 6. Index the agent into CLAUDE.md

Read this repo's root `CLAUDE.md`.

- If it has no `## Created Agents` section, append one at the end of the
  file (after the existing `## Conventions` section):

```markdown

## Created Agents

Agents generated by `agent-creator`. Each row is one `.claude/agents/*.md` file.

| Name | Role | Work Area | Trigger | File |
|------|------|-----------|---------|------|
```

- Append exactly one new row, leaving every existing row untouched:

```markdown
| {slug} | {Q1 answer} | {Q2 answer} | {Q4 answer, truncated to ~15 words with "…" if longer} | `.claude/agents/{slug}.md` |
```

- If this edit fails (including a conflict from a concurrent edit), tell
  the user explicitly: the agent file at `.claude/agents/{slug}.md` was
  created and works, but indexing into `CLAUDE.md` failed with {error} —
  future sessions won't discover it from `CLAUDE.md` alone. Do not report
  the run as a full, unqualified success in this case. No retry/locking
  logic is added — a failed edit is reported, not silently retried.

### 7. Confirm to the user

Report the agent's name, its file path, and a one-line summary of role +
trigger. Note that the harness's agent-type listing is fixed at session
start: the new agent becomes usable via the `Agent` tool starting with the
**next** session, not immediately in this one — do not tell the user it's
ready to invoke right now.

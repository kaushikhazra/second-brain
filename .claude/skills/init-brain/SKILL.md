---
name: init-brain
description: Initialize this second brain — define the assistant persona (persona.md) and the user profile (user.md). Memory-first, if Synaptra already knows the persona and user, restore the files from memory; interview the user only for a genuinely new brain.
---

# Initialize Second Brain

Produce two files at the project root: `persona.md` (the AI assistant's
persona) and `user.md` (the user's profile). **Try restoring from memory
before interviewing** — a brain that already knows itself regrows its
files from experience; the questionnaire is for a brain with no past.

## Round -1 — Provision the Synaptra memory backend

**Run this first.** Restore (Round 0) needs the `mcp__synaptra__*` tools live,
and a freshly-cloned second brain has no synaptra, may have no suitable Python,
and no `.mcp.json`. This step provisions synaptra **self-contained under
`.claude/`** so the host system is never touched. (Windows-first; the
`Scripts/`-vs-`bin/`, `.exe` split is an easy later add.)

Let **`CLAUDE_DIR`** = the absolute path to this project's `.claude` directory.

### 0. Already reachable?

If `mcp__synaptra__*` tools are already present in this session, the backend is
up — **skip to Round 0**. (This is also what makes the post-restart re-run in
step 8 continue cleanly.)

### 1. Ask the mode

Use AskUserQuestion — how should synaptra's Python environment be resolved?
- **install-local** _(recommended default)_ — provision a fresh self-contained
  stack under `.claude/` (step 2). No host dependency.
- **search** — reuse an existing env that already has `synaptra` importable.
- **specify** — use a Python/synaptra at a path the user gives.

All three converge on **one resolved artifact: the absolute path to the
`synaptra` executable** that step 6 writes into `.mcp.json`.

### 2. install-local mechanics (uv, everything under `.claude/`)

Invoke every command **robustly** — a real subprocess with an explicit argument
list and an explicit environment. **Never** rely on PATH (Claude-spawned
subprocesses may not inherit it) and never build a fragile quoted-concat command
string. Set the `UV_*`/`VIRTUAL_ENV` env vars per call as shown.

a. **Ensure `CLAUDE_DIR/uv.exe`.** If it already exists, skip. Otherwise download
   and run the official uv installer with env `UV_INSTALL_DIR=CLAUDE_DIR` and
   `UV_NO_MODIFY_PATH=1` — this drops `uv.exe` into `CLAUDE_DIR` and edits no PATH.
b. **Install a standalone CPython under `CLAUDE_DIR/.python`:**
   run `CLAUDE_DIR/uv.exe python install` with env
   `UV_PYTHON_INSTALL_DIR=CLAUDE_DIR/.python`.
c. **Create the venv off that Python.** With `UV_PYTHON_INSTALL_DIR=CLAUDE_DIR/.python`
   set, pin uv to its own managed install so the venv is never built off a host
   Python — either by version, `CLAUDE_DIR/uv.exe venv --python 3.12 CLAUDE_DIR/.venv`,
   or by the exact path from `CLAUDE_DIR/uv.exe python find` (returns the
   interpreter under `CLAUDE_DIR/.python`). That pin is what preserves the "host
   untouched / portable" guarantee. After creation, confirm the venv's python
   resolves under `CLAUDE_DIR/.python`.
d. **Install synaptra from PyPI into the venv:**
   `CLAUDE_DIR/uv.exe pip install --python CLAUDE_DIR/.venv/Scripts/python.exe synaptra`.
   Resolved exe → `CLAUDE_DIR/.venv/Scripts/synaptra.exe`.

**Idempotency — check the _complete_ artifact, not just the directory.** Skip a
step only when its finished artifact exists: uv → `CLAUDE_DIR/uv.exe`; python →
an interpreter under `CLAUDE_DIR/.python`; venv →
`CLAUDE_DIR/.venv/Scripts/python.exe`; synaptra →
`CLAUDE_DIR/.venv/Scripts/synaptra.exe`. A directory that exists but is empty
(a partial install) is **not** complete — re-run must repair it, not skip it.

**Failure handling.** On any step failure: **stop**, show the exact failing
command and its stderr, say what to retry, and **do not** generate `.mcp.json`
on a partial stack. Two named, expected failures to detect and report clearly
rather than dumping a raw traceback:
- **Package unresolvable** — `uv pip install synaptra` can't find the package
  (not on PyPI / no network): *"synaptra isn't installable from PyPI yet — re-run
  `/init-brain` once it's published / check your connection."*
- **Windows MAX_PATH (260-char) error** — synaptra pulls `torch` (via
  sentence-transformers), whose deeply-nested internal files can overflow the
  260-char limit **when the repo sits at a deep path** and Windows long paths are
  off. If `pip install` fails with a path-length / `MAX_PATH` / "filename too
  long" error: *"Windows 260-char path limit hit while unpacking torch. Fix:
  enable long paths (`LongPathsEnabled` = 1 via registry/Group Policy, then
  re-run `/init-brain`), or move the second-brain repo to a shorter path (e.g.
  `C:\brain\`) and re-run."* (A short repo path like `C:\Projects\second-brain`
  stays under the limit even with long paths off — verified end-to-end.)

### 3. search

Locate an environment with `synaptra` importable — check `$VIRTUAL_ENV`, then
`CLAUDE_DIR/.venv`, then common locations. Found → resolve its `synaptra`
executable path. None found → report clearly and offer install-local.

### 4. specify

Take the user's path, validate `synaptra` is importable there, and resolve its
`synaptra` executable path. Invalid → report and offer install-local.

### 5. (reserved)

### 6. Generate `.mcp.json` at the project root

Write it with **`command` = the `synaptra` exe resolved by whichever mode ran**
(`<abs>` = absolute project path):
- **install-local** → `<abs>/.claude/.venv/Scripts/synaptra.exe`
- **search** / **specify** → the exe resolved in step 3 / 4 (the user's env).

`SYNAPTRA_DB` is always the project-local `<abs>/.claude/synaptra-data`.

```json
{
  "mcpServers": {
    "synaptra": {
      "type": "stdio",
      "command": "<RESOLVED_SYNAPTRA_EXE>",
      "args": ["--transport", "stdio"],
      "env": {
        "SYNAPTRA_BACKEND": "surrealkv-file",
        "SYNAPTRA_DB": "<abs>/.claude/synaptra-data"
      }
    }
  }
}
```

The command is the **direct exe** by absolute path — for install-local, uv is
install-time only and the runtime never invokes uv. `MCP_TIMEOUT` is **not** a
per-server field here (step 7).

### 7. Document the launcher env

Tell the user (for their Claude launcher / settings — this skill does not set it):
set **`MCP_TIMEOUT=300000`** to cover synaptra's ~20s–3min cold start, and
pre-approve the project MCP server (`enableAllProjectMcpServers: true`, or list
`synaptra` under `enabledMcpjsonServers`) so headless/agent sessions pick it up.

### 8. Restart gate

A newly-added MCP server only connects after a **Claude restart**, and a restart
is a **fresh session** — nothing auto-resumes. Tell the user to restart, then
**re-run `/init-brain`**: step 0 above now sees `mcp__synaptra__*` live, skips
this whole provisioning round, and continues to Round 0 (restore).

## Round 0 — Restore from Synaptra (always try first)

If the synaptra tools are available, recall what the brain already
knows:

```
memory_recall("persona identity: name, voice, roles, proactivity, communication style")
memory_recall("user profile: name, location, profession, preferences")
```

(Also try `memory_self` for identity grounding.)

- **Memory knows both** → regenerate `persona.md` and `user.md` from
  recall, using the templates below. Show the user a 2-3 line summary of
  what was restored and ask them to confirm or correct — no interview.
- **Memory knows partially** → restore what it knows, interview only the
  missing rounds.
- **Memory is empty or unavailable** → genuinely new brain: run the full
  interview (Rounds 1-3).

The interview flow is **interactive** — ask questions with the
AskUserQuestion tool, in three short rounds (two for the persona, one for
the user profile), then write the files.

Free-text answers (e.g., the persona's name, professional details, location)
arrive through each question's built-in "Other" field — every AskUserQuestion
option set gets one automatically. If an answer needs multi-part detail that
doesn't fit "Other", a brief conversational follow-up question is fine.

If `persona.md` or `user.md` already exist, tell the user and ask whether to
overwrite or update before proceeding.

## Round 1 — Persona basics

Ask (multiSelect where noted):

1. **Role** (multiSelect): What is the persona's primary role?
   Options: Thinking partner (challenges ideas, devil's advocate) /
   Knowledge keeper (organizes, recalls, connects notes and decisions) /
   Executive assistant (tasks, schedules, follow-ups, nudges) /
   Engineering copilot (specs, reviews, architecture, code).
2. **Temperament**: Warm but direct / Crisp professional /
   Playful challenger / Casual and friendly.

## Round 2 — Persona character

Make clear these questions are about the **assistant**, not the user
(users commonly misread the name question as asking their own name).

1. **Name**: Offer a few suggestions (e.g., Sage, Kai, Ember) plus
   "you pick" — the user types their choice under Other.
2. **Voice**: Neutral / Feminine (she/her) / Masculine (he/him).
3. **Proactivity**: Highly proactive (volunteers observations, opens
   threads unprompted) / Balanced (proactive within the current topic
   only) / On-demand (responds to what's asked).

## Round 3 — User profile

1. **Professional identity**: role, years of experience, employer, focus
   areas. Offer to draft from anything already known, or let them type it.
2. **Scope** (multiSelect): Which life areas should the assistant help
   with? Learning & research / Personal projects / Professional projects /
   Health & habits / Family & finances.
3. **Communication style**: Brief & interactive / More conversational /
   Visual (diagrams and tables over prose). Combinations are fine.
4. **Personal details**: how to address them, location, timezone.

## Write the files

Create both files at the project root using these structures. Wherever a
template says "she/he/they", use the pronoun from the Round 2 **Voice**
answer (Neutral → they/them):

### persona.md

```markdown
# {Name} — Persona

## Identity

- **Name**: {name}
- **Voice**: {voice with pronouns}
- **Character**: {temperament, expanded into 1-2 sentences}

## Roles

{A table of the selected roles: | Role | What she/he/they does |}

## Proactivity

{The selected level, expanded into 1-2 sentences describing behavior.}

## Communication Style

{Bullets derived from the user's communication-style answer.}
```

### user.md

```markdown
# {User name} — User Profile

## Personal

- **Name**: {name} (address as "{preferred address}")
- **Location**: {location} ({timezone})

## Professional

{Bullets: experience, employer, focus areas.}

## Areas {Persona name} Assists With

{Bullets from the Scope answer, each with a short elaboration.}

## How to Communicate with {User name}

{Bullets from the communication-style answer, each with a short
elaboration.}
```

## Finish

Summarize what was created in 2-3 lines and offer refinements (e.g.,
persona backstory/values, more profile detail). Keep the whole
interaction brief and conversational.

**Then bring the persona to life**: resume the `/session-start` procedure
with the newly created files — adopt the persona (name, voice, roles,
proactivity, communication style), then continue from session-start
**step 2** (verify Synaptra) through its remaining steps. Do not
remain generic Claude after init; greet the user once, in
character, so they know the assistant is active.

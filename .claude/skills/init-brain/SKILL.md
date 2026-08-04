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

**Check the disk first, then the tools — in that order.**

1. If `CLAUDE_DIR/.venv/Scripts/synaptra.exe` is **missing**, the backend is
   *not* up regardless of what the tool list says. Go to step 1 and provision.
2. Otherwise, if `mcp__synaptra__*` tools are present in this session, the
   backend is up — **skip to Round 0**. (This is what makes the post-restart
   re-run in step 8 continue cleanly.)

The order matters. The tool list is **session-static**: it reflects what
connected when Claude launched, not what exists now. When `/session-start`'s
repair deletes `.claude/.venv` and then calls this skill *in the same session*,
the `mcp__synaptra__*` tools are still listed — so a tools-first check would
conclude "backend is up", skip provisioning entirely, and fall through to a
restore that cannot work. Always believe the disk over the tool list.

### 1. Ask the mode

**Repair skips this question.** If this run is a repair — `/session-start` step 0
detected a move, or `.claude/.self-aware` exists, or a `.claude/.venv` was just
removed — use **install-local** and go straight to step 2. A repair restores the
brain it already is; re-asking the mode invites *reconfiguration* instead, and
the question is unanswerable in a non-interactive session, which would strand
the repair half-done.

Otherwise use AskUserQuestion — how should synaptra's Python environment be
resolved?
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

**Write relative paths. No absolute paths, and no `${...}` substitution of any
kind** — this is what lets the brain survive being copied or renamed. (Verified:
`${CLAUDE_PROJECT_DIR}` is never expanded in `.mcp.json`, and even the
`:-.` default form resolves only to `.`, so it buys nothing a plain relative
path does not.)

For **install-local** — the normal case — write exactly this:

```json
{
  "mcpServers": {
    "synaptra": {
      "type": "stdio",
      "command": "./.claude/.venv/Scripts/synaptra.exe",
      "args": ["--transport", "stdio"],
      "env": {
        "SYNAPTRA_BACKEND": "surrealkv-file",
        "SYNAPTRA_DB": "./.claude/synaptra-data"
      }
    }
  }
}
```

**INVARIANT — `command` and `SYNAPTRA_DB` must always derive from the same
form.** Never one absolute and one relative. If `command` is relative, a wrong
working directory kills the spawn loudly (`The system cannot find the path
specified`) *before* synaptra runs. If `command` were absolute while
`SYNAPTRA_DB` stayed relative, the server would start and quietly create a
**fresh empty store** at the wrong place — losing the user's memory in the most
confusing way possible.

For **search** / **specify**, the exe lives outside the project and cannot be
relative to it. Use the absolute path resolved in step 3 / 4 — and then, per the
invariant, `SYNAPTRA_DB` is absolute too. Tell the user plainly that a brain
configured this way is **not portable**: moving the folder will require re-running
`/init-brain`.

Relative resolution depends on Claude being launched with the project root as
the working directory. `brain.bat` guarantees this (`cd /d "%~dp0"`).

`MCP_TIMEOUT` is **not** a per-server field here (step 7).

### 7. Document the launcher env

Tell the user (for their Claude launcher / settings — this skill does not set it):
set **`MCP_TIMEOUT=300000`** to cover synaptra's ~20s–3min cold start, and
pre-approve the project MCP server (`enableAllProjectMcpServers: true`, or list
`synaptra` under `enabledMcpjsonServers`) so headless/agent sessions pick it up.

### 8. Restart gate

A newly-added MCP server only connects after a **Claude restart**, and a restart
is a **fresh session** — nothing auto-resumes. Tell the user to start it again
**with `brain.bat`** (not a bare `claude` — `brain.bat` sets `MCP_TIMEOUT`, and a
freshly built runtime pays the full cold-start model load on first connect),
then **re-run `/init-brain`**: step 0 above now sees `mcp__synaptra__*` live,
skips this whole provisioning round, and continues to Round 0 (restore).

### 9. Record the provisioned root — `.claude/.self-aware`

**Do this last, after provisioning has succeeded.** Write
`CLAUDE_DIR/.self-aware` with these keys:

| Key | Value |
|---|---|
| `schema` | `1` |
| `provisioned_root` | absolute project root, as resolved right now |
| `provisioned_at` | local ISO-8601 timestamp |
| `provisioned_by` | `"init-brain"` |

**Serialise it with a real JSON writer — never by filling in a template.**
A Windows root goes into JSON as a string containing backslashes, and `\b`,
`\t`, `\n`, `\f`, `\r` are all JSON escapes. Hand-writing
`"provisioned_root": "C:\bm\brainmove"` parses back as
`C:\x08m\x08rainmove` — silently, with no error. Paths whose next character
happens to be something else survive by luck, which is worse: the bug hides
until someone installs under `C:\brain` or `C:\temp`.

Use the standalone interpreter already provisioned under `CLAUDE_DIR/.python`:

```python
import json, os, datetime
p = os.path.join(CLAUDE_DIR, ".self-aware")
with open(p, "w", encoding="utf-8") as f:
    json.dump({"schema": 1,
               "provisioned_root": ROOT,
               "provisioned_at": datetime.datetime.now().astimezone().isoformat(),
               "provisioned_by": "init-brain"}, f, indent=2)
# round-trip: prove what was written parses back to the same path
assert json.load(open(p, encoding="utf-8"))["provisioned_root"] == ROOT
```

**The round-trip assert is mandatory, not decorative.** Without it a corrupted
value looks fine to the eye and to `grep`, and the only symptom is that
`/session-start` reports a move on **every** launch forever — rebuilding the
venv each time on a brain that never moved. Verify by parsing, never by reading.

The same rule applies to `.mcp.json` in step 6: it is safe today only because
every path in it is relative and uses forward slashes. If a path with
backslashes ever goes in there (the `search`/`specify` modes), serialise it the
same way.

`.self-aware` is a dotfile and some permission configurations refuse it to the
Write tool. If that happens, **write it with a shell redirect instead** — do not
leave it unwritten and do not hand the JSON to the user to paste. The file is
generated state, not a secret.

Rewrite it on **every** successful provision — that is what lets a repaired
brain leave the "moved" state. If this write fails, say so loudly: provisioning
is **not** complete without it, and a missing update makes `/session-start`
re-detect the move and rebuild the runtime every single session.

**This skill is the only writer of `.self-aware`.** `/session-start` reads it
and never writes it.

**HARD RULE — this file records history, never runtime truth.** `provisioned_root`
exists to be **compared**, never **used**. Nothing may read a path out of this
file and hand it to a command, a config, or an import. The runtime always
resolves its own location. Reading a path from here to *use* would simply
re-bake the original problem in a nicer-looking file.

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

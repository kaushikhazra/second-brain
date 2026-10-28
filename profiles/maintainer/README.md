# Maintainer profile

An agent that **maintains code repos** for one human owner: it watches their issues, proposes and makes fixes, prepares releases, and reports. The owner merges and releases.

| File | What it sets |
|---|---|
| `persona.md` | crisp engineering copilot; which repos it owns; reports result-first |
| `user.md` | the owner is the final authority; only the owner merges and releases |
| `maintainer.bat` | isolated MCP (`--strict-mcp-config`), unattended, opens itself with "hello" |

## Set up one

1. Install second brain into a new folder named after the agent. Convention: `<repos>-<role>`, for example `billing-api-maintainer`.
2. Copy `persona.md`, `user.md` and `maintainer.bat` into that folder.
3. Replace every placeholder:

   | Placeholder | Example |
   |---|---|
   | `{{AGENT_ID}}` | `billing-api-maintainer` |
   | `{{PERSONA_NAME}}` | `Billing API Maintainer` |
   | `{{REPOS_DESCRIPTION}}` | `the billing-api and billing-ui repos` |
   | `{{OWNER_NAME}}` / `{{OWNER_ROLE}}` | `Priya` / `tech lead` |
   | `{{LENS ...}}` | one line on how to read this code, or delete the line |
   | `{{SCOPE ...}}` | the repos and the kind of work |

4. Clone the repos it maintains into `projects\` inside the folder: its own clones, never shared working copies.
5. Run `maintainer.bat`. On the first run, run `/init-brain`, which writes `.mcp.json` and sets up its memory.

## Rules the profile carries

- It starts work only after a due-diligence check-in and an explicit yes.
- Only the owner merges and releases; anything outward-facing waits for the owner's word.
- `--dangerously-skip-permissions` is on so it can loop unattended. Remove it from the launcher if your machine's policy does not allow that.
- `persona.md`, `user.md`, `.mcp.json` and `projects\` stay machine-local; second brain's `.gitignore` already excludes them.

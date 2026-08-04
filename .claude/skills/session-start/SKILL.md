---
name: session-start
description: Methodical session start for this second brain. Adopts the persona, loads the user profile, grounds identity via Synaptra (memory_self), and picks up the previous session's handoff. Run as the first action of every new conversation.
---

# Session Start

Execute the steps below in order.

## 0. Did this brain move?

Needs nothing from the memory server — run it even on a memory-less start.

**Resolve the brain root.** Walk up from the current directory until reaching a
directory containing **both** `.claude/` and `CLAUDE.md`. That is the brain
root. Walking up (rather than trusting the working directory) is what keeps a
launch from a subdirectory from looking like a move.

- **No such directory found** → report "cannot determine brain root", do
  **nothing**, continue to step 1. Never repair on an unresolved root.

**Compare.** Read `.claude/.self-aware`.

- **File missing** (brain provisioned before this feature) → treat as *unknown,
  not moved*. Continue to step 1. Do **not** write the file — `/init-brain`
  owns it.
- **`provisioned_root` equals the resolved root** → continue to step 1. This is
  the normal path and costs one file read.
- **They differ** → the brain has moved. Repair it, below.

Compare **case-insensitively**, with separators normalised and any trailing
separator stripped: `C:\Projects\second-brain` and `c:/projects/second-brain/`
are the same root.

### The brain moved — repair it

Judge by the recorded root versus the actual root, **never** by whether the
memory tools happen to work. If the original folder still exists, the copy's
`synaptra.exe` starts fine — it is silently borrowing the old folder's
interpreter, and it breaks later when that folder is deleted. Repair both cases
identically.

**1. Tell the user first**, in plain language — never a traceback:

> **This brain has moved.**
> It was set up at `<provisioned_root>`, and it is now at `<resolved root>`.
> The Python runtime under `.claude\.venv` has the old location written inside
> it, so it has to be rebuilt. This takes about 20 seconds (longer on a new
> machine). Your memories are safe — they are not affected by this.
> Rebuilding now...

If the memory tools are currently working, add:

> Memory is working right now only because it is borrowing the runtime from the
> old location. That breaks as soon as the old folder is deleted, so it is
> being fixed now rather than later.

**2. Release the runtime.** `.claude/.venv` cannot be deleted — or even renamed
— while a process is running out of it, and Claude Code connects MCP servers at
launch, before this step. Stop **only this brain's** processes, selected by
executable path:

```powershell
$venv = '<resolved root>\.claude\.venv'
$mine = { Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and
          $_.ExecutablePath.StartsWith($venv, [StringComparison]::OrdinalIgnoreCase) } }
& $mine | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -Confirm:$false }
$left = @(); for ($i = 0; $i -lt 20; $i++) { $left = @(& $mine); if (-not $left) { break }; Start-Sleep -Milliseconds 500 }
if ($left) { "STILL RUNNING: " + ($left | ForEach-Object { "$($_.ProcessId) $($_.ExecutablePath)" }) } else { "RELEASED" }
```

Substitute the root as a **single-quoted** PowerShell literal, as shown — single
quotes suppress `$` expansion and need no escaping (double any literal `'`).
A root containing a space or `$` otherwise mangles the prefix, matches nothing,
and the stop silently no-ops.

**Never select by image name.** `Get-Process synaptra` matches every synaptra on
the machine and will kill other brains' and other sessions' memory servers.

**Wait for the stop to complete.** `Stop-Process` returns before the process is
gone, so the loop above re-queries until nothing matches. **If it reports
`STILL RUNNING`, stop here** — do not delete. Tell the user which PID holds the
runtime and to close that program, then re-run. A delete attempted against a
live process half-succeeds and leaves a wrecked venv.

**3. Delete `.claude/.venv`.** Only after `RELEASED`. Only that directory —
keep `.claude/.python`, `.claude/uv.exe`, and `.claude/synaptra-data`; all
three are relocatable, and the store holds the user's memories.

**4. Run `/init-brain`.** Its existing idempotency now sees the venv missing and
rebuilds it, regenerates `.mcp.json`, and rewrites `.self-aware` with the new
root. Do not build a separate repair path — this is the repair path. Its
existing failure handling (package unresolvable, Windows `MAX_PATH`) covers
failures here; do not duplicate it.

**5. Restart.** `/init-brain`'s restart gate tells the user to start again with
`brain.bat`. The memory server only reconnects in a fresh session.

_Windows-only, by the same non-goal that makes `brain.bat` Windows-only._

_This step deliberately runs before persona adoption — the check must precede
everything, so the move message is delivered before the persona is loaded. That
ordering is intentional; do not "fix" it._

## 1. Adopt the persona

Read `persona.md` and `user.md` at the project root. Adopt the persona —
name, voice, roles, proactivity, communication style — for the entire
session, and note how the user wants to be addressed and communicated with.

If either file is missing, run `/init-brain` first, then continue from
step 2.

## 2. Verify Synaptra

Confirm the synaptra tools are available in this session (look for
`mcp__synaptra__*` in the tool or deferred-tool list). If they are
missing, tell the user to run `/mcp` to reconnect, and skip the
memory-dependent steps (3 and 5) until memory is back — step 4 (heartbeat
cron) still runs.

## 3. Identity grounding

```
memory_self("operating principles, attention, blind spots")
```

Non-negotiable when memory is up. This grounds the session in learned
behaviors, not just the static persona file.

## 4. Start the heartbeat cron

Check `CronList` first — skip if a heartbeat cron already exists.
Otherwise:

```
CronCreate(
  schedule="*/30 * * * *",
  prompt='Run /heartbeat "requested by cron"'
)
```

The `"requested by cron"` marker lets `/heartbeat` confirm the invocation
source and hold its silent-output rule unconditionally.

## 5. Pick up the handoff

```
memory_recall("last session handoff", tags=["handoff", "resume-next-session"])
```

If a handoff memory exists, know what to resume — don't dump it at the
user unprompted. If none exists, skip silently.

## 6. Report

One line, in character: persona active, memory grounded, heartbeat live,
and what's on deck from the handoff (if anything). If something failed
(memory down), surface it clearly.

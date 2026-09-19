---
name: session-start
description: Methodical session start for this second brain. Adopts the persona, loads the user profile, fetches the self map and surface map by tag, and picks up the most recent handoff. Run as the first action of every new conversation.
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

**5. Restart — and stop here.** `/init-brain`'s restart gate tells the user to
start again with `brain.bat`. The memory server only reconnects in a fresh
session, so **do not continue to step 1**: this session ends at the gate.
Persona adoption, identity grounding, the heartbeat cron, and handoff pickup all
belong to the fresh session that follows.

**When reading `.self-aware`, parse it — do not pattern-match the text.** If it
fails to parse, treat it as missing (unknown, not moved) and say so; never
compare against a raw substring.

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
missing, report all three boot-list fetches (self map, surface map,
handoff) as skipped for this reason, and continue on `persona.md` and
`user.md` alone — step 4 (heartbeat cron) still runs. If the tools are
present but a specific fetch in step 3 or 5 errors anyway (the server
was up at this check but drops mid-boot), report that one fetch by
name and move on to the next rather than aborting the rest.

## 3. The two boot lists

**Why this exists.** `persona.md` gives static identity; the self map is
the session's confirmation that synaptra still agrees, and the surface
map is what closed recently and is still open. Neither is optional —
booting without checking them is booting on faith.

⛔ **Fetch both by tag, with `memory_list` — never `memory_self` or
`memory_recall`.** `memory_self` is a ranked *search*; a search can
return a different subset each time it's run, which turns "who am I"
into a lottery rather than a fixed answer. `memory_recall` matches on
prose relevance, and a list of bare uuids has no prose to match against.
Boot needs a deterministic, exact-tag fetch, not a ranked guess — that
is what `memory_list(tags=[...], state="active")` is for.

### 3a. Self map

```
memory_list(tags=["self-map"], state="active")
```

- **No active memory carries the tag** → no self map yet (a brain not
  yet migrated to this mechanism, or one whose `/init-brain` round
  hasn't run). Report it and continue — this is not fatal.
- **More than one active memory carries the tag** → name all of them by
  id, load **neither**, and say this needs fixing by hand (which one is
  real is not this skill's call to make silently).
- **Exactly one** → that memory's `content` must be full uuids, one per
  line, and nothing else. ⚠ **Empty OR whitespace-only content is a
  valid, zero-count list, not malformed** — an empty string trivially
  satisfies "uuids, one per line, nothing else" (zero of each), and
  whitespace-only (a single space) is the same zero-count state written
  a different way: the raw update path this brain's writer skills use
  cannot reliably encode a true empty-string content value (issue #4,
  cycles 3–6), so the heartbeat writes a single space instead when the
  last id closes — both read as "nothing on the list." Only content
  that fails to parse as clean uuid lines AND isn't whitespace-only (prose, a partial id,
  anything else mixed in) is malformed. Malformed → report it and treat
  it as not loaded — do not try to salvage a partial parse.
  - Otherwise, `memory_get` every id on it (an empty list has none to
    fetch — report the zero count as a finding worth noting, since a
    self map with nothing on it is unusual even though it isn't
    malformed). An id that fails to resolve is reported by id; boot
    continues with what did resolve.
  - Every id that resolves must be an `identity`-typed memory. Report
    any that resolved to a different type — a self-map entry that isn't
    `identity` is a finding, not something to load quietly.

### 3b. Surface map

```
memory_list(tags=["surface-map"], state="active")
```

Same shape as 3a — no holder, more than one holder, and the
full-uuids-one-per-line content check all apply identically, **including
that empty or whitespace-only content is a valid, zero-count list, not
malformed** (same reasoning as 3a). Once one valid holder is found: `memory_get` every id
(report an unresolved one by id, continue with the rest), and **report
the count**. A count under the cap is correct, not a problem — nothing
here requires the surface map to be full, only that it hold **at most
25** ids; a count over 25 is the thing to report, and **an empty surface
map (count 0) is the normal, expected state for a freshly-seeded brain**,
not a finding to flag the way an empty self map is. The self map's
`identity`-type check does **not** apply here — what belongs on the
surface map, and keeping it within the cap, is the heartbeat's job, not
this skill's to enforce at boot.

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
memory_list(tags=["handoff"], state="active")
```

**By tag, not `memory_recall`** — same reasoning as the two lists above:
a handoff is picked up by its marker, not by how well a query happens to
match its prose.

Unlike the two lists, more than one handoff existing is normal — one
gets stored at the end of every session. **Take the most recent by
`created_at`** and `memory_get` it. Know what to resume — don't dump it
at the user unprompted.

**No handoff found at all** → tell the user this brain has none yet, and
continue. A brain's first-ever session and a brain that has never run
`/session-end` both land here; that is expected, not an error.

**Write the protected-ids record.** After steps 3 and 5 resolve, write
`.claude/.protected-ids.json` (gitignored, machine-local, rewritten every
boot — never appended to):

```
{"self_map_holder": <step 3a's holder id or null>,
 "surface_map_holder": <step 3b's holder id or null>,
 "handoff_id": <step 5's most recent handoff id or null>,
 "written_at": "<iso8601>"}
```

Write it even when a holder or the handoff is absent — `null` is the
correct value there, not an error to work around. This is what lets
`memory_guard.py` refuse a dream (issue #5) that tries to archive, retype
or unrelate any of the three; a stale record from a prior session is why
this must be rewritten every boot, not written once and left.

## 6. Report

One line, in character: persona active, self map and surface map
counts (or why either didn't load), heartbeat live, and what's on deck
from the handoff (if anything). Any finding from step 3 (malformed
content, an unresolved id, a wrong type, more than one holder) gets
said here too, not buried in a log the user never reads.

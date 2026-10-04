---
name: migrate-from
description: Move an older second brain into this one — its memories, persona, user profile and the owner's own files. For brains from July 2026 that ran on cognitive-memory. Copy only; the old brain keeps working. Use when the owner says "migrate from", "bring my old brain over", or runs /migrate-from <old brain> [<old store>].
---

# Migrate from an old second brain

One command, one line. The owner points this brain at the old one; this brain does
the rest.

```
/migrate-from <old brain folder> [<old memory store folder>]
```

- **First path** — the old brain's folder, the one holding their `persona.md`.
  Required.
- **Second path** — where the old memories live. Optional. Leave it out and the
  script uses `COGNITIVE_MEMORY_DB`, else `~/.cognitive-memory/data`, which is
  where the old memory service keeps them unless the owner changed it.

Paths with spaces need quotes.

Run it in a session started with **`brain-claude-sandbox.bat`**, never plain `brain.bat`.
The sandbox has its own Claude config, so the old brain's memory tools, which are
registered for the whole user account, never appear in this brain.

**Copy only.** Nothing in the old brain folder, and nothing in the old memory store,
is changed. The old brain keeps running, so the owner can use both side by side
until they are satisfied. Retiring the old one is their decision, later.

## 1. Read the arguments

Take the first path as the old brain and the second, if given, as the old store.
If there is no first path, ask for the old brain's folder. Do not guess it.

## 2. Provision this brain's memory backend

Run **`/init-brain` Round -1, steps 0, 2, 6 and 9 only**: install-local, write
`.mcp.json`, write `.claude/.self-aware`. Skip the mode question (step 1); the mode is
install-local. **Do not do the restart gate (step 8) yet**, and do not run Round 0 or
the interview: the migration supplies the persona and the memories.

If `.claude/.venv/Scripts/python.exe` and `synaptra.exe` already exist, skip straight
to step 3.

## 3. Run the migration

With **this brain's own interpreter**, from the brain root, passing the paths exactly
as the owner gave them:

```
.claude/.venv/Scripts/python.exe .claude/skills/migrate-from/migrate.py "<old brain>" ["<old store>"]
```

The script prints which store it used and why (`given` or `default`); read that line
back to the owner. It takes a few minutes on a large store. Let it finish.

**What it does, and it stops at the first failure:**

1. copies the old store into `.claude/synaptra-data` (refuses if one is already there)
2. counts the copy as the old memory system wrote it
3. opens it with synaptra and counts again; every number must match
4. copies the owner's own files across; a stock file from the old release is left behind

**If it stops**, show the owner the `STOPPED:` line exactly as printed and do what it
says. Do not work around it. A failed run removes its own partial copy, so a re-run
needs no cleanup. Two expected cases:

- **The store holds no memories.** The old memory service keeps its data somewhere
  other than the default. Ask the owner for that folder and re-run with it as the
  second path.
- **The copied store will not open** because the old memory service was mid-write.
  Stop the `CognitiveMemory` scheduled task, re-run, then start it again.

## 4. Show the owner the result

Show the summary block as printed: memories before and after, links, versions, the
newest memory, and what was copied and parked. **The matching numbers are the proof;
put them first.**

If anything was **parked** (`.claude/migrated-from-old/`), say what it is in one line
each: the owner had changed a file that this brain ships its own version of. Their
version is kept there, nothing is lost, and they can compare the two when they like.

## 5. Restart

Tell the owner to close this session and start the brain again **with
`brain-claude-sandbox.bat`**. The memory tools connect on that start, and the first
start loads the memory model, which can take a few minutes. That wait is normal.

On that start, `/init-brain` finds the memories and the persona already in place,
keeps `persona.md` and `user.md` as they are, and only seeds the two boot lists.

## Afterwards

The old brain is untouched and still works. Running both is safe **as long as this
brain is started with `brain-claude-sandbox.bat`**: the sandbox keeps its own Claude
config, so it never sees the old memory tools that are registered user-wide. Started
with plain `brain.bat`, it would see both memories.

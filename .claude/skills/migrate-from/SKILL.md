---
name: migrate-from
description: Move an older second brain into this one — its memories, persona, user profile and the owner's own files. For brains from July 2026 that ran on cognitive-memory. Copy only; the old brain keeps working. Use when the owner says "migrate from", "bring my old brain over", or runs /migrate-from <path>.
---

# Migrate from an old second brain

One command. The owner points this brain at the old one; this brain does the rest.

```
/migrate-from <path to the old brain folder>
```

**Copy only.** Nothing in the old brain folder, and nothing in the old memory store,
is changed. The old brain keeps running, so the owner can use both side by side
until they are satisfied. Retiring the old one is their decision, later.

## 1. Get the path

If the owner gave no path, ask for the old brain's folder (the one holding their
`persona.md`). Do not guess it.

## 2. Provision this brain's memory backend

Run **`/init-brain` Round -1, steps 0, 2, 6 and 9 only**: install-local, write
`.mcp.json`, write `.claude/.self-aware`. Skip the mode question (step 1); the mode is
install-local. **Do not do the restart gate (step 8) yet**, and do not run Round 0 or
the interview: the migration supplies the persona and the memories.

If `.claude/.venv/Scripts/python.exe` and `synaptra.exe` already exist, skip straight
to step 3.

## 3. Run the migration

With **this brain's own interpreter**, from the brain root:

```
.claude/.venv/Scripts/python.exe .claude/skills/migrate-from/migrate.py --old-brain "<path>"
```

Add `--old-store "<path>"` only if the owner's memories are not in the default place
(`COGNITIVE_MEMORY_DB`, else `~/.cognitive-memory/data`). The script prints which one
it used; read that line back to the owner.

It takes a few minutes on a large store. Let it finish.

**What it does, and it stops at the first failure:**

1. copies the old store into `.claude/synaptra-data` (refuses if one is already there)
2. counts the copy as the old memory system wrote it
3. opens it with synaptra and counts again; every number must match
4. copies the owner's own files across; a stock file from the old release is left behind
5. blocks the old memory tools **inside this brain only** (`.claude/settings.local.json`)

**If it stops**, show the owner the `STOPPED:` line exactly as printed and do what it
says. Do not work around it. The one expected case: the copied store will not open
because the old memory service was mid-write. The script names the fix (stop the
`CognitiveMemory` scheduled task, re-run, start it again).

## 4. Show the owner the result

Show the summary block as printed: memories before and after, links, versions, the
newest memory, and what was copied and parked. **The matching numbers are the proof;
put them first.**

If anything was **parked** (`.claude/migrated-from-old/`), say what it is in one line
each: the owner had changed a file that this brain ships its own version of. Their
version is kept there, nothing is lost, and they can compare the two when they like.

## 5. Restart

Tell the owner to close this session and start the brain again **with `brain.bat`**.
The memory tools connect on that start, and the first start loads the memory model,
which can take a few minutes. That wait is normal.

On that start, `/init-brain` finds the memories and the persona already in place,
keeps `persona.md` and `user.md` as they are, and only seeds the two boot lists.

## Afterwards

- ⛔ **Do not run `/dream` on a migrated brain yet.** Its backup step still stops a
  scheduled task named `CognitiveMemory`, which on this machine is the old brain's
  memory service.
- The old brain is untouched and still works. Running both is safe: this brain no
  longer sees the old memory tools, and the old brain never saw this one's.

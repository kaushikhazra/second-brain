---
name: update
description: Update this brain to a released version — synaptra substrate and product files, with backup and version recording. Use when a newer release exists or the owner asks to update.
---

# Update

Update this brain's product files and synaptra substrate to match a
released version.  The core logic lives in `.claude/shared/update_brain.py`
— this skill wraps it for the interactive path.

## Before you start

1. **Determine the target release.**  If the owner names a version, use
   that.  Otherwise, check the latest release:

   ```
   WebFetch("https://api.github.com/repos/kaushikhazra/second-brain/releases/latest")
   ```

   Read `tag_name` (strip the leading `v`) and the first asset's
   `browser_download_url`.

2. **Compare to what's running.**  Read `.claude/.release-record.json` at
   the brain root (may not exist on a brain that has never been updated —
   fall back to `VERSION`).  If the target equals the recorded version,
   tell the owner and stop.

## Run the update

3. **Download the release zip** to a project-local `.tmp/` directory
   (never system temp).  Use `WebFetch` or `gh release download`.

4. **Extract** the zip into `.tmp/update-release/`.

5. **Run the update script from the NEW release** — not from this brain's
   current copy.  The new release's script knows how to handle its own
   files:

   ```bash
   python .tmp/update-release/.claude/shared/update_brain.py <brain-root>
   ```

   The script will:
   - Back up every file it replaces to a timestamped dir under
     `.claude/.update-backup/<YYYYMMDDTHHMMSS>/`, recording which files
     are new in the release, the prior `.release-record.json` (or its
     absence), and the prior synaptra version
   - Stop any running synaptra processes from this brain's venv
   - Copy the memory store (`.claude/synaptra-data/`) into that backup, once
     synaptra is stopped — a synaptra upgrade migrates the store in place
   - Install `synaptra==<declared version>` pinned
   - Verify `synaptra.__version__` matches
   - Copy product files (skipping owner paths: `persona.md`, `user.md`,
     `.mcp.json`, `.claude/synaptra-data/`, `.claude/dream-backups/`)
   - **Never overwrite what it cannot prove untouched.**  A file whose content
     matches no shipped version of it (checked against
     `.claude/shared/shipped_hashes.json`, which carries the hashes of every
     past release) is a conflict: it is not overwritten, and the release's
     version is written beside it as `<name>.new`
   - Write `.claude/.release-record.json`
   - **Auto-rollback**: if any step after the backup fails, the script
     automatically restores from the backup and exits non-zero naming
     the failed step

6. **Report** what changed: the old and new versions of both the brain and
   synaptra, the number of files replaced, and the backup location.  If the
   script printed `CONFLICT n file(s)`, each is a file that matches no shipped
   version of itself, so it cannot be proven untouched.  Show the owner each
   file's diff and **ask, per file: take the release's, keep theirs, or
   merge** -- never choose for them.  Then run, from the brain root:

   - take:  `python .claude/shared/update_brain.py <brain-root> --take <file>`
   - keep:  `python .claude/shared/update_brain.py <brain-root> --keep <file>`
   - merge: edit `<file>` using `<file>.new`, then `--keep <file>` to drop the
     `.new`

   A release that ships no hash table treats every differing file this way.

7. **Restart gate.**  The synaptra MCP server was stopped in step 5.
   Tell the owner to restart the brain so the server
   reconnects.  Do not continue — this session ends at the gate, same as
   `/init-brain`'s restart.

## Restore

If the owner wants to roll back:

```bash
python <brain-root>/.claude/shared/update_brain.py <brain-root> --restore
```

This uses the most recent timestamped backup under
`.claude/.update-backup/` and:

- Restores every backed-up file to its original location
- Deletes files that were **new** in the release (did not exist before)
- Restores `.release-record.json` to its prior state (or removes it if
  it did not exist before the update)
- Reinstalls the prior synaptra version (stops services first); if the
  prior version is unknown, leaves synaptra as-is and says so
- Puts the backed-up memory store back. The store it replaces (with any
  memories written since the update) is not deleted: it is moved to
  `.claude/synaptra-data.replaced-<time>/` and the script prints where

To restore from a specific backup, pass `--backup-dir <path>`.

Multiple updates preserve all prior backups (timestamped directories),
so rolling back past the most recent update is possible by naming the
backup directory explicitly.

## Manual path (R7)

When this brain's own skills are broken or out of date, the update can be
run without Claude:

```
1. Download the release zip from GitHub
2. Extract it (e.g. to C:\tmp\sb-release)
3. Run:  python C:\tmp\sb-release\.claude\shared\update_brain.py C:\path\to\brain
4. Restart the brain
```

This is documented **above** any automatic path in the release notes.

## What is never touched

- `persona.md` — the owner's identity definition
- `user.md` — the owner's profile
- `.claude/synaptra-data/` — the memory store (copied into the backup, never overwritten by the release)
- `.mcp.json` — machine-local server config
- `.claude/dream-backups/` — dream checkpoint backups
- `.claude/.self-aware` — provisioning record (owned by `/init-brain`)
- `.claude/activations.json` — opt-in habit answers
- `.claude/.protected-ids.json` — boot-list protection record

#!/usr/bin/env python3
"""Update a second-brain to a new release.

Manual command (documented above any automatic path in release notes):

    python <new-release>/.claude/shared/update_brain.py <brain-root>

Where <new-release> is the extracted release zip and <brain-root> is the
brain to update.  The script resolves the release root relative to itself
(three levels up from .claude/shared/) when --release is omitted.

Restore the prior state with:

    python <brain-root>/.claude/shared/update_brain.py <brain-root> --restore

Stdlib only.  No synaptra import, no network, no host dependency beyond a
Python 3.8+ interpreter.
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import platform_paths  # noqa: E402  (beside this file; the one platform rule)

# -- owner / machine-local paths: never overwritten ----------------------

OWNER_PATHS = frozenset(
    {
        "persona.md",
        "user.md",
        ".mcp.json",
    }
)

OWNER_DIRS = frozenset(
    {
        ".claude/synaptra-data",
        ".claude/dream-backups",
        ".claude/.venv",
        ".claude/.python",
        ".claude/skills/transcribe/models",
    }
)

BASELINE = ".claude/conformance-baseline.json"

MACHINE_LOCAL = frozenset(
    {
        ".claude/.self-aware",
        ".claude/.protected-ids.json",
        ".claude/.list-holder-check.json",
        ".claude/activations.json",
        BASELINE,
        ".claude/dream-cycle-plan.json",
        ".claude/dream-cycle-log.md",
        ".claude/skills/local-agent/config.json",
    }
)

# Internal manifest filenames stored inside each backup dir
_MANIFEST_NEW = "_manifest_new_files.json"
_RESTORE_META = "_restore_meta.json"
# The memory store's copy: a folder of the backup that restore treats apart from the files.
_STORE_COPY = "_store"
STORE_DIR = ".claude/synaptra-data"


def release_root_from_script() -> Path:
    """The release root: three levels up from .claude/shared/update_brain.py."""
    return Path(__file__).resolve().parent.parent.parent


_REEXEC_ENV = "_UPDATE_BRAIN_REEXEC"


def _is_under(path: str | Path, parent: Path) -> bool:
    p = os.path.normcase(os.path.abspath(str(path)))
    d = os.path.normcase(os.path.abspath(str(parent)))
    return p == d or p.startswith(d + os.sep)


def running_from_venv(brain: Path) -> bool:
    """True if this process is the brain's own venv Python."""
    venv = brain / ".claude" / ".venv"
    return _is_under(sys.executable, venv) or _is_under(sys.prefix, venv)


def find_standalone_python(brain: Path) -> Path | None:
    """The standalone interpreter /init-brain installed under .claude/.python."""
    found = sorted(
        (brain / ".claude" / ".python").glob(platform_paths.standalone_python_glob())
    )
    return found[0] if found else None


def hand_over_to_standalone(brain: Path) -> int | None:
    """Rerun this command under the standalone interpreter if started from the venv.

    The venv's Python is what the update replaces and what stop_synaptra
    stops, so the update should not run on it.  Returns the child's exit code,
    or None to carry on in this process.
    """
    if os.environ.get(_REEXEC_ENV) or not running_from_venv(brain):
        return None
    py = find_standalone_python(brain)
    if py is None:
        print(
            "NOTE  started from the brain's venv Python and no standalone"
            " interpreter found under .claude/.python -- continuing here"
        )
        return None
    print(
        f"MOVE  started from the brain's venv Python -- continuing under {py}",
        flush=True,
    )
    cmd = [str(py), str(Path(__file__).resolve()), *sys.argv[1:]]
    env = {**os.environ, _REEXEC_ENV: "1"}
    return subprocess.run(cmd, env=env).returncode


def read_version_file(root: Path, name: str) -> str:
    p = root / name
    if not p.exists():
        raise SystemExit(f"FAIL: {p} not found")
    v = p.read_text(encoding="utf-8").strip()
    if not v:
        raise SystemExit(f"FAIL: {name} is empty in {root}")
    return v


def is_owner_path(relpath: str) -> bool:
    """True if this relative path must not be overwritten by an update."""
    normed = relpath.replace("\\", "/")
    if normed in OWNER_PATHS or normed in MACHINE_LOCAL:
        return True
    for d in OWNER_DIRS:
        if normed.startswith(d + "/") or normed == d:
            return True
    return False


# -- owner edits ---------------------------------------------------------
#
# Every release ships SHIPPED_HASHES: the sha256 of each product file in every
# release up to and including itself.  A live file whose hash is in its path's
# list is a shipped copy the owner never touched, so replacing it loses nothing.
# Any other live file is the owner's; it is kept and the release's version is
# written beside it as <name>.new.

SHIPPED_HASHES = ".claude/shared/shipped_hashes.json"
NEW_SUFFIX = ".new"


def normalized_sha256(data: bytes) -> str:
    """sha256 of *data*, with CRLF read as LF for text.

    git checks text out with the platform's line endings, so a Windows copy of an
    untouched file differs from the archive byte for byte.  Binary data (any NUL
    in the first 8000 bytes) is hashed as it is.
    """
    if b"\0" not in data[:8000]:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def load_shipped_hashes(release: Path) -> dict[str, list[str]] | None:
    p = release / SHIPPED_HASHES
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))["files"]


def plan_update(
    brain: Path, release: Path, release_files: list[str]
) -> tuple[list[str], list[str]]:
    """Split the release's product files into (replace, keep).

    *keep* are files the brain already has whose content is neither the new
    release's nor any shipped version: conflicts, left for the owner to settle.
    Everything else is replaced.  A release without a hash table cannot prove
    any file untouched, so every file that differs from the release is a
    conflict -- nothing is overwritten on a guess.
    """
    table = load_shipped_hashes(release)
    if table is None:
        print("  NOTE  release has no shipped-hash table -- no file can be proven")
        print("        untouched, so any file that differs is kept as a conflict")
        table = {}
    replace: list[str] = []
    keep: list[str] = []
    for rel in release_files:
        live = brain / rel
        if rel == SHIPPED_HASHES or is_owner_path(rel) or not live.is_file():
            replace.append(rel)
            continue
        live_hash = normalized_sha256(live.read_bytes())
        if live_hash in table.get(rel, ()) or live_hash == normalized_sha256(
            (release / rel).read_bytes()
        ):
            replace.append(rel)
        else:
            keep.append(rel)
    return replace, keep


def diff_summary(live: Path, new: Path) -> str:
    """'+A -R lines' going from the owner's file to the release's."""
    try:
        a = live.read_text(encoding="utf-8").splitlines()
        b = new.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return "binary or unreadable"
    added = removed = 0
    for line in difflib.ndiff(a, b):
        if line.startswith("+ "):
            added += 1
        elif line.startswith("- "):
            removed += 1
    return f"+{added} -{removed} lines"


def write_new_files(brain: Path, release: Path, keep: list[str]) -> None:
    for rel in keep:
        shutil.copy2(str(release / rel), str(brain / (rel + NEW_SUFFIX)))


DIFF_LINES = 40


def diff_excerpt(live: Path, new: Path) -> list[str]:
    """The first DIFF_LINES lines of a unified diff, owner's file -> release's."""
    try:
        a = live.read_text(encoding="utf-8").splitlines()
        b = new.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return ["(binary or unreadable -- no diff)"]
    lines = list(difflib.unified_diff(a, b, "yours", "release", lineterm="", n=1))
    if len(lines) > DIFF_LINES:
        lines = lines[:DIFF_LINES] + [f"... {len(lines) - DIFF_LINES} more diff lines"]
    return lines


def report_kept(brain: Path, keep: list[str]) -> None:
    if not keep:
        return
    print(
        f"CONFLICT {len(keep)} file(s) differ from every shipped version -- not overwritten"
    )
    for rel in keep:
        new = brain / (rel + NEW_SUFFIX)
        print(f"  {rel}  ({diff_summary(brain / rel, new)} to reach the release)")
        print(f"    release version: {rel + NEW_SUFFIX}")
        enc = sys.stdout.encoding or "utf-8"
        for line in diff_excerpt(brain / rel, new):
            # the owner's text can hold characters a legacy console cannot show
            print("    | " + line.encode(enc, "replace").decode(enc))
    print("  Ask the owner, per file: take the release's, keep theirs, or merge.")
    print("    take:  update_brain.py <brain> --take <file>")
    print("    keep:  update_brain.py <brain> --keep <file>")
    print("    merge: edit <file> by hand using <file>.new, then --keep <file>")


def resolve_conflict(brain: Path, rel: str, action: str) -> None:
    """Settle one kept file: 'take' installs the release's, 'keep' drops the .new."""
    live = brain / rel
    new = brain / (rel + NEW_SUFFIX)
    if not new.is_file():
        raise SystemExit(f"FAIL: {rel + NEW_SUFFIX} not found -- nothing to resolve")
    if action == "take":
        shutil.move(str(new), str(live))
        print(f"TAKE  {rel} now matches the release (yours is in .update-backup)")
    else:
        new.unlink()
        print(f"KEEP  {rel} left as yours; {rel + NEW_SUFFIX} removed")


def list_release_files(release: Path) -> list[str]:
    """All files in the release tree, as forward-slash relative paths."""
    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(str(release)):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in {".venv", ".python", "synaptra-data", "__pycache__"}
        ]
        for f in filenames:
            p = Path(dirpath) / f
            rel = p.relative_to(release).as_posix()
            files.append(rel)
    return sorted(files)


# -- backup / restore ---------------------------------------------------


def _make_timestamped_backup_dir(brain: Path) -> Path:
    """Create a new timestamped backup dir under .claude/.update-backup/."""
    root = brain / ".claude" / ".update-backup"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    d = root / stamp
    # If same-second collision, append a counter
    if d.exists():
        for i in range(1, 100):
            d = root / f"{stamp}-{i}"
            if not d.exists():
                break
    d.mkdir(parents=True)
    return d


def _latest_backup_dir(brain: Path) -> Path:
    """Return the most recent timestamped backup dir, or raise."""
    root = brain / ".claude" / ".update-backup"
    if not root.exists():
        raise SystemExit(f"FAIL: no backup directory at {root}")
    dirs = sorted(
        [d for d in root.iterdir() if d.is_dir()],
        key=lambda p: p.name,
        reverse=True,
    )
    if not dirs:
        raise SystemExit(f"FAIL: no backups found in {root}")
    return dirs[0]


def _read_synaptra_version(brain: Path) -> str | None:
    """Read the currently installed synaptra.__version__ from the venv.

    Returns None if the venv or synaptra is not installed.
    """
    claude_dir = brain / ".claude"
    venv_python = platform_paths.venv_python(claude_dir / ".venv")
    if not venv_python.exists():
        return None
    try:
        result = subprocess.run(
            [str(venv_python), "-c", "import synaptra; print(synaptra.__version__)"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except Exception:
        pass
    return None


def backup_current(
    brain: Path,
    backup_dir: Path,
    release_files: list[str],
    kept: list[str] = (),
) -> int:
    """Copy every file the update will replace into the backup directory.

    *kept* are the owner-edited files the update leaves alone; the ``.new`` files
    written beside them are recorded like any other file the update adds, or
    backed up if one was already there.

    Also records:
    - _manifest_new_files.json: release paths that did NOT exist in the brain
      before the update (so restore can delete them).
    - _restore_meta.json: prior .release-record.json content (or null) and
      prior synaptra version (or null).

    The memory store is copied separately, by backup_store, once synaptra is stopped.
    """
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir(parents=True)

    backed = 0
    new_files: list[str] = []
    for rel in release_files:
        if is_owner_path(rel):
            continue
        src = brain / rel
        if src.exists():
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
            backed += 1
        else:
            new_files.append(rel)

    for rel in kept:
        beside = rel + NEW_SUFFIX
        if (brain / beside).exists():
            dst = backup_dir / beside
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(brain / beside), str(dst))
            backed += 1
        else:
            new_files.append(beside)

    # Write manifest of new files
    manifest_path = backup_dir / _MANIFEST_NEW
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(new_files, f, indent=2)

    # Capture restore metadata
    record_path = brain / ".claude" / ".release-record.json"
    prior_record = None
    if record_path.is_file():
        try:
            prior_record = json.loads(record_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    prior_synaptra = _read_synaptra_version(brain)

    meta = {
        "prior_release_record": prior_record,
        "prior_synaptra_version": prior_synaptra,
    }
    meta_path = backup_dir / _RESTORE_META
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return backed


def _update_meta(backup_dir: Path, **fields) -> None:
    meta_path = backup_dir / _RESTORE_META
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update(fields)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def backup_store(brain: Path, backup_dir: Path) -> None:
    """Copy the memory store into the backup.  Synaptra must already be stopped.

    A synaptra upgrade reopens the store and migrates it in place, so restoring
    the old synaptra alone leaves old software on a store it did not write.
    Noted in the backup's metadata only once the copy is complete, so a failed
    copy is never mistaken for a backup.
    """
    store = brain / STORE_DIR
    if not store.is_dir():
        print("  (no memory store to back up)")
        return
    dst = backup_dir / _STORE_COPY
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(store, dst)
    _update_meta(backup_dir, store_backed_up=True)
    print(f"  backed up the memory store to {dst}")


def restore_store(brain: Path, backup_dir: Path) -> None:
    """Put the backed-up memory store back.  Synaptra must already be stopped.

    The store it replaces is moved aside, not deleted: memories written since the
    update live only there.
    """
    saved = backup_dir / _STORE_COPY
    store = brain / STORE_DIR
    if store.exists():
        stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        aside = store.with_name(f"{store.name}.replaced-{stamp}")
        n = 0
        while aside.exists():
            n += 1
            aside = store.with_name(f"{store.name}.replaced-{stamp}-{n}")
        shutil.move(str(store), str(aside))
        print(f"  the store it replaces is kept at {aside}")
    shutil.copytree(saved, store)
    print("  restored the memory store")


def restore_backup(
    brain: Path,
    backup_dir: Path,
    *,
    skip_synaptra: bool = False,
) -> int:
    """Restore every file from the pre-update backup.

    Also:
    - Deletes files that were NEW in the release (from _manifest_new_files.json).
    - Restores .release-record.json to its prior state (or removes it).
    - Reinstalls the prior synaptra version if known (stops services first).
    """
    if not backup_dir.exists():
        raise SystemExit(f"FAIL: no backup at {backup_dir}")

    # 1. Restore backed-up files
    restored = 0
    for dirpath, dirnames, filenames in os.walk(str(backup_dir)):
        if Path(dirpath) == backup_dir:
            dirnames[:] = [d for d in dirnames if d != _STORE_COPY]
        for f in filenames:
            # Skip internal manifests
            if f in (_MANIFEST_NEW, _RESTORE_META):
                continue
            src = Path(dirpath) / f
            rel = src.relative_to(backup_dir)
            dst = brain / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
            restored += 1

    # 2. Delete files that were NEW in the release
    manifest_path = backup_dir / _MANIFEST_NEW
    if manifest_path.is_file():
        try:
            new_files = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            new_files = []
        deleted = 0
        for rel in new_files:
            p = brain / rel
            if p.is_file():
                p.unlink()
                deleted += 1
                # Clean up empty parent dirs (up to brain root)
                parent = p.parent
                while parent != brain:
                    try:
                        if not any(parent.iterdir()):
                            parent.rmdir()
                        else:
                            break
                    except OSError:
                        break
                    parent = parent.parent
        if deleted:
            print(f"  deleted {deleted} files that were new in the release")

    # 3. Restore .release-record.json and synaptra version
    meta_path = backup_dir / _RESTORE_META
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}

        # Release record
        record_path = brain / ".claude" / ".release-record.json"
        prior_record = meta.get("prior_release_record")
        if prior_record is not None:
            with open(record_path, "w", encoding="utf-8") as f:
                json.dump(prior_record, f, indent=2)
            print("  restored .release-record.json to prior state")
        elif record_path.is_file():
            record_path.unlink()
            print("  removed .release-record.json (did not exist before update)")

        # Command guard setting the update added
        added = meta.get("guard_entry_added")
        if added is not None:
            remove_guard_entry(brain, added["file_existed"])

        # Conformance baseline the update added
        if meta.get("baseline_added") is True:
            (brain / BASELINE).unlink(missing_ok=True)
            print("  removed the conformance baseline the update added")

        # Synaptra version, then the store it migrated
        if not skip_synaptra:
            prior_synaptra = meta.get("prior_synaptra_version")
            store_saved = meta.get("store_backed_up") is True
            if store_saved and not prior_synaptra:
                print("STOP synaptra")
                stop_synaptra(brain)
            if prior_synaptra:
                print(f"  restoring synaptra to prior version {prior_synaptra}")
                print("STOP synaptra")
                stop_synaptra(brain)
                try:
                    install_synaptra(brain, prior_synaptra)
                    verify_synaptra_version(brain, prior_synaptra)
                    print(f"  synaptra restored to {prior_synaptra}")
                except SystemExit as exc:
                    print(
                        f"  WARNING: could not restore synaptra"
                        f" to {prior_synaptra}: {exc}"
                    )
                    print("  synaptra left at current version")
            else:
                print("  prior synaptra version unknown -- leaving synaptra as-is")
            if store_saved:
                restore_store(brain, backup_dir)

    return restored


# -- synaptra lifecycle -------------------------------------------------


def stop_synaptra(brain: Path) -> bool:
    """Stop synaptra processes running from this brain's venv.

    Returns True if any were stopped.
    """
    venv = brain / ".claude" / ".venv"
    if not venv.exists():
        print("  (no .venv -- nothing to stop)")
        return False

    if not platform_paths.is_windows():
        stopped = platform_paths.stop_venv_processes(venv.resolve())
        if stopped:
            print(f"  stopped {stopped} synaptra process(es)")
            time.sleep(1)
        else:
            print("  (no running synaptra processes)")
        return stopped > 0

    venv_str = str(venv).replace("'", "''")  # escape for PS single-quote
    # This script is a child of the updater, so walking up from $PID reaches the
    # updater and whatever launched it.  None of those may be stopped.
    ps_script = "\n".join(
        [
            "$venv = '" + venv_str + "'",
            "$skip = @{}",
            "$cur = $PID",
            "while ($cur -and -not $skip.ContainsKey([int]$cur)) {",
            "    $skip[[int]$cur] = $true",
            '    $row = Get-CimInstance Win32_Process -Filter "ProcessId=$cur"',
            "    $cur = if ($row) { $row.ParentProcessId } else { 0 }",
            "}",
            "$mine = {",
            "    Get-CimInstance Win32_Process | Where-Object {",
            "        $_.ExecutablePath -and",
            "        $_.ExecutablePath.StartsWith($venv, [StringComparison]::OrdinalIgnoreCase) -and",
            "        -not $skip.ContainsKey([int]$_.ProcessId)",
            "    }",
            "}",
            "$count = 0",
            "foreach ($p in @(& $mine)) {",
            "    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue",
            "    $count++",
            "}",
            "if ($count -gt 0) {",
            "    for ($i = 0; $i -lt 20; $i++) {",
            "        if (-not @(& $mine)) { break }",
            "        Start-Sleep -Milliseconds 500",
            "    }",
            "}",
            "Write-Output $count",
        ]
    )

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        stopped = int(result.stdout.strip() or "0")
    except Exception as exc:
        print(f"  (stop check failed: {exc})")
        return False

    if stopped > 0:
        print(f"  stopped {stopped} synaptra process(es)")
        time.sleep(1)
    else:
        print("  (no running synaptra processes)")
    return stopped > 0


def install_synaptra(brain: Path, version: str) -> None:
    """Install synaptra pinned to the declared version via uv."""
    claude_dir = brain / ".claude"
    uv = platform_paths.uv_path(claude_dir)
    venv_python = platform_paths.venv_python(claude_dir / ".venv")

    if not uv.exists():
        raise SystemExit(f"FAIL: uv not found at {uv} -- run /init-brain first")
    if not venv_python.exists():
        raise SystemExit(
            f"FAIL: venv python not found at {venv_python} -- run /init-brain first"
        )

    env = {**os.environ, "UV_PYTHON_INSTALL_DIR": str(claude_dir / ".python")}
    result = subprocess.run(
        [
            str(uv),
            "pip",
            "install",
            "--python",
            str(venv_python),
            f"synaptra=={version}",
        ],
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )
    if result.returncode != 0:
        print(f"  stderr: {result.stderr}", file=sys.stderr)
        raise SystemExit(
            f"FAIL: synaptra=={version} install failed (exit {result.returncode})"
        )


def verify_synaptra_version(brain: Path, expected: str) -> None:
    """Assert the installed synaptra.__version__ equals *expected*."""
    claude_dir = brain / ".claude"
    venv_python = platform_paths.venv_python(claude_dir / ".venv")

    result = subprocess.run(
        [str(venv_python), "-c", "import synaptra; print(synaptra.__version__)"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise SystemExit(f"FAIL: could not import synaptra: {result.stderr}")

    actual = result.stdout.strip()
    if actual != expected:
        raise SystemExit(f"FAIL: version mismatch -- expected {expected}, got {actual}")


# -- file copy ----------------------------------------------------------


def copy_release_files(
    release: Path,
    brain: Path,
    release_files: list[str],
) -> int:
    """Copy product files from *release* into *brain*, skipping owner paths."""
    copied = 0
    for rel in release_files:
        if is_owner_path(rel):
            continue
        src = release / rel
        dst = brain / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        copied += 1
    return copied


# -- release record ----------------------------------------------------


def write_release_record(
    brain: Path,
    brain_version: str,
    synaptra_version: str,
) -> Path:
    """Write .claude/.release-record.json with a round-trip verify."""
    record = {
        "schema": 1,
        "brain_version": brain_version,
        "synaptra_version": synaptra_version,
        "updated_at": datetime.datetime.now().astimezone().isoformat(),
        "updated_by": "update_brain.py",
    }
    p = brain / ".claude" / ".release-record.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    # round-trip
    with open(p, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["brain_version"] == brain_version, "round-trip failed"
    assert loaded["synaptra_version"] == synaptra_version, "round-trip failed"
    return p


# -- command guard setting ---------------------------------------------


def had_command_guard(brain: Path) -> bool:
    """True if this brain already ran the command guard, before the update."""
    return (brain / ".claude" / "hooks" / "command_guard.py").is_file()


def _write_activations(path: Path, record: dict) -> None:
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def keep_guard_setting(
    brain: Path, had_guard: bool, version: str, backup_dir: Path
) -> None:
    """Record the guard as on for a brain that had it and never chose a setting.

    Before /guard existed the guard was always on. Without an entry the hook reads
    "off", so an updated brain would lose it; writing the entry keeps what it had.
    An entry already there, on or off, is the owner's and is left alone. What is
    added is noted in the backup so --restore can take it out again.
    """
    path = brain / ".claude" / "activations.json"
    existed = path.is_file()
    try:
        record = json.loads(path.read_text(encoding="utf-8")) if existed else {}
    except (OSError, ValueError):
        return  # unreadable: not ours to overwrite
    if not had_guard or not isinstance(record, dict) or "guard" in record:
        return
    meta_path = backup_dir / _RESTORE_META
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["guard_entry_added"] = {"file_existed": existed}
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    record["guard"] = {"answered_at_version": version, "active": True}
    _write_activations(path, record)
    print("  command guard stays on (this brain already had it)")


def keep_conformance_baseline(brain: Path, backup_dir: Path) -> None:
    """Date the session-end conformance scan from this update, if the brain has no date.

    Memories older than the baseline are history, not violations (issue #79). An
    existing baseline is the owner's and is left alone. What is added is noted in the
    backup so --restore can take it out again.
    """
    path = brain / BASELINE
    if path.exists():
        return
    since = datetime.datetime.now().astimezone().isoformat()
    path.write_text(json.dumps({"since": since}, indent=2) + "\n", encoding="utf-8")
    meta_path = backup_dir / _RESTORE_META
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["baseline_added"] = True
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"  conformance baseline set to {since}")


def remove_guard_entry(brain: Path, file_existed: bool) -> None:
    """Undo keep_guard_setting: take the entry out, and the file if it was ours."""
    path = brain / ".claude" / "activations.json"
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if not isinstance(record, dict) or "guard" not in record:
        return
    del record["guard"]
    if record or file_existed:
        _write_activations(path, record)
    else:
        path.unlink()
    print("  removed the command guard setting the update added")


# -- main --------------------------------------------------------------


class _UpdateStepFailed(Exception):
    """A post-backup step failed; carries the step name for the error message."""

    def __init__(self, step: str, cause: Exception | None = None):
        self.step = step
        self.cause = cause
        super().__init__(f"step '{step}' failed: {cause}")


def run_update(
    brain: Path,
    release: Path,
    *,
    skip_synaptra: bool = False,
) -> None:
    """Execute the full update sequence.  Raises SystemExit on failure.

    If any step after the backup fails, the backup is restored automatically
    and the script exits non-zero naming the failed step.
    """
    brain_version = read_version_file(release, "VERSION")
    synaptra_version = read_version_file(release, "SYNAPTRA_VERSION")

    print(f"UPDATE  brain at {brain}")
    print(f"  release: second-brain {brain_version}, synaptra {synaptra_version}")

    had_guard = had_command_guard(brain)  # asked before the copy adds the hook
    release_files = list_release_files(release)
    print(f"  release contains {len(release_files)} files")
    release_files, kept_files = plan_update(brain, release, release_files)

    # 1. Backup (timestamped)
    backup_dir = _make_timestamped_backup_dir(brain)
    print("BACKUP")
    n = backup_current(brain, backup_dir, release_files, kept_files)
    print(f"  backed up {n} files to {backup_dir}")

    # -- Fault injection for testing (never in production) --
    fault_step = os.getenv("_UPDATE_BRAIN_FAULT_STEP", "")

    # Steps 2-5 are wrapped: any failure triggers auto-rollback.
    try:
        # 2. Stop synaptra  (R8: before replacing)
        print("STOP synaptra")
        if fault_step == "stop":
            raise _UpdateStepFailed("stop", RuntimeError("injected fault"))
        stop_synaptra(brain)

        # 2b. Copy the memory store, now that nothing holds it open
        if not skip_synaptra:
            backup_store(brain, backup_dir)

        # 3. Install pinned synaptra  (R2)
        if not skip_synaptra:
            print("INSTALL synaptra")
            if fault_step == "install":
                raise _UpdateStepFailed("install", RuntimeError("injected fault"))
            install_synaptra(brain, synaptra_version)
            print(f"  synaptra=={synaptra_version} installed")
            verify_synaptra_version(brain, synaptra_version)
            print(f"  verified synaptra.__version__ == {synaptra_version}")

        # 4. Copy product files  (R3)
        print("COPY product files")
        if fault_step == "copy":
            raise _UpdateStepFailed("copy", RuntimeError("injected fault"))
        copied = copy_release_files(release, brain, release_files)
        print(f"  copied {copied} product files")
        write_new_files(brain, release, kept_files)

        # 5. Record  (R5)
        print("RECORD")
        if fault_step == "record":
            raise _UpdateStepFailed("record", RuntimeError("injected fault"))
        write_release_record(brain, brain_version, synaptra_version)
        keep_guard_setting(brain, had_guard, brain_version, backup_dir)
        keep_conformance_baseline(brain, backup_dir)

    except _UpdateStepFailed as exc:
        print(f"\nFAILED at step '{exc.step}': {exc.cause}")
        print("AUTO-ROLLBACK from backup")
        restored = restore_backup(brain, backup_dir, skip_synaptra=skip_synaptra)
        print(f"  restored {restored} files")
        raise SystemExit(
            f"FAIL: update aborted at step '{exc.step}' -- rolled back to prior state"
        )
    except SystemExit:
        # SystemExit from install/verify/etc -- also rollback
        print("\nAUTO-ROLLBACK from backup")
        restored = restore_backup(brain, backup_dir, skip_synaptra=skip_synaptra)
        print(f"  restored {restored} files")
        raise
    except Exception as exc:
        print(f"\nUNEXPECTED ERROR: {exc}")
        print("AUTO-ROLLBACK from backup")
        restored = restore_backup(brain, backup_dir, skip_synaptra=skip_synaptra)
        print(f"  restored {restored} files")
        raise SystemExit(f"FAIL: update aborted -- {exc} -- rolled back to prior state")

    print(
        f"DONE  brain updated to second-brain {brain_version}"
        f" + synaptra {synaptra_version}"
    )
    print("  Restart Claude to reconnect the memory server.")
    report_kept(brain, kept_files)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update a second-brain to a new release.",
        epilog=(
            "Manual path: extract the release zip, then run this script "
            "from the extracted tree against the brain root."
        ),
    )
    parser.add_argument("brain", type=Path, help="Path to the brain to update")
    parser.add_argument(
        "--release",
        type=Path,
        default=None,
        help="Path to extracted release (default: resolved from script location)",
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore the pre-update backup instead of updating",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Specific backup dir to restore from (default: most recent)",
    )
    parser.add_argument(
        "--skip-synaptra",
        action="store_true",
        help="Skip synaptra install/verify (for file-only testing)",
    )
    parser.add_argument(
        "--take",
        action="append",
        default=[],
        metavar="FILE",
        help="Settle a conflict: install the release's version of FILE",
    )
    parser.add_argument(
        "--keep",
        action="append",
        default=[],
        metavar="FILE",
        help="Settle a conflict: keep your FILE and drop FILE.new",
    )
    args = parser.parse_args()

    brain = args.brain.resolve()
    if not (brain / "CLAUDE.md").exists():
        raise SystemExit(
            f"FAIL: {brain} does not look like a brain root (no CLAUDE.md)"
        )

    if args.take or args.keep:
        for rel in args.take:
            resolve_conflict(brain, rel, "take")
        for rel in args.keep:
            resolve_conflict(brain, rel, "keep")
        return 0

    handed_over = hand_over_to_standalone(brain)
    if handed_over is not None:
        return handed_over

    if args.restore:
        if args.backup_dir:
            backup_dir = args.backup_dir.resolve()
        else:
            backup_dir = _latest_backup_dir(brain)
        print(f"RESTORE from backup {backup_dir.name}")
        n = restore_backup(brain, backup_dir, skip_synaptra=args.skip_synaptra)
        print(f"  restored {n} files")
        print("DONE -- restored to pre-update state")
        return 0

    release = (args.release or release_root_from_script()).resolve()
    if not (release / "VERSION").exists():
        raise SystemExit(
            f"FAIL: {release} does not look like a release root (no VERSION)"
        )

    run_update(brain, release, skip_synaptra=args.skip_synaptra)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

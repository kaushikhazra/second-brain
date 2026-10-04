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
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

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
    }
)

MACHINE_LOCAL = frozenset(
    {
        ".claude/.self-aware",
        ".claude/.protected-ids.json",
        ".claude/.list-holder-check.json",
        ".claude/activations.json",
        ".claude/skills/local-agent/config.json",
    }
)

# Internal manifest filenames stored inside each backup dir
_MANIFEST_NEW = "_manifest_new_files.json"
_RESTORE_META = "_restore_meta.json"


def release_root_from_script() -> Path:
    """The release root: three levels up from .claude/shared/update_brain.py."""
    return Path(__file__).resolve().parent.parent.parent


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
    scripts = "Scripts" if sys.platform == "win32" else "bin"
    ext = ".exe" if sys.platform == "win32" else ""
    venv_python = claude_dir / ".venv" / scripts / f"python{ext}"
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
) -> int:
    """Copy every file the update will replace into the backup directory.

    Also records:
    - _manifest_new_files.json: release paths that did NOT exist in the brain
      before the update (so restore can delete them).
    - _restore_meta.json: prior .release-record.json content (or null) and
      prior synaptra version (or null).
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
    for dirpath, _, filenames in os.walk(str(backup_dir)):
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

        # Synaptra version
        if not skip_synaptra:
            prior_synaptra = meta.get("prior_synaptra_version")
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

    return restored


# -- synaptra lifecycle -------------------------------------------------


def stop_synaptra(brain: Path) -> bool:
    """Stop synaptra processes running from this brain's venv.

    Returns True if any were stopped.  Windows-only (matches the product).
    """
    venv = brain / ".claude" / ".venv"
    if not venv.exists():
        print("  (no .venv -- nothing to stop)")
        return False

    venv_str = str(venv).replace("'", "''")  # escape for PS single-quote
    ps_script = "\n".join(
        [
            "$venv = '" + venv_str + "'",
            "$procs = Get-CimInstance Win32_Process | Where-Object {",
            "    $_.ExecutablePath -and",
            "    $_.ExecutablePath.StartsWith($venv, [StringComparison]::OrdinalIgnoreCase)",
            "}",
            "$count = 0",
            "foreach ($p in $procs) {",
            "    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue",
            "    $count++",
            "}",
            "if ($count -gt 0) {",
            "    for ($i = 0; $i -lt 20; $i++) {",
            "        $left = @(Get-CimInstance Win32_Process | Where-Object {",
            "            $_.ExecutablePath -and",
            "            $_.ExecutablePath.StartsWith($venv, [StringComparison]::OrdinalIgnoreCase)",
            "        })",
            "        if (-not $left) { break }",
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
    uv = claude_dir / ("uv.exe" if sys.platform == "win32" else "uv")
    scripts = "Scripts" if sys.platform == "win32" else "bin"
    ext = ".exe" if sys.platform == "win32" else ""
    venv_python = claude_dir / ".venv" / scripts / f"python{ext}"

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
    scripts = "Scripts" if sys.platform == "win32" else "bin"
    ext = ".exe" if sys.platform == "win32" else ""
    venv_python = claude_dir / ".venv" / scripts / f"python{ext}"

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

    release_files = list_release_files(release)
    print(f"  release contains {len(release_files)} files")

    # 1. Backup (timestamped)
    backup_dir = _make_timestamped_backup_dir(brain)
    print("BACKUP")
    n = backup_current(brain, backup_dir, release_files)
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

        # 5. Record  (R5)
        print("RECORD")
        if fault_step == "record":
            raise _UpdateStepFailed("record", RuntimeError("injected fault"))
        write_release_record(brain, brain_version, synaptra_version)

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
    args = parser.parse_args()

    brain = args.brain.resolve()
    if not (brain / "CLAUDE.md").exists():
        raise SystemExit(
            f"FAIL: {brain} does not look like a brain root (no CLAUDE.md)"
        )

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

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

OWNER_PATHS = frozenset({
    "persona.md",
    "user.md",
    ".mcp.json",
})

OWNER_DIRS = frozenset({
    ".claude/synaptra-data",
    ".claude/dream-backups",
    ".claude/.venv",
    ".claude/.python",
})

MACHINE_LOCAL = frozenset({
    ".claude/.self-aware",
    ".claude/.protected-ids.json",
    ".claude/.list-holder-check.json",
    ".claude/activations.json",
    ".claude/skills/local-agent/config.json",
})


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
            d for d in dirnames
            if d not in {".venv", ".python", "synaptra-data", "__pycache__"}
        ]
        for f in filenames:
            p = Path(dirpath) / f
            rel = p.relative_to(release).as_posix()
            files.append(rel)
    return sorted(files)


# -- backup / restore ---------------------------------------------------

def backup_current(brain: Path, backup_dir: Path, release_files: list[str]) -> int:
    """Copy every file the update will replace into the backup directory."""
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir(parents=True)

    backed = 0
    for rel in release_files:
        if is_owner_path(rel):
            continue
        src = brain / rel
        if src.exists():
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
            backed += 1
    return backed


def restore_backup(brain: Path, backup_dir: Path) -> int:
    """Restore every file from the pre-update backup."""
    if not backup_dir.exists():
        raise SystemExit(f"FAIL: no backup at {backup_dir}")

    restored = 0
    for dirpath, _, filenames in os.walk(str(backup_dir)):
        for f in filenames:
            src = Path(dirpath) / f
            rel = src.relative_to(backup_dir)
            dst = brain / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
            restored += 1
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
    ps_script = "\n".join([
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
    ])

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=30,
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
        [str(uv), "pip", "install", "--python", str(venv_python),
         f"synaptra=={version}"],
        capture_output=True, text=True, timeout=300, env=env,
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
        [str(venv_python), "-c",
         "import synaptra; print(synaptra.__version__)"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise SystemExit(f"FAIL: could not import synaptra: {result.stderr}")

    actual = result.stdout.strip()
    if actual != expected:
        raise SystemExit(
            f"FAIL: version mismatch -- expected {expected}, got {actual}"
        )


# -- file copy ----------------------------------------------------------

def copy_release_files(
    release: Path, brain: Path, release_files: list[str],
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
    brain: Path, brain_version: str, synaptra_version: str,
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

def run_update(
    brain: Path,
    release: Path,
    *,
    skip_synaptra: bool = False,
) -> None:
    """Execute the full update sequence.  Raises SystemExit on failure."""
    brain_version = read_version_file(release, "VERSION")
    synaptra_version = read_version_file(release, "SYNAPTRA_VERSION")

    print(f"UPDATE  brain at {brain}")
    print(f"  release: second-brain {brain_version}, synaptra {synaptra_version}")

    release_files = list_release_files(release)
    print(f"  release contains {len(release_files)} files")

    # 1. Backup
    backup_dir = brain / ".claude" / ".update-backup"
    print("BACKUP")
    n = backup_current(brain, backup_dir, release_files)
    print(f"  backed up {n} files to {backup_dir}")

    # 2. Stop synaptra  (R8: before replacing)
    print("STOP synaptra")
    stop_synaptra(brain)

    # 3. Install pinned synaptra  (R2)
    if not skip_synaptra:
        print("INSTALL synaptra")
        install_synaptra(brain, synaptra_version)
        print(f"  synaptra=={synaptra_version} installed")
        verify_synaptra_version(brain, synaptra_version)
        print(f"  verified synaptra.__version__ == {synaptra_version}")

    # 4. Copy product files  (R3)
    print("COPY product files")
    copied = copy_release_files(release, brain, release_files)
    print(f"  copied {copied} product files")

    # 5. Record  (R5)
    print("RECORD")
    write_release_record(brain, brain_version, synaptra_version)

    print(f"DONE  brain updated to second-brain {brain_version}"
          f" + synaptra {synaptra_version}")
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
        "--release", type=Path, default=None,
        help="Path to extracted release (default: resolved from script location)",
    )
    parser.add_argument(
        "--restore", action="store_true",
        help="Restore the pre-update backup instead of updating",
    )
    parser.add_argument(
        "--skip-synaptra", action="store_true",
        help="Skip synaptra install/verify (for file-only testing)",
    )
    args = parser.parse_args()

    brain = args.brain.resolve()
    if not (brain / "CLAUDE.md").exists():
        raise SystemExit(
            f"FAIL: {brain} does not look like a brain root (no CLAUDE.md)"
        )

    if args.restore:
        backup_dir = brain / ".claude" / ".update-backup"
        print("RESTORE from backup")
        n = restore_backup(brain, backup_dir)
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

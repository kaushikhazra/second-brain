#!/usr/bin/env python3
"""R2, R3, R4, R5, R8 proofs: integration test against a scratch brain.

Creates a scratch brain under C:/Projects/.tmp/sb-35-integration/, runs
the update script against it, and verifies:

  R2  synaptra is installed pinned and __version__ matches
  R3  owner files are byte-identical before and after
  R4  backup exists and restore returns the prior tree
  R5  .release-record.json has both version fields
  R8  the run log shows STOP before INSTALL

Uses --skip-synaptra by default (no real synaptra install in CI).
Pass --live to run the real install (requires uv + venv in the scratch brain).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH_ROOT = Path("C:/Projects/.tmp/sb-35-integration")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup_scratch(root: Path) -> None:
    """Create a minimal scratch brain from src/."""
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    # Copy all src/ files
    for dirpath, dirnames, filenames in os.walk(str(SRC)):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__"}]
        for f in filenames:
            src = Path(dirpath) / f
            rel = src.relative_to(SRC)
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))

    # Create fake owner files
    (root / "persona.md").write_text(
        "# Test Persona\nI am a test brain.\n", encoding="utf-8"
    )
    (root / "user.md").write_text("# Test User\nName: Tester\n", encoding="utf-8")
    (root / ".mcp.json").write_text('{"mcpServers": {}}', encoding="utf-8")

    # Create fake synaptra-data
    sd = root / ".claude" / "synaptra-data"
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "test.db").write_text("fake db content", encoding="utf-8")

    # Set an old VERSION to simulate upgrading
    (root / "VERSION").write_text("1.0.0\n", encoding="utf-8")


def main() -> int:
    live = "--live" in sys.argv
    results: list[tuple[str, bool, str]] = []

    # Setup
    print("Setting up scratch brain...")
    setup_scratch(SCRATCH_ROOT)

    # Record owner file hashes before update
    owner_files = [
        "persona.md",
        "user.md",
        ".mcp.json",
        ".claude/synaptra-data/test.db",
    ]
    before_hashes = {}
    for rel in owner_files:
        p = SCRATCH_ROOT / rel
        if p.exists():
            before_hashes[rel] = sha256(p)

    # Record product file hashes for restore check
    product_before: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(str(SCRATCH_ROOT)):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", "synaptra-data"}]
        for f in filenames:
            p = Path(dirpath) / f
            rel = p.relative_to(SCRATCH_ROOT).as_posix()
            if rel not in owner_files:
                product_before[rel] = sha256(p)

    # Run update
    print("Running update...")
    update_script = SRC / ".claude" / "shared" / "update_brain.py"
    cmd = [
        sys.executable,
        str(update_script),
        str(SCRATCH_ROOT),
        "--release",
        str(SRC),
    ]
    if not live:
        cmd.append("--skip-synaptra")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    log = result.stdout + result.stderr
    print(log)

    ok_ran = result.returncode == 0
    results.append(
        ("Update script ran successfully", ok_ran, f"exit {result.returncode}")
    )

    if not ok_ran:
        # Can't check further if the update itself failed
        for name, ok, detail in results:
            print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        return 1

    # -- R3: owner files byte-identical --
    after_hashes = {}
    for rel in owner_files:
        p = SCRATCH_ROOT / rel
        if p.exists():
            after_hashes[rel] = sha256(p)

    r3_ok = before_hashes == after_hashes
    r3_detail = (
        "all identical"
        if r3_ok
        else f"changed: {set(before_hashes.keys()) ^ set(after_hashes.keys()) or [k for k in before_hashes if before_hashes.get(k) != after_hashes.get(k)]}"
    )
    results.append(("R3: owner files byte-identical after update", r3_ok, r3_detail))

    # -- R4: backup exists --
    backup_dir = SCRATCH_ROOT / ".claude" / ".update-backup"
    r4_backup_exists = backup_dir.is_dir()
    backup_count = (
        sum(1 for _ in backup_dir.rglob("*") if _.is_file()) if r4_backup_exists else 0
    )
    results.append(
        (
            "R4: backup directory exists with files",
            r4_backup_exists and backup_count > 0,
            f"{backup_count} files" if r4_backup_exists else "missing",
        )
    )

    # R4: restore returns prior tree
    if r4_backup_exists:
        restore_cmd = [
            sys.executable,
            str(update_script),
            str(SCRATCH_ROOT),
            "--restore",
        ]
        restore_result = subprocess.run(
            restore_cmd, capture_output=True, text=True, timeout=60
        )
        r4_restore_ran = restore_result.returncode == 0
        results.append(
            (
                "R4: restore command succeeded",
                r4_restore_ran,
                f"exit {restore_result.returncode}",
            )
        )

        # Check that restored files match originals
        if r4_restore_ran:
            restored_match = True
            mismatched = []
            for rel, orig_hash in product_before.items():
                p = SCRATCH_ROOT / rel
                if p.exists():
                    if sha256(p) != orig_hash:
                        restored_match = False
                        mismatched.append(rel)
            results.append(
                (
                    "R4: restored files match pre-update state",
                    restored_match,
                    "all match" if restored_match else f"mismatched: {mismatched[:5]}",
                )
            )
    else:
        results.append(("R4: restore command succeeded", False, "no backup to restore"))
        results.append(
            ("R4: restored files match pre-update state", False, "no backup")
        )

    # Re-run update for R5 and R8 checks (restore undid it)
    print("Re-running update for R5/R8 checks...")
    result2 = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    log2 = result2.stdout + result2.stderr

    # -- R5: release record --
    record_path = SCRATCH_ROOT / ".claude" / ".release-record.json"
    r5_exists = record_path.is_file()
    results.append(
        (
            "R5: .release-record.json exists",
            r5_exists,
            str(record_path) if r5_exists else "missing",
        )
    )

    if r5_exists:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        has_brain = "brain_version" in record and record["brain_version"]
        has_synaptra = "synaptra_version" in record and record["synaptra_version"]
        results.append(
            (
                "R5: record has brain_version",
                has_brain,
                record.get("brain_version", "missing"),
            )
        )
        results.append(
            (
                "R5: record has synaptra_version",
                has_synaptra,
                record.get("synaptra_version", "missing"),
            )
        )
    else:
        results.append(("R5: record has brain_version", False, "no record"))
        results.append(("R5: record has synaptra_version", False, "no record"))

    # -- R8: STOP before INSTALL/COPY in log --
    # When --skip-synaptra, INSTALL doesn't appear; verify STOP before COPY
    # (the file replacement).  When --live, also verify STOP before INSTALL.
    stop_idx = log2.find("STOP synaptra")
    copy_idx = log2.find("COPY product files")
    r8_stop_before_copy = stop_idx >= 0 and copy_idx >= 0 and stop_idx < copy_idx
    results.append(
        (
            "R8: STOP appears before COPY in run log",
            r8_stop_before_copy,
            f"STOP@{stop_idx} COPY@{copy_idx}",
        )
    )
    if live:
        install_idx = log2.find("INSTALL synaptra")
        r8_stop_before_install = (
            stop_idx >= 0 and install_idx >= 0 and stop_idx < install_idx
        )
        results.append(
            (
                "R8: STOP appears before INSTALL in run log",
                r8_stop_before_install,
                f"STOP@{stop_idx} INSTALL@{install_idx}",
            )
        )

    # -- R2: check log for pinned install (when --live) --
    if live:
        declared = SRC.joinpath("SYNAPTRA_VERSION").read_text(encoding="utf-8").strip()
        r2_pinned = f"synaptra=={declared}" in log2
        results.append(
            ("R2: installed synaptra pinned to declared version", r2_pinned, declared)
        )

        r2_verified = f"verified synaptra.__version__ == {declared}" in log2
        results.append(
            ("R2: verified __version__ after install", r2_verified, declared)
        )
    else:
        results.append(
            ("R2: (skipped -- pass --live for real install)", True, "--skip-synaptra")
        )

    # Report
    print("\n" + "=" * 60)
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{passed}/{total} checks pass.")

    # Cleanup
    if SCRATCH_ROOT.exists():
        shutil.rmtree(SCRATCH_ROOT)
        print(f"Cleaned up {SCRATCH_ROOT}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

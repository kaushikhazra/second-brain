#!/usr/bin/env python3
"""Defect-fix proofs: four defects in update_brain.py restore/backup logic.

Creates scratch brains under C:/Projects/.tmp/sb-35-defect-*/, exercises
each defect, cleans up after.

Defect 1: restore leaves NEW release files behind (not in prior tree)
Defect 2: restore leaves .release-record.json and synaptra at new version
Defect 3: second update overwrites first backup
Defect 4: failure after backup does not auto-rollback

Uses --skip-synaptra (no real synaptra install).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH_BASE = Path("C:/Projects/.tmp")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_tree(root: Path, exclude_dirs: set[str] | None = None) -> dict[str, str]:
    """Return {rel_posix_path: sha256} for every file, excluding owner dirs."""
    if exclude_dirs is None:
        exclude_dirs = {
            "synaptra-data",
            ".venv",
            ".python",
            "dream-backups",
            "__pycache__",
        }
    result: dict[str, str] = {}
    owner_files = {"persona.md", "user.md", ".mcp.json"}
    owner_prefixes = {
        ".claude/synaptra-data",
        ".claude/dream-backups",
        ".claude/.venv",
        ".claude/.python",
    }
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for f in filenames:
            p = Path(dirpath) / f
            rel = p.relative_to(root).as_posix()
            # skip owner paths
            if rel in owner_files:
                continue
            if any(rel.startswith(pfx + "/") or rel == pfx for pfx in owner_prefixes):
                continue
            # skip backup dirs themselves from snapshot
            if ".update-backup" in rel:
                continue
            result[rel] = sha256(p)
    return result


def make_minimal_brain(root: Path) -> None:
    """Create a brain with FEWER files than src/ -- simulates an older release."""
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    # Only copy a subset of src/ files (skip some skills to simulate new ones)
    for dirpath, dirnames, filenames in os.walk(str(SRC)):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__"}]
        for f in filenames:
            src = Path(dirpath) / f
            rel = src.relative_to(SRC)
            rel_posix = rel.as_posix()
            # Skip the update skill itself -- it will be "new" in the release
            if "skills/curiosity" in rel_posix:
                continue
            # Skip news skill too
            if "skills/news" in rel_posix:
                continue
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))

    # Owner files
    (root / "persona.md").write_text("# Persona\nTest.\n", encoding="utf-8")
    (root / "user.md").write_text("# User\nTest.\n", encoding="utf-8")
    (root / ".mcp.json").write_text('{"mcpServers": {}}', encoding="utf-8")
    sd = root / ".claude" / "synaptra-data"
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "test.db").write_text("owner data", encoding="utf-8")

    # Old version
    (root / "VERSION").write_text("1.0.0\n", encoding="utf-8")


def run_update(
    brain: Path,
    release: Path,
    extra_args: list[str] | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(SRC / ".claude" / "shared" / "update_brain.py"),
        str(brain),
        "--release",
        str(release),
        "--skip-synaptra",
    ]
    if extra_args:
        cmd.extend(extra_args)
    env = {**os.environ}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)


def run_restore(
    brain: Path, extra_args: list[str] | None = None
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(brain / ".claude" / "shared" / "update_brain.py"),
        str(brain),
        "--restore",
        "--skip-synaptra",
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    # ── Defect 1: restore removes NEW files ──────────────────────────

    scratch1 = SCRATCH_BASE / "sb-35-defect1"
    print("=== Defect 1: restore removes NEW release files ===")
    make_minimal_brain(scratch1)
    before1 = snapshot_tree(scratch1)

    # The brain should NOT have curiosity/news skills
    has_curiosity_before = any("skills/curiosity" in k for k in before1)
    results.append(
        (
            "D1-pre: brain lacks curiosity skill before update",
            not has_curiosity_before,
            f"{'absent' if not has_curiosity_before else 'present (test setup wrong)'}",
        )
    )

    r = run_update(scratch1, SRC)
    results.append(("D1: update succeeded", r.returncode == 0, f"exit {r.returncode}"))

    if r.returncode == 0:
        after_update1 = snapshot_tree(scratch1)
        has_curiosity_after = any("skills/curiosity" in k for k in after_update1)
        results.append(
            (
                "D1-mid: curiosity skill now present after update",
                has_curiosity_after,
                f"{'present' if has_curiosity_after else 'absent (update did not copy)'}",
            )
        )

        r_restore = run_restore(scratch1)
        results.append(
            (
                "D1: restore succeeded",
                r_restore.returncode == 0,
                f"exit {r_restore.returncode}",
            )
        )

        after_restore1 = snapshot_tree(scratch1)

        # Key check: no extra files
        extra_files = set(after_restore1.keys()) - set(before1.keys())
        missing_files = set(before1.keys()) - set(after_restore1.keys())
        content_mismatches = [
            k
            for k in before1
            if k in after_restore1 and before1[k] != after_restore1[k]
        ]

        d1_ok = (
            len(extra_files) == 0
            and len(missing_files) == 0
            and len(content_mismatches) == 0
        )
        detail_parts = []
        if extra_files:
            detail_parts.append(f"extra: {sorted(extra_files)[:5]}")
        if missing_files:
            detail_parts.append(f"missing: {sorted(missing_files)[:5]}")
        if content_mismatches:
            detail_parts.append(f"changed: {content_mismatches[:5]}")
        results.append(
            (
                "D1: tree byte-identical after update+restore (no extra files)",
                d1_ok,
                "identical" if d1_ok else "; ".join(detail_parts),
            )
        )

    if scratch1.exists():
        shutil.rmtree(scratch1)

    # ── Defect 2: restore reverts release record ─────────────────────

    scratch2 = SCRATCH_BASE / "sb-35-defect2"
    print("\n=== Defect 2: restore reverts release record ===")
    make_minimal_brain(scratch2)

    # Ensure no release record exists before
    record_path = scratch2 / ".claude" / ".release-record.json"
    if record_path.exists():
        record_path.unlink()

    r = run_update(scratch2, SRC)
    results.append(("D2: update succeeded", r.returncode == 0, f"exit {r.returncode}"))

    if r.returncode == 0:
        has_record_after = record_path.is_file()
        results.append(
            (
                "D2-mid: release record exists after update",
                has_record_after,
                str(has_record_after),
            )
        )

        r_restore = run_restore(scratch2)
        results.append(
            (
                "D2: restore succeeded",
                r_restore.returncode == 0,
                f"exit {r_restore.returncode}",
            )
        )

        record_gone = not record_path.is_file()
        results.append(
            (
                "D2: release record removed after restore (did not exist before)",
                record_gone,
                "removed" if record_gone else "still present (defect)",
            )
        )

    if scratch2.exists():
        shutil.rmtree(scratch2)

    # ── Defect 3: timestamped backups survive second update ──────────

    scratch3 = SCRATCH_BASE / "sb-35-defect3"
    print("\n=== Defect 3: timestamped backups ===")
    make_minimal_brain(scratch3)

    r1 = run_update(scratch3, SRC)
    results.append(
        ("D3: first update succeeded", r1.returncode == 0, f"exit {r1.returncode}")
    )

    backup_root = scratch3 / ".claude" / ".update-backup"
    if r1.returncode == 0:
        # Count backup dirs after first update
        if backup_root.is_dir():
            dirs_after_first = [d for d in backup_root.iterdir() if d.is_dir()]
        else:
            dirs_after_first = []

        # Brief pause to ensure different timestamp
        time.sleep(1.1)

        r2 = run_update(scratch3, SRC)
        results.append(
            ("D3: second update succeeded", r2.returncode == 0, f"exit {r2.returncode}")
        )

        if r2.returncode == 0 and backup_root.is_dir():
            dirs_after_second = [d for d in backup_root.iterdir() if d.is_dir()]
            both_exist = len(dirs_after_second) >= 2
            results.append(
                (
                    "D3: both backups preserved (>= 2 dirs)",
                    both_exist,
                    f"{len(dirs_after_second)} backup dirs: {[d.name for d in dirs_after_second]}"
                    if dirs_after_second
                    else "0 dirs",
                )
            )
        else:
            # Maybe it's a flat dir (old behavior) -- that's the defect
            is_flat = backup_root.is_dir() and any(backup_root.iterdir())
            has_subdirs = backup_root.is_dir() and any(
                d.is_dir() for d in backup_root.iterdir()
            )
            results.append(
                (
                    "D3: both backups preserved (>= 2 dirs)",
                    False,
                    "flat backup (no timestamped dirs)"
                    if is_flat and not has_subdirs
                    else f"second update exit {r2.returncode}",
                )
            )

    if scratch3.exists():
        shutil.rmtree(scratch3)

    # ── Defect 4: auto-rollback on failure after backup ──────────────

    scratch4 = SCRATCH_BASE / "sb-35-defect4"
    print("\n=== Defect 4: auto-rollback on post-backup failure ===")
    make_minimal_brain(scratch4)
    before4 = snapshot_tree(scratch4)

    # Inject a fault at the copy step
    r = run_update(scratch4, SRC, env_extra={"_UPDATE_BRAIN_FAULT_STEP": "copy"})

    # The update SHOULD fail (non-zero exit)
    results.append(
        (
            "D4: update with injected fault exits non-zero",
            r.returncode != 0,
            f"exit {r.returncode}",
        )
    )

    # The tree should be byte-identical to before
    after4 = snapshot_tree(scratch4)
    extra4 = set(after4.keys()) - set(before4.keys())
    missing4 = set(before4.keys()) - set(after4.keys())
    changed4 = [k for k in before4 if k in after4 and before4[k] != after4[k]]

    d4_ok = len(extra4) == 0 and len(missing4) == 0 and len(changed4) == 0
    detail4 = []
    if extra4:
        detail4.append(f"extra: {sorted(extra4)[:5]}")
    if missing4:
        detail4.append(f"missing: {sorted(missing4)[:5]}")
    if changed4:
        detail4.append(f"changed: {changed4[:5]}")
    results.append(
        (
            "D4: tree byte-identical after failed update (auto-rollback)",
            d4_ok,
            "identical" if d4_ok else "; ".join(detail4),
        )
    )

    # Check that the failure message names the failed step
    output = r.stdout + r.stderr
    names_step = "copy" in output.lower() or "COPY" in output
    results.append(
        (
            "D4: failure output names the failed step",
            names_step,
            "mentioned" if names_step else "not mentioned",
        )
    )

    if scratch4.exists():
        shutil.rmtree(scratch4)

    # ── Report ────────────────────────────────────────────────────────

    print("\n" + "=" * 60)
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{passed}/{total} defect checks pass.")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

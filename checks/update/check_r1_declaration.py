#!/usr/bin/env python3
"""R1 proof: A release declares the synaptra version it requires, in one
place in src/.

Structural check — no scratch brain needed.  Scans src/ for files whose
content is a bare semver that names a synaptra version.  Asserts exactly
one such file exists and that both the update script and the init-brain
skill reference it by name.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+\s*$")


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    # 1. Exactly one file named SYNAPTRA_VERSION in src/
    sv_file = SRC / "SYNAPTRA_VERSION"
    exists = sv_file.is_file()
    results.append(
        (
            "SYNAPTRA_VERSION exists in src/",
            exists,
            str(sv_file) if exists else "not found",
        )
    )

    if exists:
        content = sv_file.read_text(encoding="utf-8").strip()
        valid = bool(SEMVER_RE.match(content + "\n"))
        results.append(("SYNAPTRA_VERSION is a valid semver", valid, content))
    else:
        results.append(("SYNAPTRA_VERSION is a valid semver", False, "file missing"))

    # 2. No other file in src/ declares a synaptra version as a standalone
    #    version file (SYNAPTRA_VERSION is the ONE place)
    other_declarations = []
    for p in SRC.rglob("*"):
        if not p.is_file():
            continue
        if p.name == "SYNAPTRA_VERSION":
            continue
        if p.name == "VERSION":
            continue
        # Skip binary / large files
        if p.suffix in {".pyc", ".exe", ".zip", ".bat"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # Look for a line that looks like it declares a synaptra version
        # e.g. synaptra_version = "2.1.1" or SYNAPTRA_VERSION: 2.1.1
        if re.search(r'(?i)synaptra.version\s*[:=]\s*["\']?\d+\.\d+\.\d+', text):
            other_declarations.append(str(p.relative_to(SRC)))

    ok_single = len(other_declarations) == 0
    results.append(
        (
            "No other file hard-codes a synaptra version declaration",
            ok_single,
            "clean" if ok_single else f"found in: {other_declarations}",
        )
    )

    # 3. The update script reads SYNAPTRA_VERSION
    update_script = SRC / ".claude" / "shared" / "update_brain.py"
    if update_script.is_file():
        text = update_script.read_text(encoding="utf-8")
        reads_it = "SYNAPTRA_VERSION" in text
        results.append(
            (
                "update_brain.py reads SYNAPTRA_VERSION",
                reads_it,
                "found" if reads_it else "not found",
            )
        )
    else:
        results.append(
            ("update_brain.py reads SYNAPTRA_VERSION", False, "script not found")
        )

    # 4. The init-brain skill references SYNAPTRA_VERSION
    init_skill = SRC / ".claude" / "skills" / "init-brain" / "SKILL.md"
    if init_skill.is_file():
        text = init_skill.read_text(encoding="utf-8")
        refs_it = "SYNAPTRA_VERSION" in text
        results.append(
            (
                "init-brain SKILL.md references SYNAPTRA_VERSION",
                refs_it,
                "found" if refs_it else "not found",
            )
        )
    else:
        results.append(
            (
                "init-brain SKILL.md references SYNAPTRA_VERSION",
                False,
                "skill not found",
            )
        )

    # Report
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nR1: {passed}/{len(results)} checks pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

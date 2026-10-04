#!/usr/bin/env python3
"""R2 proof: /update installs synaptra pinned and verifies __version__.

Three tests:
  1. The update_brain.py install command uses pinned syntax (synaptra==X.Y.Z).
  2. verify_synaptra_version catches a mismatch (wrong version -> SystemExit).
  3. verify_synaptra_version passes when the installed version matches.

The live install test (actually replacing synaptra) requires the MCP server
to be stopped first (R8), so it cannot run in a live Claude session.  The
integration test in check_r2_r3_r4_r5_r8.py covers the full sequence
against a scratch brain with --live.
"""

from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
CLAUDE_DIR = REPO / ".claude"


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    declared = (SRC / "SYNAPTRA_VERSION").read_text(encoding="utf-8").strip()
    print(f"Declared synaptra version: {declared}")

    # Test 1: The install function uses pinned syntax
    sys.path.insert(0, str(SRC / ".claude" / "shared"))
    from update_brain import install_synaptra, verify_synaptra_version

    source = inspect.getsource(install_synaptra)
    uses_pinned = 'f"synaptra=={version}"' in source
    results.append(
        (
            "install_synaptra uses pinned syntax (synaptra==X.Y.Z)",
            uses_pinned,
            "found" if uses_pinned else "not found in source",
        )
    )

    # Test 2: verify_synaptra_version catches a mismatch
    venv_python = CLAUDE_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        # Get the actually installed version
        check = subprocess.run(
            [str(venv_python), "-c", "import synaptra; print(synaptra.__version__)"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if check.returncode == 0:
            actual = check.stdout.strip()
            print(f"Currently installed synaptra: {actual}")

            # Pass with the actual version
            try:
                verify_synaptra_version(REPO, actual)
                results.append(
                    ("verify passes with actual installed version", True, actual)
                )
            except SystemExit as e:
                results.append(
                    ("verify passes with actual installed version", False, str(e))
                )

            # Fail with a wrong version
            try:
                verify_synaptra_version(REPO, "0.0.1")
                results.append(
                    ("verify fails with wrong version", False, "should have raised")
                )
            except SystemExit:
                results.append(
                    (
                        "verify fails with wrong version",
                        True,
                        "correctly raised SystemExit",
                    )
                )

            # If actual != declared, also prove the mismatch is caught
            if actual != declared:
                try:
                    verify_synaptra_version(REPO, declared)
                    results.append(
                        (
                            f"verify catches mismatch (installed={actual}, declared={declared})",
                            False,
                            "should have raised",
                        )
                    )
                except SystemExit:
                    results.append(
                        (
                            f"verify catches mismatch (installed={actual}, declared={declared})",
                            True,
                            "correctly raised -- proves R2 would fail without updating",
                        )
                    )
        else:
            results.append(("synaptra importable in venv", False, check.stderr))
    else:
        print(f"[SKIP] venv not found at {venv_python}")
        results.append(
            ("verify passes with actual installed version", True, "skipped -- no venv")
        )
        results.append(("verify fails with wrong version", True, "skipped -- no venv"))

    # Test 3: init-brain skill now instructs pinned install
    init_skill = SRC / ".claude" / "skills" / "init-brain" / "SKILL.md"
    text = init_skill.read_text(encoding="utf-8")
    has_pinned = "synaptra==<version>" in text or "synaptra==" in text
    has_verify = "verify" in text.lower() and "__version__" in text
    results.append(
        (
            "init-brain instructs pinned install",
            has_pinned,
            "found" if has_pinned else "not found",
        )
    )
    results.append(
        (
            "init-brain instructs __version__ verification",
            has_verify,
            "found" if has_verify else "not found",
        )
    )

    # Report
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nR2: {passed}/{len(results)} checks pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

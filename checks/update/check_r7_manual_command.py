#!/usr/bin/env python3
"""R7 proof: the update can be run by a single documented manual command
that does not depend on the brain's own skills being current.

Creates a scratch brain pinned to a previous release (simulated with old
VERSION), then runs the update script from the NEW release tree against
it.  Proves the manual path works without Claude or the brain's skills.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH = Path("C:/Projects/.tmp/sb-35-manual")


def setup_old_brain(root: Path) -> None:
    """Simulate a brain on an older release."""
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    # Minimal brain structure
    (root / "CLAUDE.md").write_text("# Old Brain\n", encoding="utf-8")
    (root / "VERSION").write_text("1.0.0\n", encoding="utf-8")

    # Old skill files (would be replaced by update)
    skills = root / ".claude" / "skills" / "session-start"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text(
        "# Old session-start\nOutdated.\n", encoding="utf-8"
    )

    # Owner files that must survive
    (root / "persona.md").write_text("# My Persona\nOriginal.\n", encoding="utf-8")
    (root / "user.md").write_text("# My Profile\nOriginal.\n", encoding="utf-8")
    (root / ".mcp.json").write_text('{"mcpServers":{}}', encoding="utf-8")

    sd = root / ".claude" / "synaptra-data"
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "memories.db").write_text("precious data", encoding="utf-8")


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    setup_old_brain(SCRATCH)

    # The manual command: run NEW release's script against the old brain
    update_script = SRC / ".claude" / "shared" / "update_brain.py"

    # 1. Script exists in the release
    results.append(
        ("update_brain.py exists in src/", update_script.is_file(), str(update_script))
    )

    # 2. Run it -- no Claude, no skills, just python
    cmd = [
        sys.executable,
        str(update_script),
        str(SCRATCH),
        "--release",
        str(SRC),
        "--skip-synaptra",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    log = result.stdout

    ok_ran = result.returncode == 0
    results.append(
        ("Manual command succeeds (exit 0)", ok_ran, f"exit {result.returncode}")
    )

    if ok_ran:
        # 3. Brain is now at the new version
        new_version = (SCRATCH / "VERSION").read_text(encoding="utf-8").strip()
        expected = SRC.joinpath("VERSION").read_text(encoding="utf-8").strip()
        results.append(
            (
                "Brain VERSION updated",
                new_version == expected,
                f"{new_version} (expected {expected})",
            )
        )

        # 4. Owner files untouched
        persona = (SCRATCH / "persona.md").read_text(encoding="utf-8")
        results.append(
            (
                "persona.md preserved",
                persona == "# My Persona\nOriginal.\n",
                "identical" if "Original" in persona else "changed",
            )
        )

        user = (SCRATCH / "user.md").read_text(encoding="utf-8")
        results.append(
            (
                "user.md preserved",
                user == "# My Profile\nOriginal.\n",
                "identical" if "Original" in user else "changed",
            )
        )

        memories = (SCRATCH / ".claude" / "synaptra-data" / "memories.db").read_text(
            encoding="utf-8"
        )
        results.append(
            (
                "synaptra-data preserved",
                memories == "precious data",
                "identical" if memories == "precious data" else "changed",
            )
        )

        # 5. Release record written
        record_path = SCRATCH / ".claude" / ".release-record.json"
        results.append(
            (
                "Release record written",
                record_path.is_file(),
                "exists" if record_path.is_file() else "missing",
            )
        )

        # 6. New skills are present
        new_update_skill = SCRATCH / ".claude" / "skills" / "update" / "SKILL.md"
        results.append(
            (
                "New /update skill present",
                new_update_skill.is_file(),
                "exists" if new_update_skill.is_file() else "missing",
            )
        )

        # 7. Old session-start was replaced
        ss = (SCRATCH / ".claude" / "skills" / "session-start" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        results.append(
            (
                "session-start SKILL.md replaced (not 'Outdated')",
                "Outdated" not in ss,
                "updated" if "Outdated" not in ss else "still old",
            )
        )
    else:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")

    # 8. The skill documents the manual path
    skill_path = SRC / ".claude" / "skills" / "update" / "SKILL.md"
    if skill_path.is_file():
        skill_text = skill_path.read_text(encoding="utf-8")
        has_manual = "manual" in skill_text.lower() and "update_brain.py" in skill_text
        results.append(
            (
                "Skill documents the manual command",
                has_manual,
                "found" if has_manual else "not found",
            )
        )

    # Report
    print("\n" + "=" * 60)
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nR7: {passed}/{len(results)} checks pass.")

    # Cleanup
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
        print(f"Cleaned up {SCRATCH}")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

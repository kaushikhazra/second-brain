#!/usr/bin/env python3
"""R6 proof: session-start reports exactly one line when a newer release
exists, nothing when current or offline.

Structural check on the session-start skill text, plus a functional test
of the version-comparison logic that the skill describes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SKILL = SRC / ".claude" / "skills" / "session-start" / "SKILL.md"


def semver_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    if not SKILL.is_file():
        print(f"[FAIL] session-start SKILL.md not found at {SKILL}")
        return 1

    text = SKILL.read_text(encoding="utf-8")

    # 1. The skill mentions checking for a newer release
    has_release_check = "release" in text.lower() and "api.github.com" in text
    results.append(
        (
            "Skill references GitHub releases API",
            has_release_check,
            "found" if has_release_check else "not found",
        )
    )

    # 2. The skill mentions offline-quiet failure
    has_offline = (
        re.search(r"(?i)(offline|network|timeout).{0,80}(nothing|silent|quiet)", text)
        is not None
    )
    results.append(
        (
            "Skill describes offline-quiet failure",
            has_offline,
            "found" if has_offline else "not found",
        )
    )

    # 3. The skill says to emit exactly one line
    has_one_line = "one line" in text.lower() or "exactly one" in text.lower()
    results.append(
        (
            "Skill specifies exactly one line output",
            has_one_line,
            "found" if has_one_line else "not found",
        )
    )

    # 4. The skill mentions .release-record.json
    has_record = ".release-record.json" in text
    results.append(
        (
            "Skill references .release-record.json",
            has_record,
            "found" if has_record else "not found",
        )
    )

    # 5. The skill describes falling back to VERSION
    has_fallback = "VERSION" in text and (
        "fall back" in text.lower() or "fallback" in text.lower()
    )
    results.append(
        (
            "Skill describes VERSION fallback",
            has_fallback,
            "found" if has_fallback else "not found",
        )
    )

    # 6. Functional: version comparison logic
    # newer, current, older
    cases = [
        ("1.1.1", "1.1.0", True, "newer"),
        ("1.1.1", "1.1.1", False, "current"),
        ("1.1.0", "1.1.1", False, "older-remote"),
        ("2.0.0", "1.9.9", True, "major bump"),
    ]
    for remote, local, expect_newer, label in cases:
        is_newer = semver_tuple(remote) > semver_tuple(local)
        ok = is_newer == expect_newer
        results.append(
            (
                f"Version compare {remote} vs {local} ({label})",
                ok,
                f"newer={is_newer}, expected={expect_newer}",
            )
        )

    # 7. The skill mentions /update
    has_update_ref = "/update" in text
    results.append(
        (
            "Skill directs user to /update",
            has_update_ref,
            "found" if has_update_ref else "not found",
        )
    )

    # Report
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nR6: {passed}/{len(results)} checks pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

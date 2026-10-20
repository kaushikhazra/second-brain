#!/usr/bin/env python3
"""Issue #66: a release obeys only the owner.

Checks (exit 1 on any failure):
  AC 1-3  the CLAUDE.md in `git archive HEAD:src` has no orchestration section,
          names no session/persona/channel as the owner's voice, and has no
          instruction to act unconfirmed on another session's message.
  AC 4    a brain extracted from dist/second-brain-1.5.0.zip, updated with
          update_brain.py from that archive, ends up meeting AC 1-3.
          (Skipped with a note if the 1.5.0 zip is not in dist/.)
  AC 5    the shipped CLAUDE.md tells the brain to get the owner's confirmation
          before acting on a message from another session.

Stdlib only. Run from anywhere inside the repo: python checks/owner-only/check_owner_only.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=Path(__file__).resolve().parent,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
)

FORBIDDEN = {
    "orchestration section": re.compile(r"^#+\s*Orchestration over", re.I | re.M),
    "named session as owner's voice": re.compile(r"velasari|relayed", re.I),
    "crosschat channel as instruction source": re.compile(r"crosschat channel", re.I),
    "act without confirmation": re.compile(
        r"do not ask for confirmation|without (asking|confirmation)", re.I
    ),
}
REQUIRED = re.compile(r"owner'?s confirmation", re.I)


def problems(claude_md: str) -> list[str]:
    out = [
        f"forbidden: {name}" for name, rx in FORBIDDEN.items() if rx.search(claude_md)
    ]
    if not REQUIRED.search(claude_md):
        out.append("missing: owner-confirmation rule for other sessions' messages")
    return out


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        new_zip = tmp / "new.zip"
        new_zip.write_bytes(
            subprocess.run(
                ["git", "archive", "--format=zip", "HEAD:src"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout
        )
        with zipfile.ZipFile(new_zip) as zf:
            zf.extractall(tmp / "release")
        bad = problems((tmp / "release" / "CLAUDE.md").read_text(encoding="utf-8"))
        print("AC 1-3,5 release CLAUDE.md:", "OK" if not bad else bad)
        failures += bool(bad)

        old_zip = ROOT / "dist" / "second-brain-1.5.0.zip"
        if not old_zip.exists():
            print("AC 4 skipped: dist/second-brain-1.5.0.zip not present")
            return 1 if failures else 0
        with zipfile.ZipFile(old_zip) as zf:
            zf.extractall(tmp / "brain")
        before = problems((tmp / "brain" / "CLAUDE.md").read_text(encoding="utf-8"))
        if not before:
            print(
                "AC 4 invalid: the 1.5.0 brain already passes, so the test proves nothing"
            )
            return 1
        subprocess.run(
            [
                sys.executable,
                "-I",
                str(tmp / "release" / ".claude" / "shared" / "update_brain.py"),
                str(tmp / "brain"),
                "--release",
                str(tmp / "release"),
                "--skip-synaptra",
            ],
            check=True,
            capture_output=True,
        )
        after = problems((tmp / "brain" / "CLAUDE.md").read_text(encoding="utf-8"))
        print(
            f"AC 4 1.5.0 brain had {len(before)} problems; after update:",
            "OK" if not after else after,
        )
        failures += bool(after)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

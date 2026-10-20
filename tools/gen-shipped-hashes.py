#!/usr/bin/env python3
"""Write ``src/.claude/shared/shipped_hashes.json``.

The table maps every product file path to the sha256 of that file in every
release tag and in HEAD. ``update_brain.py`` uses it to tell a file the owner
edited from a shipped copy they never touched, which is what lets an update
keep their edits -- including on brains from releases that installed no
manifest of their own.

Run it before building a release, then commit the result:

    python tools/gen-shipped-hashes.py

Tags from before the ``src/`` split are read from the repo root. Stdlib only.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tarfile
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
sys.path.insert(0, str(ROOT / "src" / ".claude" / "shared"))
from update_brain import SHIPPED_HASHES, normalized_sha256  # noqa: E402


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=check)


def tree_hashes(ref: str) -> dict[str, str]:
    """{path: hash} of the product tree at *ref* (``src/`` if it has one)."""
    spec = f"{ref}:src"
    if git("rev-parse", "--verify", "--quiet", spec, check=False).returncode != 0:
        spec = ref
    blob = git("archive", "--format=tar", spec).stdout
    out: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        for m in tar.getmembers():
            if m.isfile():
                out[m.name] = normalized_sha256(tar.extractfile(m).read())
    return out


def main() -> int:
    tags = git("tag", "--list").stdout.decode().split()
    table: dict[str, set[str]] = {}
    for ref in [*tags, "HEAD"]:
        for path, digest in tree_hashes(ref).items():
            table.setdefault(path, set()).add(digest)
    table.pop(SHIPPED_HASHES, None)  # the table cannot hold its own hash
    doc = {
        "schema": 1,
        "releases": tags,
        "files": {p: sorted(h) for p, h in sorted(table.items())},
    }
    out = ROOT / "src" / SHIPPED_HASHES
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}: {len(table)} paths from {len(tags)} tags + HEAD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

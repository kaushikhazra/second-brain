#!/usr/bin/env python3
"""Issue #94: an update never overwrites a file it cannot prove untouched.

Builds a pre-1.6 brain from `git archive v1.3.0:src` (no shipped-hash record of
its own) and runs the working tree's update_brain.py against it. Prints one line
per criterion; exit 1 if any fails.

    python checks/update-conflict/check_pre16_conflict.py
"""

from __future__ import annotations

import shutil
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
OLD_TAG = "v1.3.0"
MINE = b"\n## My own rule\nAlways greet me.\n"
results: list[tuple[str, bool, str]] = []


def record(ac: str, ok: bool, note: str = "") -> None:
    results.append((ac, ok, note))
    print(f"{'PASS' if ok else 'FAIL'}  {ac}  {note}")


def run(release: Path, brain: Path, *extra: str) -> str:
    script = release / ".claude" / "shared" / "update_brain.py"
    out = subprocess.run(
        [sys.executable, "-I", str(script), str(brain), "--release", str(release)]
        + list(extra),
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stdout + out.stderr)
    return out.stdout


def update(release: Path, brain: Path) -> str:
    return run(release, brain, "--skip-synaptra")


def pre16_brain(dest: Path, edited: bool) -> Path:
    blob = subprocess.run(
        ["git", "archive", "--format=zip", f"{OLD_TAG}:src"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    z = dest.with_suffix(".zip")
    z.write_bytes(blob)
    with zipfile.ZipFile(z) as zf:
        zf.extractall(dest)
    if edited:
        f = dest / "CLAUDE.md"
        f.write_bytes(f.read_bytes() + MINE)
    return dest


def news(brain: Path) -> list[str]:
    return sorted(p.relative_to(brain).as_posix() for p in brain.rglob("*.new"))


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        release = tmp / "release"
        shutil.copytree(
            ROOT / "src", release, ignore=shutil.ignore_patterns("__pycache__")
        )
        release_claude = (release / "CLAUDE.md").read_bytes()

        # AC 1: an edited pre-1.6 CLAUDE.md is kept, never overwritten
        b = pre16_brain(tmp / "edited", edited=True)
        mine = (b / "CLAUDE.md").read_bytes()
        log = update(release, b)
        record(
            "AC 1  pre-1.6 edit kept, release beside it",
            (b / "CLAUDE.md").read_bytes() == mine
            and (b / "CLAUDE.md.new").read_bytes() == release_claude,
        )

        # AC 2: the owner is shown the diff and offered take / keep / merge
        record(
            "AC 2  diff shown, take/keep/merge offered",
            "CONFLICT" in log
            and "--- yours" in log
            and "+++ release" in log
            and "take" in log
            and "keep" in log
            and "merge" in log,
        )

        # AC 3: --take installs the release's file and drops the .new
        c = pre16_brain(tmp / "take", edited=True)
        update(release, c)
        run(release, c, "--take", "CLAUDE.md")
        record(
            "AC 3  --take installs the release's file",
            (c / "CLAUDE.md").read_bytes() == release_claude and not news(c),
        )

        # AC 4: --keep leaves the owner's file and drops the .new
        k = pre16_brain(tmp / "keep", edited=True)
        update(release, k)
        run(release, k, "--keep", "CLAUDE.md")
        record(
            "AC 4  --keep leaves the owner's file",
            (k / "CLAUDE.md").read_bytes() == mine and not news(k),
        )

        # AC 5: an untouched pre-1.6 brain is replaced silently, no conflict
        p = pre16_brain(tmp / "pristine", edited=False)
        log = update(release, p)
        record(
            "AC 5  untouched pre-1.6 brain replaced, no conflict",
            (p / "CLAUDE.md").read_bytes() == release_claude
            and not news(p)
            and "CONFLICT" not in log,
        )

        # AC 6: a release with no hash table proves nothing -- differing files
        # are conflicts, none is overwritten
        bare = tmp / "bare-release"
        shutil.copytree(release, bare)
        (bare / ".claude" / "shared" / "shipped_hashes.json").unlink()
        q = pre16_brain(tmp / "nohash", edited=False)
        before = (q / "CLAUDE.md").read_bytes()
        log = update(bare, q)
        record(
            "AC 6  no hash table: differing file kept as a conflict",
            (q / "CLAUDE.md").read_bytes() == before
            and "CLAUDE.md.new" in news(q)
            and "CONFLICT" in log,
            f".new={news(q)}",
        )

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks hold")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

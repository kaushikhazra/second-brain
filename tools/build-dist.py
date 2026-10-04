#!/usr/bin/env python3
"""Build the distributable second-brain archive.

Produces ``dist/second-brain-<VERSION>.zip`` containing exactly what a fresh
brain needs: the tracked files under ``src/``, and nothing else.

The archive is written by ``git archive HEAD:src``, not by copying the working
directory. That is deliberate. A working directory carries the provisioned
runtime (``.claude/.venv`` is ~900 MB), the memory store, generated
``.mcp.json``, specs, and whatever a test left behind — and a copy-based
builder would ship all of it the first time someone ran it on a dirty tree.
Building from the git tree makes the mechanism *incapable* of that error
rather than relying on anyone remembering to avoid it.

Because ``HEAD:src`` archives only the subtree, nothing outside ``src/`` can
reach the artifact — no ``.gitattributes`` rules needed. Adding a test or loop
file at the repo root cannot change what ships.

Stdlib only. Run from anywhere inside the repo:

    python tools/build-dist.py
"""

from __future__ import annotations

import argparse
import fnmatch
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

# Anything matching these must never reach a user's machine. The builder
# asserts their absence rather than trusting that git got it right.
FORBIDDEN = (
    ".venv",
    ".python",
    "synaptra-data",
    "dream-backups",
    ".mcp.json",
    ".self-aware",
    ".claude/specs",
    ".update-backup",
    ".release-record.json",
    ".tmp",
    ".git/",
    "uv.exe",
    "__pycache__",
)

# Basename globs that must never appear in the artifact.
#
# These exist because the set-equality check against `git archive` CANNOT
# catch an exclusion regression. `export-ignore` changes what `git archive`
# emits, so both sides of that comparison move together and it keeps passing
# whether or not the exclusion worked. Only an assert stated in absolute
# terms — "no file named test_*.py is in this zip" — can actually fail.
FORBIDDEN_GLOBS = ("test_*.py",)


class BuildError(RuntimeError):
    """Raised when the archive is not what it must be."""


def git(*args: str, repo: Path, binary: bool = False):
    """Run a git command in *repo*, returning stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout if binary else result.stdout.decode("utf-8")


def repo_root() -> Path:
    """The top of the working tree, resolved at runtime — never hardcoded."""
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=Path(__file__).resolve().parent,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return Path(out.stdout.decode("utf-8").strip())


def read_version(root: Path) -> str:
    version = (root / "src" / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise BuildError("VERSION is empty")
    return version


def expected_members(root: Path) -> set[str]:
    """File list ``git archive HEAD:src`` would produce.

    ``HEAD:src`` archives the subtree with the ``src/`` prefix already stripped,
    so the resulting paths are brain-relative — exactly what a user unpacks.
    """
    blob = git("archive", "--format=tar", "HEAD:src", repo=root, binary=True)
    with tempfile.TemporaryDirectory() as tmp:
        tar_path = Path(tmp) / "ref.tar"
        tar_path.write_bytes(blob)
        with tarfile.open(tar_path) as tar:
            return {m.name for m in tar.getmembers() if m.isfile()}


def check_forbidden(names: set[str]) -> None:
    bad = sorted(n for n in names for f in FORBIDDEN if f in n)
    if bad:
        raise BuildError(f"archive contains files that must never ship: {bad}")
    globbed = sorted(
        n
        for n in names
        for g in FORBIDDEN_GLOBS
        if fnmatch.fnmatch(PurePosixPath(n).name, g)
    )
    if globbed:
        raise BuildError(
            f"archive contains development-only files matching {FORBIDDEN_GLOBS}: "
            f"{globbed} — check .gitattributes export-ignore"
        )


def build(root: Path, version: str, *, force: bool = False) -> Path:
    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    out = dist / f"second-brain-{version}.zip"
    if out.exists():
        if not force:
            raise BuildError(
                f"{out} already exists. Pass --force to overwrite. "
                f"This guard exists because VERSION may still point at a "
                f"shipped release whose dist/ zip is the only copy on disk."
            )
        out.unlink()
    blob = git("archive", "--format=zip", "HEAD:src", repo=root, binary=True)
    out.write_bytes(blob)
    return out


def verify(out: Path, expected: set[str]) -> set[str]:
    """Extract to a clean temp dir and assert the file list matches exactly."""
    with zipfile.ZipFile(out) as zf:
        if zf.testzip() is not None:
            raise BuildError("zip failed its own integrity check")
        listed = {n for n in zf.namelist() if not n.endswith("/")}
        with tempfile.TemporaryDirectory() as tmp:
            zf.extractall(tmp)
            base = Path(tmp)
            extracted = {
                p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()
            }

    for label, actual in (("zip manifest", listed), ("extracted tree", extracted)):
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise BuildError(
                f"{label} differs from `git archive`: missing={missing} extra={extra}"
            )

    check_forbidden(extracted)
    return extracted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing archive instead of refusing",
    )
    args = parser.parse_args()

    if shutil.which("git") is None:
        print("git is not on PATH — this builder needs it.", file=sys.stderr)
        return 1

    root = repo_root()
    try:
        version = read_version(root)
        expected = expected_members(root)
        check_forbidden(expected)
        out = build(root, version, force=args.force)
        files = verify(out, expected)
    except (BuildError, subprocess.CalledProcessError) as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1

    size = out.stat().st_size
    print(f"built   : {out}")
    print(f"version : {version}")
    print(f"files   : {len(files)}")
    print(f"size    : {size:,} bytes ({size / 1024:.1f} KB)")
    print("verified: extracted file list == `git archive HEAD:src` output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

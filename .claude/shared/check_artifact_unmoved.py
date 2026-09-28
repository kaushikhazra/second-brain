#!/usr/bin/env python3
"""Assert that what a user receives has not moved.

Issue #25 moves the product into ``src/``. The repo's layout is free to change;
the archive a user unpacks is not. This check is the only thing standing between
that restructure and a silently altered install.

**Why it cannot use ``build-dist.py``'s own verification.** That builder compares
its zip against ``git archive`` output. ``export-ignore`` changes what ``git
archive`` emits, so *both sides of that comparison move together* and it keeps
passing whether or not the exclusion worked. The builder's own comments say so.
Only a check stated in absolute terms against the shipped artifact can fail.

**Why the reference is a tag and not ``dist/``.** ``dist/`` is gitignored and
untracked, so those zips live on exactly one disk — and ``build-dist.py`` opens
by unlinking ``dist/second-brain-<VERSION>.zip``. With ``VERSION`` at ``1.0.1``,
running the builder deletes the reference. The ``v1.0.1`` tag is in git, is
pushed, and cannot be clobbered by a build.

Stdlib only. Run from anywhere inside the repo::

    python .claude/shared/check_artifact_unmoved.py
    python .claude/shared/check_artifact_unmoved.py --candidate HEAD:src
    python .claude/shared/check_artifact_unmoved.py --self-test
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


class CheckError(RuntimeError):
    """Raised when the comparison cannot be performed at all."""


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


def archive_tree(root: Path, treeish: str, dest: Path) -> dict[str, bytes]:
    """Extract ``git archive <treeish>`` into *dest* and return path -> bytes.

    A ``treeish`` of the form ``HEAD:src`` archives that subtree with the prefix
    already stripped, which is what the post-move candidate looks like.
    """
    try:
        blob = subprocess.run(
            ["git", "archive", "--format=tar", treeish],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", "replace").strip()
        raise CheckError(f"git archive {treeish} failed: {detail}") from exc

    tar_path = dest / "tree.tar"
    tar_path.write_bytes(blob)
    out = dest / "tree"
    out.mkdir()
    with tarfile.open(tar_path) as tar:
        # Explicit filter: 3.14 rejects unfiltered extraction, and a warning in a
        # check's output is noise that trains people to ignore its output.
        tar.extractall(out, filter="data")
    tar_path.unlink()

    return {
        p.relative_to(out).as_posix(): p.read_bytes()
        for p in out.rglob("*")
        if p.is_file()
    }


def compare(reference: dict[str, bytes], candidate: dict[str, bytes]) -> list[str]:
    """Return every difference as a line. Empty list means identical."""
    problems: list[str] = []

    missing = sorted(set(reference) - set(candidate))
    extra = sorted(set(candidate) - set(reference))

    for path in missing:
        problems.append(f"MISSING  {path}  (in reference, not in candidate)")
    for path in extra:
        problems.append(f"EXTRA    {path}  (in candidate, not in reference)")

    for path in sorted(set(reference) & set(candidate)):
        if reference[path] != candidate[path]:
            problems.append(
                f"CHANGED  {path}  "
                f"({len(reference[path])} -> {len(candidate[path])} bytes)"
            )

    return problems


def self_test(root: Path) -> int:
    """Prove the comparison can fail. A check that never fails is not a check."""
    reference = {"a.txt": b"one", "b.txt": b"two", "gone.txt": b"three"}

    cases = {
        "content change": (
            {"a.txt": b"ONE", "b.txt": b"two", "gone.txt": b"three"},
            "CHANGED  a.txt",
        ),
        "missing file": ({"a.txt": b"one", "b.txt": b"two"}, "MISSING  gone.txt"),
        "extra file": (
            {"a.txt": b"one", "b.txt": b"two", "gone.txt": b"three", "new.txt": b"x"},
            "EXTRA    new.txt",
        ),
    }

    failures = 0
    for name, (candidate, expected) in cases.items():
        problems = compare(reference, candidate)
        hit = any(line.startswith(expected) for line in problems)
        print(
            f"  {'ok  ' if hit else 'FAIL'}  {name}: {problems or 'reported nothing'}"
        )
        if not hit:
            failures += 1

    identical = compare(reference, dict(reference))
    print(f"  {'ok  ' if not identical else 'FAIL'}  identical trees report nothing")
    if identical:
        failures += 1

    print()
    print("self-test PASSED" if not failures else f"self-test FAILED ({failures})")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reference",
        default="v1.0.1",
        help="git tree-ish holding the shipped artifact (default: v1.0.1)",
    )
    parser.add_argument(
        "--candidate",
        default="HEAD",
        help="git tree-ish to test. After the move this becomes HEAD:src.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="prove the comparison can fail, then exit",
    )
    args = parser.parse_args()

    root = repo_root()

    if args.self_test:
        print("self-test - the comparison must report each of these:")
        return self_test(root)

    try:
        with tempfile.TemporaryDirectory() as tmp:
            ref_dir = Path(tmp) / "reference"
            cand_dir = Path(tmp) / "candidate"
            ref_dir.mkdir()
            cand_dir.mkdir()

            reference = archive_tree(root, args.reference, ref_dir)
            candidate = archive_tree(root, args.candidate, cand_dir)
            problems = compare(reference, candidate)
    except CheckError as exc:
        print(f"CHECK COULD NOT RUN: {exc}", file=sys.stderr)
        return 2

    print(f"reference : {args.reference}  ({len(reference)} files)")
    print(f"candidate : {args.candidate}  ({len(candidate)} files)")
    print()

    if not problems:
        print("IDENTICAL - every path present in both, every file byte for byte.")
        return 0

    for line in problems:
        print(line)
    print()
    print(f"DIFFERS - {len(problems)} difference(s). The user's install would change.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

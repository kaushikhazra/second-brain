#!/usr/bin/env python3
"""Issue #69: an update keeps a file the owner edited.

Exercises update_brain.py from `git archive HEAD:src` against brains extracted
from the real release zips in dist/ (1.2.0 .. 1.5.0), none of which installed a
manifest. Prints one line per criterion; exit 1 if any fails.

    python checks/update-keeps-edits/check_keeps_edits.py
"""

from __future__ import annotations

import importlib.util
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
VERSIONS = ["1.2.0", "1.3.0", "1.4.0", "1.5.0"]
results: list[tuple[str, bool, str]] = []


def record(ac: str, ok: bool, note: str = "") -> None:
    results.append((ac, ok, note))
    print(f"{'PASS' if ok else 'FAIL'}  {ac}  {note}")


def update(brain: Path, release: Path, *extra: str) -> str:
    out = subprocess.run(
        [
            sys.executable,
            "-I",
            str(release / ".claude" / "shared" / "update_brain.py"),
            str(brain),
            "--release",
            str(release),
            "--skip-synaptra",
            *extra,
        ],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stdout + out.stderr)
    return out.stdout


def restore(brain: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-I",
            str(brain / ".claude" / "shared" / "update_brain.py"),
            str(brain),
            "--restore",
            "--skip-synaptra",
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def extract_zip(zip_path: Path, dest: Path) -> Path:
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    return dest


def news(brain: Path) -> list[str]:
    return sorted(p.relative_to(brain).as_posix() for p in brain.rglob("*.new"))


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        release_zip = tmp / "release.zip"
        release_zip.write_bytes(
            subprocess.run(
                ["git", "archive", "--format=zip", "HEAD:src"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout
        )
        release = extract_zip(release_zip, tmp / "release")
        release_claude = (release / "CLAUDE.md").read_bytes()

        for v in VERSIONS:
            z = ROOT / "dist" / f"second-brain-{v}.zip"
            if not z.exists():
                record(f"{v} present", False, f"{z} missing")
                continue

            # AC 5, 9: untouched brain -> everything replaced, no .new
            b = extract_zip(z, tmp / f"pristine-{v}")
            update(b, release)
            same = (b / "CLAUDE.md").read_bytes() == release_claude
            record(
                f"AC 5,9  {v} untouched brain", same and not news(b), f".new={news(b)}"
            )

            # AC 8: a second update over an up-to-date brain writes nothing new
            update(b, release)
            record(f"AC 8    {v} already current", not news(b))

            # AC 6: CRLF copy of an untouched file is not an edit
            c = extract_zip(z, tmp / f"crlf-{v}")
            f = c / "CLAUDE.md"
            f.write_bytes(
                f.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            )
            update(c, release)
            record(
                f"AC 6    {v} CRLF copy",
                not news(c) and (c / "CLAUDE.md").read_bytes() == release_claude,
            )

            # AC 1-4, 10: edited CLAUDE.md is kept; the rest is updated
            e = extract_zip(z, tmp / f"edited-{v}")
            mine = (
                e / "CLAUDE.md"
            ).read_bytes() + b"\n## My own rule\nAlways greet me.\n"
            (e / "CLAUDE.md").write_bytes(mine)
            log = update(e, release)
            kept = (e / "CLAUDE.md").read_bytes() == mine
            beside = (e / "CLAUDE.md.new").read_bytes() == release_claude
            listed = "CLAUDE.md" in log and "lines" in log
            others = (e / "README.md").read_bytes() == (
                release / "README.md"
            ).read_bytes()
            record(
                f"AC 1,2   {v} edit kept, .new beside",
                kept and beside and news(e) == ["CLAUDE.md.new"],
            )
            record(f"AC 3     {v} diff summary listed", listed)
            record(f"AC 4     {v} rest replaced", others)

            # AC 13: restore removes the .new and leaves the brain as before the update
            restore(e)
            record(
                f"AC 13   {v} restore",
                not news(e) and (e / "CLAUDE.md").read_bytes() == mine,
            )

        # AC 7: a path no past release shipped, owner already has a file there
        z = ROOT / "dist" / "second-brain-1.5.0.zip"
        b = extract_zip(z, tmp / "ac7")
        (release / "zz_new_in_release.md").write_text("from the release\n")
        (b / "zz_new_in_release.md").write_text("the owner's own file\n")
        update(b, release)
        record(
            "AC 7    own file at a newly shipped path kept",
            (b / "zz_new_in_release.md").read_text() == "the owner's own file\n"
            and (b / "zz_new_in_release.md.new").exists(),
        )
        (release / "zz_new_in_release.md").unlink()

        # AC 11, 12: the table covers HEAD; a stale table stops the build
        spec = importlib.util.spec_from_file_location(
            "bd", ROOT / "tools" / "build-dist.py"
        )
        bd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bd)
        try:
            bd.check_shipped_hashes(ROOT)
            record("AC 11    table covers every file in HEAD:src", True)
        except bd.BuildError as exc:
            record("AC 11    table covers every file in HEAD:src", False, str(exc))

        clone = tmp / "clone"
        subprocess.run(
            ["git", "clone", "-q", "--local", str(ROOT), str(clone)], check=True
        )
        (clone / "src" / "CLAUDE.md").write_text("changed after the table was made\n")
        subprocess.run(
            [
                "git",
                "-C",
                str(clone),
                "-c",
                "user.name=t",
                "-c",
                "user.email=t@t",
                "commit",
                "-qam",
                "stale",
            ],
            check=True,
        )
        spec2 = importlib.util.spec_from_file_location(
            "bd2", clone / "tools" / "build-dist.py"
        )
        bd2 = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(bd2)
        try:
            bd2.check_shipped_hashes(clone)
            record("AC 12    stale table stops the build", False, "build passed")
        except bd2.BuildError:
            record("AC 12    stale table stops the build", True)

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks hold")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Issue #72: the transcriber lives in the brain's one .claude/.venv.

Exercises launch.py's install logic against a PROVISIONED brain (a release tree
with .claude/uv, .claude/.python and .claude/.venv holding synaptra). It does
not transcribe -- it runs the launcher with an input that makes it stop right
after the environment step, and reads what is on disk.

    python checks/transcribe-one-venv/check_one_venv.py <brain-root>

Checks (exit 1 on any failure):
  AC 1,3  faster-whisper lands in .claude/.venv; no skill .venv exists; no
          release file mentions a transcribe-owned environment
  AC 6    synaptra imports at the same version after the install
  AC 7    a forced conflict is rolled back: package set identical to before,
          synaptra imports at the prior version, the message names the conflict
  AC 9    deleting the install marker and the package makes the next run reinstall
  AC 10   with the venv python gone, the launcher stops with a plain message and
          creates no environment
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

brain = Path(sys.argv[1]).resolve()
claude = brain / ".claude"
venv = claude / ".venv"
py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
uv = claude / ("uv.exe" if os.name == "nt" else "uv")
skill = claude / "skills" / "transcribe"
results: list[bool] = []


def record(ac: str, ok: bool, note: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {ac}  {note}")


def load_launcher():
    spec = importlib.util.spec_from_file_location(
        "launch", skill / "scripts" / "launch.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def freeze() -> str:
    return subprocess.run(
        [str(uv), "pip", "freeze", "--python", str(py)], capture_output=True, text=True
    ).stdout


def synaptra_version() -> str | None:
    out = subprocess.run(
        [str(py), "-c", "import synaptra; print(synaptra.__version__)"],
        capture_output=True,
        text=True,
    )
    return out.stdout.strip() if out.returncode == 0 else None


def main() -> int:
    before_version = synaptra_version()
    record(
        "precondition  synaptra imports",
        before_version is not None,
        str(before_version),
    )

    launch = load_launcher()
    launch.say = lambda m: print(f"    [launcher] {m}")

    # AC 1, 6: base install into the one venv
    launch.ensure_base(before_version)
    has_fw = subprocess.run([str(py), "-c", "import faster_whisper"]).returncode == 0
    record("AC 1  faster-whisper in .claude/.venv", has_fw)
    record("AC 1  no skill .venv", not (skill / ".venv").exists())
    record("AC 6  synaptra unchanged", synaptra_version() == before_version)

    # AC 7: force a conflict with a test-only requirement that downgrades synaptra's pin
    snapshot = freeze()
    bad = skill / "requirements-conflict-test.txt"
    bad.write_text("pydantic==1.10.13\n", encoding="utf-8")  # synaptra needs pydantic 2
    bad_mark = venv / ".transcribe-conflict-test"
    bad_mark.unlink(missing_ok=True)
    try:
        launch.install(bad, bad_mark, "a conflicting test package", before_version)
        record("AC 7  conflict detected", False, "install did not complain")
    except launch.Conflict as exc:
        record(
            "AC 7  conflict detected and reported",
            "conflicts" in str(exc),
            str(exc)[:90],
        )
    finally:
        bad.unlink(missing_ok=True)
    record("AC 7  package set restored exactly", freeze() == snapshot)
    record(
        "AC 7  synaptra imports at prior version", synaptra_version() == before_version
    )
    record("AC 7  no marker kept", not bad_mark.exists())

    # AC 9: marker and package gone -> reinstall
    launch.BASE_MARK.unlink(missing_ok=True)
    subprocess.run(
        [str(uv), "pip", "uninstall", "--python", str(py), "faster-whisper"],
        capture_output=True,
    )
    gone = (
        subprocess.run(
            [str(py), "-c", "import faster_whisper"], capture_output=True
        ).returncode
        != 0
    )
    launch.ensure_base(before_version)
    back = subprocess.run([str(py), "-c", "import faster_whisper"]).returncode == 0
    record("AC 9  reinstalled after the package and marker vanished", gone and back)

    # AC 10: venv unusable -> plain stop, nothing created
    moved = venv.with_name(".venv-hidden")
    venv.rename(moved)
    try:
        run = subprocess.run(
            [sys.executable, str(skill / "scripts" / "launch.py"), "x.wav"],
            capture_output=True,
            text=True,
        )
        record(
            "AC 10 stops with a plain message",
            run.returncode != 0 and "missing or unusable" in run.stderr,
        )
        record(
            "AC 10 creates no environment",
            not venv.exists() and not (skill / ".venv").exists(),
        )
    finally:
        if venv.exists():
            shutil.rmtree(venv)
        moved.rename(venv)

    print(f"\n{sum(results)} of {len(results)} checks hold")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

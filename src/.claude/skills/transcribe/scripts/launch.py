#!/usr/bin/env python3
"""Launcher for the transcribe skill.

Runs under the brain's own standalone interpreter (``.claude/.python``), never a
global one. On first use it creates the skill's ``.venv`` with the brain's own
``uv``, installs faster-whisper into it, and -- only when an NVIDIA GPU is
present -- the CUDA 12 runtime wheels. Then it hands the command line to
``transcribe.py`` running inside that venv.

Nothing here freezes an absolute path. Every location is derived from this
file's own position, and the venv's ``pyvenv.cfg`` is re-pointed at the
interpreter running *now* on every launch, so renaming the brain folder after
first use does not strand the venv.

Usage: python launch.py <input_path> [output_dir]
Environment: TRANSCRIBE_DEVICE=cpu forces the CPU path and skips CUDA wheels.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CLAUDE = SKILL.parent.parent
VENV = SKILL / ".venv"
IS_WIN = sys.platform == "win32"

BASE_REQ = SKILL / "requirements.txt"
CUDA_REQ = SKILL / "requirements-cuda.txt"
BASE_MARK = VENV / ".transcribe-base"
CUDA_MARK = VENV / ".transcribe-cuda"


def say(msg: str) -> None:
    print(f"[transcribe] {msg}", flush=True)


def fail(msg: str, code: int = 2) -> "None":
    print(f"[transcribe] ERROR: {msg}", file=sys.stderr, flush=True)
    raise SystemExit(code)


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if IS_WIN else "bin/python")


def find_uv() -> Path:
    uv = CLAUDE / ("uv.exe" if IS_WIN else "uv")
    if not uv.exists():
        fail(
            f"the brain's uv was not found at {uv}. Run /init-brain first; "
            "it installs uv and a standalone Python into .claude/."
        )
    return uv


def uv_env() -> dict[str, str]:
    env = dict(os.environ)
    env["UV_PYTHON_INSTALL_DIR"] = str(CLAUDE / ".python")
    env["UV_NO_MODIFY_PATH"] = "1"
    env.pop("VIRTUAL_ENV", None)
    return env


def run_uv(*args: str) -> None:
    # --no-cache keeps wheels out of the user-profile cache: nothing outside the brain.
    cmd = [str(find_uv()), *args]
    result = subprocess.run(cmd, env=uv_env())
    if result.returncode != 0:
        fail(f"uv failed ({result.returncode}): {' '.join(args[:3])}")


def repoint_venv() -> None:
    """Make an existing venv's ``home`` the interpreter running now."""
    cfg = VENV / "pyvenv.cfg"
    if not cfg.exists():
        return
    home = str(Path(sys.executable).parent)
    text = cfg.read_text(encoding="utf-8")
    new = re.sub(r"(?m)^home\s*=.*$", lambda _: f"home = {home}", text)
    if new != text:
        cfg.write_text(new, encoding="utf-8")


def ensure_venv() -> None:
    if venv_python().exists():
        repoint_venv()
        return
    say("first use: creating this skill's own Python environment (.venv)...")
    if VENV.exists():
        shutil.rmtree(VENV)
    run_uv(
        "venv",
        "--no-cache",
        "--no-python-downloads",
        "--python",
        sys.executable,
        str(VENV),
    )
    repoint_venv()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(req: Path, mark: Path, label: str) -> None:
    want = digest(req)
    if mark.exists() and mark.read_text(encoding="utf-8").strip() == want:
        return
    say(f"installing {label} (first use only; this can take a few minutes)...")
    run_uv(
        "pip",
        "install",
        "--no-cache",
        "--link-mode",
        "copy",
        "--python",
        str(venv_python()),
        "-r",
        str(req),
    )
    mark.write_text(want, encoding="utf-8")


def has_nvidia_gpu() -> bool:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return False
    try:
        return (
            subprocess.run([exe, "-L"], capture_output=True, timeout=20).returncode == 0
        )
    except (OSError, subprocess.SubprocessError):
        return False


def choose_device() -> str:
    forced = os.environ.get("TRANSCRIBE_DEVICE", "").strip().lower()
    if forced == "cpu":
        say("TRANSCRIBE_DEVICE=cpu: CPU path, no CUDA wheels.")
        return "cpu"
    if not has_nvidia_gpu():
        say("no NVIDIA GPU found (nvidia-smi absent): CPU path.")
        return "cpu"
    try:
        install(CUDA_REQ, CUDA_MARK, "the CUDA 12 runtime (cuBLAS + cuDNN)")
    except SystemExit:
        say("CUDA runtime install failed; falling back to the CPU path.")
        return "cpu"
    return "cuda"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    ensure_venv()
    install(BASE_REQ, BASE_MARK, "faster-whisper")
    device = choose_device()

    env = dict(os.environ)
    env["TRANSCRIBE_DEVICE"] = device
    env["PYTHONUTF8"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    cmd = [str(venv_python()), str(SKILL / "scripts" / "transcribe.py"), *sys.argv[1:]]
    return subprocess.run(cmd, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Launcher for the transcribe skill.

Runs under the brain's own standalone interpreter (``.claude/.python``), never a
global one. It installs faster-whisper into the brain's one environment,
``.claude/.venv`` -- the venv synaptra runs in -- with the brain's own ``uv``,
and, only when an NVIDIA GPU is present, the CUDA 12 runtime wheels. Then it
hands the command line to ``transcribe.py`` running inside that venv.

The venv belongs to the brain, not to this skill: it is never created, repaired
or re-pointed here. If it is missing or unusable the launcher says so and stops.
A marker file inside the venv records what was installed, so a rebuilt venv
(an update, a move repair) has no marker and the next run installs again.

Every install is guarded. The package set is snapshotted first; if synaptra no
longer imports at its prior version afterwards, the snapshot is restored.

Usage: python launch.py <input_path> [output_dir]
Environment: TRANSCRIBE_DEVICE=cpu forces the CPU path and skips CUDA wheels.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CLAUDE = SKILL.parent.parent
VENV = CLAUDE / ".venv"
IS_WIN = sys.platform == "win32"

sys.path.insert(0, str(CLAUDE / "shared"))

BASE_REQ = SKILL / "requirements.txt"
CUDA_REQ = SKILL / "requirements-cuda.txt"
BASE_MARK = VENV / ".transcribe-base"
CUDA_MARK = VENV / ".transcribe-cuda"
SNAPSHOT = VENV / ".transcribe-snapshot.txt"

PROBE_SYNAPTRA = "import synaptra; print(synaptra.__version__)"
# The server module pulls in mcp, pydantic and the rest of synaptra's stack, so
# this fails when an install breaks a dependency even if `import synaptra` alone
# would still pass.
PROBE_SYNAPTRA_STACK = "import synaptra, synaptra.server; print(synaptra.__version__)"
PROBE_WHISPER = "import faster_whisper"


class Conflict(Exception):
    """An install disturbed synaptra and was rolled back."""


def say(msg: str) -> None:
    print(f"[transcribe] {msg}", flush=True)


def fail(msg: str, code: int = 2) -> "None":
    print(f"[transcribe] ERROR: {msg}", file=sys.stderr, flush=True)
    raise SystemExit(code)


def venv_python() -> Path:
    return platform_paths.venv_python(VENV)


def probe(code: str) -> str | None:
    """Run *code* in the brain's venv; its stdout, or None if it fails."""
    py = venv_python()
    if not py.exists():
        return None
    try:
        out = subprocess.run(
            [str(py), "-c", code], capture_output=True, text=True, timeout=120
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def find_uv() -> Path:
    uv = platform_paths.uv_path(CLAUDE)
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


def run_uv(*args: str, capture: bool = False) -> subprocess.CompletedProcess:
    # --no-cache keeps wheels out of the user-profile cache: nothing outside the brain.
    return subprocess.run(
        [str(find_uv()), *args], env=uv_env(), capture_output=capture, text=True
    )


def require_brain_venv() -> str:
    """The synaptra version the venv has now; stop if the venv cannot be used."""
    version = probe(PROBE_SYNAPTRA)
    if version is None:
        fail(
            "the brain's Python environment (.claude/.venv) is missing or unusable, "
            "so synaptra cannot be imported there. Restart the brain "
            "(a moved brain repairs it on /session-start) or run /init-brain, "
            "then try again. This skill does not create an environment of its own."
        )
    return version


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_current(req: Path, mark: Path) -> bool:
    return mark.exists() and mark.read_text(encoding="utf-8").strip() == digest(req)


def restore_snapshot(label: str) -> None:
    result = run_uv(
        "pip", "sync", "--no-cache", "--python", str(venv_python()), str(SNAPSHOT)
    )
    if result.returncode != 0:
        fail(
            f"installing {label} broke the brain's environment AND restoring it "
            f"failed. The package list from before is in {SNAPSHOT}; restore it "
            "with `uv pip sync`, or run /init-brain."
        )


def install(req: Path, mark: Path, label: str, prior: str) -> None:
    """Install *req* into the brain's venv; undo it if synaptra is disturbed."""
    snap = run_uv("pip", "freeze", "--python", str(venv_python()), capture=True)
    if snap.returncode != 0:
        fail(f"could not snapshot the brain's environment: {snap.stderr.strip()}")
    SNAPSHOT.write_text(snap.stdout, encoding="utf-8")

    say(f"installing {label} into the brain's environment (first use only)...")
    result = run_uv(
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
    after = probe(PROBE_SYNAPTRA_STACK)
    if result.returncode != 0 or after != prior:
        why = (
            f"the install failed (uv exit {result.returncode})"
            if result.returncode != 0
            else f"synaptra went from {prior} to {after or 'unimportable'}"
        )
        say(f"{why}; restoring the brain's environment to how it was.")
        restore_snapshot(label)
        restored = probe(PROBE_SYNAPTRA_STACK)
        if restored != prior:
            fail(
                f"restore finished but synaptra reports {restored}, not {prior}; "
                "run /init-brain."
            )
        raise Conflict(
            f"{label} conflicts with the brain's synaptra environment: {why}. "
            f"The environment is back to its previous state (synaptra {prior}) and "
            "nothing was kept."
        )
    SNAPSHOT.unlink(missing_ok=True)
    mark.write_text(digest(req), encoding="utf-8")


def ensure_base(prior: str) -> None:
    if is_current(BASE_REQ, BASE_MARK) and probe(PROBE_WHISPER) is not None:
        return
    try:
        install(BASE_REQ, BASE_MARK, "faster-whisper", prior)
    except Conflict as exc:
        fail(str(exc))


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


def choose_device(prior: str) -> str:
    forced = os.environ.get("TRANSCRIBE_DEVICE", "").strip().lower()
    if forced == "cpu":
        say("TRANSCRIBE_DEVICE=cpu: CPU path, no CUDA wheels.")
        return "cpu"
    if not has_nvidia_gpu():
        say("no NVIDIA GPU found (nvidia-smi absent): CPU path.")
        return "cpu"
    if is_current(CUDA_REQ, CUDA_MARK):
        return "cuda"
    try:
        install(CUDA_REQ, CUDA_MARK, "the CUDA 12 runtime (cuBLAS + cuDNN)", prior)
    except Conflict as exc:
        say(f"{exc} Falling back to the CPU path.")
        return "cpu"
    return "cuda"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    prior = require_brain_venv()
    ensure_base(prior)
    device = choose_device(prior)

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

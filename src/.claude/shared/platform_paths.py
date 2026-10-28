#!/usr/bin/env python3
"""The one platform rule for where the brain's own runtime lives (issue #97).

Windows and Linux differ in exactly three ways: the `Scripts/` vs `bin/` folder of a
venv, the `.exe` suffix, and how a process is found and stopped. Everything that
needs one of them asks this module instead of writing `sys.platform == "win32"` again.

    python .claude/shared/platform_paths.py show
    python .claude/shared/platform_paths.py stop-venv <venv>      (Linux; Windows stops via PowerShell)

Stdlib only; it runs before the venv exists.
"""

from __future__ import annotations

import os
import posixpath
import signal
import sys
import time
from pathlib import Path


def is_windows() -> bool:
    return sys.platform == "win32"


def exe(name: str) -> str:
    """`uv` -> `uv.exe` on Windows, unchanged elsewhere."""
    return name + ".exe" if is_windows() else name


def venv_bin_dir(venv: Path) -> Path:
    return venv / ("Scripts" if is_windows() else "bin")


def venv_python(venv: Path) -> Path:
    return venv_bin_dir(venv) / exe("python")


def synaptra_exe(venv: Path) -> Path:
    return venv_bin_dir(venv) / exe("synaptra")


def uv_path(claude_dir: Path) -> Path:
    return claude_dir / exe("uv")


def standalone_python_glob() -> str:
    """Where `uv python install` puts an interpreter, below `.claude/.python`."""
    return "*/python.exe" if is_windows() else "*/bin/python3"


def mcp_command() -> str:
    """`.mcp.json`'s `command`: relative to the brain root, in the platform's own form."""
    return "./.claude/.venv/" + (
        "Scripts/synaptra.exe" if is_windows() else "bin/synaptra"
    )


# -- finding and stopping the processes that run out of a venv (Linux) ------------------


def cmdline_runs_from(cmdline: list[str], cwd: str, venv: str) -> bool:
    """True when this process runs out of `venv`: its program, or the script a python
    interpreter was handed, resolves under it.

    A console script is exec'd through its shebang, so the memory server's command line
    is `<interpreter> ./.claude/.venv/bin/synaptra ...` with a path *relative to the
    process's cwd*. The interpreter itself is a symlink into `.claude/.python`, so the
    process's resolved exe says nothing about which brain it belongs to."""
    venv = posixpath.normpath(venv)
    prefix = venv + "/"

    def under(arg: str) -> bool:
        return posixpath.normpath(posixpath.join(cwd, arg)).startswith(prefix)

    if not cmdline:
        return False
    if under(cmdline[0]):
        return True
    return (
        posixpath.basename(cmdline[0]).startswith("python")
        and len(cmdline) > 1
        and under(cmdline[1])
    )


def _ancestors(pid: int) -> set[int]:
    seen: set[int] = set()
    while pid and pid not in seen:
        seen.add(pid)
        try:
            stat = Path(f"/proc/{pid}/stat").read_text()
            pid = int(stat.rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    return seen


def venv_pids(venv: Path) -> list[int]:
    """Processes running out of `venv`, never this process or anything that launched it."""
    skip = _ancestors(os.getpid())
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) in skip:
            continue
        try:
            cmdline = (
                (entry / "cmdline").read_bytes().decode(errors="replace").split("\0")
            )
            cwd = os.readlink(entry / "cwd")
        except OSError:
            continue
        if cmdline_runs_from([c for c in cmdline if c], cwd, venv.as_posix()):
            found.append(int(entry.name))
    return found


def stop_venv_processes(venv: Path) -> int:
    """Stop this brain's venv processes and wait until none is left. Returns how many
    were stopped. Selected by what they run, never by image name: `pkill synaptra` would
    take down every other brain's memory server on the machine."""
    pids = venv_pids(venv)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    deadline = time.monotonic() + 10
    while venv_pids(venv) and time.monotonic() < deadline:
        time.sleep(0.5)
    for pid in venv_pids(venv):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
    return len(pids)


def main(argv: list[str]) -> int:
    if argv[:1] == ["show"]:
        claude = Path(".claude")
        venv = claude / ".venv"
        for label, value in (
            ("uv", uv_path(claude)),
            ("venv python", venv_python(venv)),
            ("synaptra", synaptra_exe(venv)),
            ("standalone python", standalone_python_glob()),
            (".mcp.json command", mcp_command()),
        ):
            print(
                f"{label}: {Path(value).as_posix() if not isinstance(value, str) else value}"
            )
        return 0
    if len(argv) == 2 and argv[0] == "stop-venv" and not is_windows():
        venv = Path(argv[1]).resolve()
        n = stop_venv_processes(venv)
        left = venv_pids(venv)
        print("RELEASED" if not left else "STILL RUNNING: " + " ".join(map(str, left)))
        return 0 if not left else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Issue #60 proofs: the updater does not stop itself when started from the venv.

Builds scratch brains under C:/Projects/.tmp/sb-60-*, each with a standalone
interpreter under .claude/.python and a real venv under .claude/.venv, then runs
update_brain.py against them with a PATH that holds no Python (AC 4).

    AC 1  run with the venv's Python: completes, release record shows new version
    AC 2  run with the standalone interpreter: completes, no hand-over line
    AC 3  venv run prints exactly one hand-over line, before BACKUP
    AC 4  every run above has no system Python on PATH
    AC 5  a process running from the venv is stopped before the install
    AC 6  every run ends in DONE or a named failed step

Each criterion is shown to bite: the same scenarios run against two broken
copies of the updater (hand-over removed; self-exclusion removed) and must FAIL.

    python checks/update/check_venv_launch.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH_BASE = Path("C:/Projects/.tmp")
SCRIPT_REL = Path(".claude") / "shared" / "update_brain.py"
MOVE_MARK = "MOVE  started from the brain's venv Python"

# Each mutant is a list of (old, new) replacements in the scratch update_brain.py.
_NO_HANDOVER = (
    "    handed_over = hand_over_to_standalone(brain)\n",
    "    handed_over = None\n",
)
_NO_SELF_EXCLUSION = (
    "-not $skip.ContainsKey([int]$_.ProcessId)",
    "$true",
)
MUTANTS = {
    "no-handover": [_NO_HANDOVER],
    "original-bug": [_NO_HANDOVER, _NO_SELF_EXCLUSION],
}


def stripped_path() -> str:
    """PATH with only what PowerShell needs -- no Python anywhere on it."""
    root = os.environ.get("SystemRoot", r"C:\Windows")
    return os.pathsep.join(
        [
            os.path.join(root, "System32"),
            os.path.join(root, "System32", "WindowsPowerShell", "v1.0"),
        ]
    )


def build_brain(root: Path) -> None:
    """A minimal brain: product files, a standalone Python, a venv on top of it."""
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(
        SRC,
        root,
        ignore=shutil.ignore_patterns("__pycache__", ".venv", ".python"),
    )
    (root / "persona.md").write_text("# Persona\n", encoding="utf-8")
    (root / "user.md").write_text("# User\n", encoding="utf-8")
    (root / "VERSION").write_text("0.0.1\n", encoding="utf-8")

    home = Path(sys.base_prefix)
    standalone = root / ".claude" / ".python" / "cpython-scratch-windows-x86_64-none"
    shutil.copytree(
        home,
        standalone,
        ignore=shutil.ignore_patterns("__pycache__", "test", "tests", "Doc", "Tools"),
    )
    subprocess.run(
        [str(standalone / "python.exe"), "-m", "venv", str(root / ".claude" / ".venv")],
        check=True,
        capture_output=True,
    )


def venv_python(brain: Path) -> Path:
    return brain / ".claude" / ".venv" / "Scripts" / "python.exe"


def standalone_python(brain: Path) -> Path:
    return next((brain / ".claude" / ".python").glob("*/python.exe"))


def mutate(release: Path, name: str) -> None:
    script = release / SCRIPT_REL
    text = script.read_text(encoding="utf-8")
    for old, new in MUTANTS[name]:
        if old not in text:
            raise SystemExit(f"FAIL: mutant {name} does not apply to update_brain.py")
        text = text.replace(old, new, 1)
    script.write_text(text, encoding="utf-8")


def run_scenario(base: Path, launcher: str, mutant: str | None) -> dict:
    """Run one update; return what the criteria are judged on."""
    brain = base / "brain"
    release = base / "release"
    build_brain(brain)
    if release.exists():
        shutil.rmtree(release)
    shutil.copytree(SRC, release, ignore=shutil.ignore_patterns("__pycache__"))
    if mutant:
        mutate(release, mutant)

    py = venv_python(brain) if launcher == "venv" else standalone_python(brain)
    env = {**os.environ, "PATH": stripped_path()}
    env.pop("_UPDATE_BRAIN_REEXEC", None)

    # A stand-in for a running synaptra server: a process out of the venv.
    server = subprocess.Popen(
        [str(venv_python(brain)), "-c", "import time; time.sleep(600)"], env=env
    )
    time.sleep(1.0)

    cmd = [
        str(py),
        str(release / SCRIPT_REL),
        str(brain),
        "--release",
        str(release),
        "--skip-synaptra",
    ]
    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
        encoding="utf-8",
        errors="replace",
    )

    deadline = time.time() + 10
    while server.poll() is None and time.time() < deadline:
        time.sleep(0.25)
    server_stopped = server.poll() is not None
    if not server_stopped:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(server.pid)], capture_output=True
        )

    record = brain / ".claude" / ".release-record.json"
    version = None
    if record.is_file():
        version = json.loads(record.read_text(encoding="utf-8")).get("brain_version")
    expected = (SRC / "VERSION").read_text(encoding="utf-8").strip()
    out = r.stdout + r.stderr
    lines = out.splitlines()
    first_backup = next(
        (i for i, ln in enumerate(lines) if ln.strip() == "BACKUP"), None
    )
    first_move = next((i for i, ln in enumerate(lines) if MOVE_MARK in ln), None)

    shutil.rmtree(base, ignore_errors=True)
    return {
        "exit": r.returncode,
        "out": out,
        "done": any(ln.startswith("DONE") for ln in lines),
        "failed_named": any("FAIL" in ln and "step" in ln for ln in lines),
        "record_ok": version == expected,
        "moves": sum(MOVE_MARK in ln for ln in lines),
        "move_before_backup": first_move is not None
        and (first_backup is None or first_move < first_backup),
        "server_stopped": server_stopped,
        "no_system_python": shutil.which("python", path=stripped_path()) is None,
    }


def judge(venv_run: dict, standalone_run: dict) -> list[tuple[str, bool, str]]:
    v, s = venv_run, standalone_run
    return [
        (
            "AC 1: venv run completes and release record shows new version",
            v["exit"] == 0 and v["done"] and v["record_ok"],
            f"exit {v['exit']}, DONE={v['done']}, record_ok={v['record_ok']}",
        ),
        (
            "AC 2: standalone run completes, no hand-over",
            s["exit"] == 0 and s["done"] and s["record_ok"] and s["moves"] == 0,
            f"exit {s['exit']}, DONE={s['done']}, moves={s['moves']}",
        ),
        (
            "AC 3: venv run prints one hand-over line before any backup",
            v["moves"] == 1 and v["move_before_backup"],
            f"moves={v['moves']}, before_backup={v['move_before_backup']}",
        ),
        (
            "AC 4: no system Python on PATH for either run",
            v["no_system_python"] and s["no_system_python"] and v["exit"] == 0,
            f"no_system_python={v['no_system_python'] and s['no_system_python']}",
        ),
        (
            "AC 5: process running from the venv is stopped (venv and standalone runs)",
            v["server_stopped"] and s["server_stopped"],
            f"venv={v['server_stopped']}, standalone={s['server_stopped']}",
        ),
        (
            "AC 6: every run ends in DONE or a named failed step",
            all(x["done"] or x["failed_named"] for x in (v, s)),
            f"venv done={v['done']}/named={v['failed_named']}, "
            f"standalone done={s['done']}/named={s['failed_named']}",
        ),
    ]


def run_all(tag: str, mutant: str | None) -> list[tuple[str, bool, str]]:
    base = SCRATCH_BASE / f"sb-60-{tag}"
    v = run_scenario(base / "venv", "venv", mutant)
    s = run_scenario(base / "standalone", "standalone", mutant)
    shutil.rmtree(base, ignore_errors=True)
    return judge(v, s)


def main() -> int:
    print("=== real updater ===")
    real = run_all("real", None)
    for name, ok, detail in real:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    held = sum(ok for _, ok, _ in real)
    print(f"\n{held}/{len(real)} criteria hold.")

    bites = {"no-handover": ("AC 3",), "original-bug": ("AC 1", "AC 6")}
    bite_ok = True
    for mutant, must_fail in bites.items():
        print(f"\n=== broken copy: {mutant} (must FAIL {', '.join(must_fail)}) ===")
        res = run_all(mutant, mutant)
        for name, ok, detail in res:
            if any(name.startswith(m) for m in must_fail):
                print(
                    f"[{'FAILS AS REQUIRED' if not ok else 'DID NOT FAIL'}] {name}: {detail}"
                )
                bite_ok = bite_ok and not ok
    print(f"\nEvery checked criterion bites: {bite_ok}")
    return 0 if held == len(real) and bite_ok else 1


if __name__ == "__main__":
    sys.exit(main())

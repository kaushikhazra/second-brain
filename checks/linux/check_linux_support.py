#!/usr/bin/env python3
"""Issue #97 proofs: the brain runs on Linux and nothing changes on Windows.

There is no Linux box here, so every criterion is shown on this machine: the platform rule is
exercised for both platforms by switching `is_windows`, the shell launchers are run for real
under `sh` against a fake `claude`, and the Linux process-matching rule is run on command lines
taken from how a console script is actually exec'd.

    AC 1  Windows: the platform rule returns exactly the paths the product used before
    AC 2  Linux: bin/ not Scripts/, no .exe anywhere, the .mcp.json command points at bin/synaptra
    AC 3  /init-brain's platform table agrees with the platform rule on both platforms
    AC 4  brain.sh: checks claude is on PATH, sets MCP_TIMEOUT, starts in its own folder,
          forwards arguments, puts the brain's venv first so `python` is the brain's
    AC 5  the launchers are sh scripts with LF endings and the executable bit in git
    AC 6  process matching finds the memory server of THIS brain (relative console-script path)
          and not another brain's, a sibling folder's, or an unrelated program
    AC 7  update_brain stops processes through the rule on Linux and through PowerShell on Windows
    AC 8  no script outside platform_paths.py hardcodes the Scripts/ or .exe layout
    AC 9  the guard hook launcher finds the Linux interpreter layout

Each criterion is shown to bite: the same scenarios run on copies of the files with one
behaviour removed, and the named criteria must FAIL.

    python checks/linux/check_linux_support.py
"""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH_BASE = Path("C:/Projects/.tmp")
PLATFORM = SRC / ".claude" / "shared" / "platform_paths.py"
UPDATE = SRC / ".claude" / "shared" / "update_brain.py"
BRAIN_SH = SRC / "brain.sh"
INIT_SKILL = SRC / ".claude" / "skills" / "init-brain" / "SKILL.md"
RUN_GUARD = SRC / ".claude" / "hooks" / "run_guard.sh"
LAUNCHERS = [
    "brain.sh",
    "brain-claude-sandbox.sh",
    ".claude/skills/transcribe/scripts/transcribe.sh",
]

# One behaviour removed per mutant: (file, old, new, criteria that must fail).
MUTANTS = {
    "Linux still uses Scripts/": (
        PLATFORM,
        '("Scripts" if is_windows() else "bin")',
        '"Scripts"',
        ("AC 2",),
    ),
    "Linux keeps the .exe suffix": (
        PLATFORM,
        'return name + ".exe" if is_windows() else name',
        'return name + ".exe"',
        ("AC 2",),
    ),
    "Windows loses the .exe suffix": (
        PLATFORM,
        'return name + ".exe" if is_windows() else name',
        "return name",
        ("AC 1",),
    ),
    "a sibling folder counts as this venv": (
        PLATFORM,
        'prefix = venv + "/"',
        "prefix = venv",
        ("AC 6",),
    ),
    "relative script paths are not resolved": (
        PLATFORM,
        "posixpath.normpath(posixpath.join(cwd, arg)).startswith(prefix)",
        "posixpath.normpath(arg).startswith(prefix)",
        ("AC 6",),
    ),
    "any program mentioning the venv matches": (
        PLATFORM,
        '    return (\n        posixpath.basename(cmdline[0]).startswith("python")\n        and len(cmdline) > 1\n        and under(cmdline[1])\n    )',
        "    return any(under(c) for c in cmdline)",
        ("AC 6",),
    ),
    "brain.sh forgets the MCP timeout": (
        BRAIN_SH,
        "MCP_TIMEOUT=300000",
        "MCP_TIMEOUT=1",
        ("AC 4",),
    ),
    "brain.sh does not enter its own folder": (
        BRAIN_SH,
        'cd "$(dirname "$0")" || exit 1',
        "true",
        ("AC 4",),
    ),
    "brain.sh skips the claude check": (
        BRAIN_SH,
        "if ! command -v claude",
        "if false && ! command -v claude",
        ("AC 4",),
    ),
    "update_brain stops nothing on Linux": (
        UPDATE,
        "stopped = platform_paths.stop_venv_processes(venv.resolve())",
        "stopped = 0",
        ("AC 7",),
    ),
    "update_brain hardcodes Scripts again": (
        UPDATE,
        'venv_python = platform_paths.venv_python(claude_dir / ".venv")\n\n    result = subprocess.run(\n        [str(venv_python), "-c"',
        'venv_python = claude_dir / ".venv" / "Scripts" / "python.exe"\n\n    result = subprocess.run(\n        [str(venv_python), "-c"',
        ("AC 8",),
    ),
    "the init-brain table drifts from the rule": (
        INIT_SKILL,
        "`./.claude/.venv/bin/synaptra`",
        "`./.claude/.venv/bin/synaptra.exe`",
        ("AC 3",),
    ),
    "run_guard.sh loses the Linux layout": (
        RUN_GUARD,
        '    "$claude/.venv/bin/python" \\\n',
        "",
        ("AC 9",),
    ),
}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def on(mod, windows: bool):
    mod.is_windows = lambda: windows
    return mod


def posix(p) -> str:
    return Path(p).as_posix() if not isinstance(p, str) else p


def sh_run(
    script: Path, args: list[str], cwd: Path, env: dict
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["sh", script.as_posix(), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def make_fake_claude(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    fake = bin_dir / "claude"
    fake.write_text(
        "#!/bin/sh\n"
        'echo "ARGS:$*"\n'
        'echo "PWD:$(pwd)"\n'
        'echo "MCP:$MCP_TIMEOUT"\n'
        'echo "PATH0:${PATH%%:*}"\n',
        encoding="utf-8",
        newline="",
    )
    fake.chmod(0o755)


def scenarios(
    plat_py: Path,
    brain_sh: Path,
    update_py: Path,
    init_text: str,
    guard_sh: Path,
    base: Path,
) -> dict[str, tuple[bool, str]]:
    r: dict[str, tuple[bool, str]] = {}
    plat = load(plat_py, "platform_paths_under_test")
    claude, venv = Path("CLAUDE"), Path("CLAUDE/.venv")

    # AC 1 -- Windows unchanged: the exact literals the product used before this issue.
    on(plat, True)
    win = {
        "uv": posix(plat.uv_path(claude)),
        "python": posix(plat.venv_python(venv)),
        "synaptra": posix(plat.synaptra_exe(venv)),
        "glob": plat.standalone_python_glob(),
        "mcp": plat.mcp_command(),
    }
    win_want = {
        "uv": "CLAUDE/uv.exe",
        "python": "CLAUDE/.venv/Scripts/python.exe",
        "synaptra": "CLAUDE/.venv/Scripts/synaptra.exe",
        "glob": "*/python.exe",
        "mcp": "./.claude/.venv/Scripts/synaptra.exe",
    }
    r["AC 1"] = (win == win_want, f"windows rule: {win}")

    # AC 2 -- Linux.
    on(plat, False)
    lin = {
        "uv": posix(plat.uv_path(claude)),
        "python": posix(plat.venv_python(venv)),
        "synaptra": posix(plat.synaptra_exe(venv)),
        "glob": plat.standalone_python_glob(),
        "mcp": plat.mcp_command(),
    }
    lin_want = {
        "uv": "CLAUDE/uv",
        "python": "CLAUDE/.venv/bin/python",
        "synaptra": "CLAUDE/.venv/bin/synaptra",
        "glob": "*/bin/python3",
        "mcp": "./.claude/.venv/bin/synaptra",
    }
    r["AC 2"] = (
        lin == lin_want
        and not any(".exe" in v or "Scripts" in v for v in lin.values()),
        f"linux rule: {lin}",
    )

    # AC 3 -- the skill's table says what the rule says.
    rows = {
        m.group(1): (m.group(2), m.group(3))
        for m in re.finditer(
            r"^\| `?([^|`]+?)`?(?: `command`)? \| `?([^|]+?)`? \| `?([^|]+?)`? \|$",
            init_text,
            re.M,
        )
    }

    def cell(label: str, col: int) -> str:
        return rows.get(label, ("", ""))[col].strip("`")

    table_ok = (
        cell("UV", 0) == "CLAUDE_DIR/uv.exe"
        and cell("UV", 1) == "CLAUDE_DIR/uv"
        and cell("VENV_PY", 0) == "CLAUDE_DIR/.venv/Scripts/python.exe"
        and cell("VENV_PY", 1) == "CLAUDE_DIR/.venv/bin/python"
        and cell("SYNAPTRA", 0) == "CLAUDE_DIR/.venv/Scripts/synaptra.exe"
        and cell("SYNAPTRA", 1) == "CLAUDE_DIR/.venv/bin/synaptra"
        and cell(".mcp.json", 0) == win_want["mcp"]
        and cell(".mcp.json", 1) == lin_want["mcp"]
        and cell("LAUNCHER", 0) == "brain.bat"
        and cell("LAUNCHER", 1) == "./brain.sh"
    )
    r["AC 3"] = (table_ok, f"table rows read: {sorted(rows)}")

    # AC 4 -- brain.sh, run for real against a fake claude.
    work = base / "ac4"
    if work.exists():
        shutil.rmtree(work)
    brain = work / "my brain"  # a space, because folders get named by people
    brain.mkdir(parents=True)
    shutil.copy(brain_sh, brain / "brain.sh")
    fakebin = work / "fakebin"
    make_fake_claude(fakebin)
    bare = work / "emptybin"
    bare.mkdir()
    env = dict(
        os.environ, PATH=os.pathsep.join([fakebin.as_posix(), os.environ["PATH"]])
    )
    env.pop("MCP_TIMEOUT", None)

    plain = sh_run(brain / "brain.sh", ["--one", "two words"], work, env)
    out = dict(l.split(":", 1) for l in plain.stdout.splitlines() if ":" in l)
    in_own_folder = (
        out.get("PWD", "").replace("\\", "/").rstrip("/").endswith("my brain")
    )
    no_venv_first = not out.get("PATH0", "").endswith(".claude/.venv/bin")

    (brain / ".claude" / ".venv" / "bin").mkdir(parents=True)
    withvenv = sh_run(brain / "brain.sh", [], work, env)
    out2 = dict(l.split(":", 1) for l in withvenv.stdout.splitlines() if ":" in l)
    venv_first = (
        out2.get("PATH0", "").replace("\\", "/").endswith("my brain/.claude/.venv/bin")
    )

    noclaude_env = dict(
        env,
        PATH=bare.as_posix() + os.pathsep + os.environ.get("SystemRoot", "") + "/bin",
    )
    shutil.copy(brain_sh, brain / "brain2.sh")
    missing = subprocess.run(
        [
            "sh",
            "-c",
            f'PATH="{bare.as_posix()}:/usr/bin:/bin"; export PATH; sh "{(brain / "brain2.sh").as_posix()}"',
        ],
        cwd=work,
        env=noclaude_env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    # /usr/bin may hold a real claude on this machine; only judge the message when it was absent.
    absent_msg_ok = (
        "Claude Code was not found on PATH" in missing.stdout
        and missing.returncode == 1
        if shutil.which("claude", path="/usr/bin") is None
        and "claude" not in (missing.stdout + "x")
        else True
    )
    r["AC 4"] = (
        plain.returncode == 0
        and out.get("ARGS") == "--one two words"
        and out.get("MCP") == "300000"
        and in_own_folder
        and no_venv_first
        and venv_first
        and absent_msg_ok,
        f"args={out.get('ARGS')!r} mcp={out.get('MCP')!r} cwd_ok={in_own_folder} "
        f"venv_first_only_when_present={venv_first and no_venv_first} missing_claude_ok={absent_msg_ok}",
    )

    # AC 6 -- which processes belong to this brain.
    venv_s = "/home/pi/brains/one/.claude/.venv"
    cases = {
        # exec'd through the console script's shebang: interpreter, then the script as launched
        "relative console script": (
            [
                "/home/pi/brains/one/.claude/.python/cpython-3.12/bin/python3.12",
                "./.claude/.venv/bin/synaptra",
                "--transport",
                "stdio",
            ],
            "/home/pi/brains/one",
            True,
        ),
        "absolute venv python": ([venv_s + "/bin/python", "-m", "synaptra"], "/", True),
        "another brain, same relative path": (
            [
                "/home/pi/brains/one/.claude/.python/cpython-3.12/bin/python3.12",
                "./.claude/.venv/bin/synaptra",
            ],
            "/home/pi/brains/two",
            False,
        ),
        "sibling folder with the same prefix": (
            ["/home/pi/brains/one/.claude/.venv2/bin/python"],
            "/",
            False,
        ),
        "editor with the venv path as an argument": (
            ["vim", venv_s + "/pyvenv.cfg"],
            "/",
            False,
        ),
        "empty command line": ([], "/", False),
    }
    plat2 = load(plat_py, "platform_paths_under_test_2")
    got = {
        k: plat2.cmdline_runs_from(cl, cwd, venv_s) for k, (cl, cwd, _) in cases.items()
    }
    wrong = [k for k, (_, _, want) in cases.items() if got[k] != want]
    r["AC 6"] = (not wrong, f"misjudged: {wrong}")

    # AC 7 -- update_brain's stop, per platform.
    upd = load(update_py, "update_brain_under_test")
    fake_brain = base / "ac7" / "brain"
    (fake_brain / ".claude" / ".venv").mkdir(parents=True, exist_ok=True)
    calls: list[str] = []
    saved_run = upd.subprocess.run

    class Done:
        stdout = "2\n"
        returncode = 0

    upd.platform_paths.stop_venv_processes = lambda v: (calls.append("linux-stop"), 3)[
        1
    ]
    upd.subprocess.run = lambda cmd, **kw: (calls.append(cmd[0]), Done())[1]
    upd.time.sleep = lambda s: None
    try:
        upd.platform_paths.is_windows = lambda: False
        linux_stopped = upd.stop_synaptra(fake_brain)
        linux_calls = list(calls)
        calls.clear()
        upd.platform_paths.is_windows = lambda: True
        win_stopped = upd.stop_synaptra(fake_brain)
        win_calls = list(calls)
    finally:
        upd.subprocess.run = saved_run
    r["AC 7"] = (
        linux_stopped
        and linux_calls == ["linux-stop"]
        and win_stopped
        and win_calls == ["powershell"],
        f"linux calls={linux_calls} windows calls={win_calls}",
    )

    # AC 8 -- one platform rule: no other script spells out the layout.
    offenders = []
    for py in (SRC / ".claude").rglob("*.py"):
        if py.name == "platform_paths.py":
            continue
        text = update_py.read_text("utf-8") if py == UPDATE else py.read_text("utf-8")
        if re.search(
            r"""["']Scripts["']|["']uv\.exe["']|ext = ["']\.exe["']""",
            text,
        ):
            offenders.append(py.name)
    r["AC 8"] = (not offenders, f"scripts that spell the layout out: {offenders}")

    # AC 9 -- the guard hook launcher against a Linux-shaped brain.
    g = base / "ac9" / ".claude"
    if g.parent.exists():
        shutil.rmtree(g.parent)
    (g / "hooks").mkdir(parents=True)
    (g / ".venv" / "bin").mkdir(parents=True)
    shutil.copy(guard_sh, g / "hooks" / "run_guard.sh")
    py = g / ".venv" / "bin" / "python"
    py.write_text('#!/bin/sh\necho "RAN $*"\n', encoding="utf-8", newline="")
    py.chmod(0o755)
    ran = subprocess.run(
        ["sh", (g / "hooks" / "run_guard.sh").as_posix(), "command_guard.py"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    r["AC 9"] = (
        ran.returncode == 0
        and "RAN" in ran.stdout
        and "command_guard.py" in ran.stdout,
        f"rc={ran.returncode} out={ran.stdout.strip()!r} err={ran.stderr.strip()[:80]!r}",
    )
    return r


def static_checks() -> dict[str, tuple[bool, str]]:
    """AC 5: facts about the shipped files, which no mutant of a single file changes."""
    bad = []
    for rel in LAUNCHERS:
        p = SRC / rel
        data = p.read_bytes()
        if not data.startswith(b"#!/bin/sh\n"):
            bad.append(f"{rel}: no sh shebang")
        if b"\r" in data:
            bad.append(f"{rel}: CRLF")
        if subprocess.run(["sh", "-n", p.as_posix()], capture_output=True).returncode:
            bad.append(f"{rel}: sh -n fails")
        mode = subprocess.run(
            ["git", "-C", str(REPO), "ls-files", "-s", f"src/{rel}"],
            capture_output=True,
            text=True,
        ).stdout.split()
        if not mode or mode[0] != "100755":
            bad.append(f"{rel}: git mode {mode[:1]} not 100755")
    attrs = (REPO / ".gitattributes").read_text("utf-8")
    if "*.sh text eol=lf" not in attrs:
        bad.append(".gitattributes: *.sh not pinned to LF")
    return {
        "AC 5": (
            not bad,
            "; ".join(bad) or f"{len(LAUNCHERS)} launchers: sh, LF, 100755",
        )
    }


def run_all(
    plat_py, brain_sh, update_py, init_skill, guard_sh, base
) -> dict[str, tuple[bool, str]]:
    return scenarios(
        plat_py, brain_sh, update_py, init_skill.read_text("utf-8"), guard_sh, base
    )


def main() -> int:
    SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    base = SCRATCH_BASE / "sb-97-check"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir()
    if shutil.which("sh") is None:
        print("FAIL  sh not found on PATH; the launcher checks need it")
        return 1

    failed = 0
    print("== shipped files ==")
    real = {
        **run_all(PLATFORM, BRAIN_SH, UPDATE, INIT_SKILL, RUN_GUARD, base / "real"),
        **static_checks(),
    }
    for ac in sorted(real):
        ok, note = real[ac]
        print(f"  {'PASS' if ok else 'FAIL'}  {ac}  {note}")
        failed += not ok

    print("== each criterion bites ==")
    for i, (name, (target, old, new, must_fail)) in enumerate(MUTANTS.items()):
        text = target.read_text("utf-8")
        if old not in text:
            print(f"  FAIL  mutant '{name}': text to remove not found in {target.name}")
            failed += 1
            continue
        mdir = base / f"m{i}"
        mdir.mkdir()
        files = {
            PLATFORM: PLATFORM,
            BRAIN_SH: BRAIN_SH,
            UPDATE: UPDATE,
            INIT_SKILL: INIT_SKILL,
            RUN_GUARD: RUN_GUARD,
        }
        mutant = mdir / target.name
        mutant.write_text(text.replace(old, new, 1), encoding="utf-8", newline="")
        files[target] = mutant
        # update_brain imports platform_paths from beside itself, so a copy needs its sibling.
        if target == UPDATE:
            shutil.copy(PLATFORM, mdir / "platform_paths.py")
        got = run_all(
            files[PLATFORM],
            files[BRAIN_SH],
            files[UPDATE],
            files[INIT_SKILL],
            files[RUN_GUARD],
            base / f"m{i}run",
        )
        for ac in must_fail:
            bit = not got[ac][0]
            print(f"  {'PASS' if bit else 'FAIL'}  '{name}' makes {ac} fail")
            failed += not bit

    shutil.rmtree(base, ignore_errors=True)
    print("\nOK" if not failed else f"\n{failed} check(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Issue #106: the update removes the PyTorch synaptra no longer needs, safely.

Real scratch venvs, real uv, hand-built wheels (torch, sentence-transformers, ...),
so "import torch fails afterwards" is observed, not assumed.  Every safety check is
also run against a deliberately broken copy of venv_cleanup.py and must FAIL there,
so a check that cannot fail is caught.

    python checks/update/check_torch_cleanup.py

Needs uv: on PATH, or in a parent folder's .claude/ (a brain).  Without it the
check says so and exits 2 -- it never reports a pass it did not earn.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import types
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SHARED = REPO / "src" / ".claude" / "shared"
sys.path.insert(0, str(SHARED))
import platform_paths  # noqa: E402
import venv_cleanup  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


# -- finding uv -----------------------------------------------------------


def find_uv() -> Path | None:
    found = shutil.which("uv")
    if found:
        return Path(found)
    exe = platform_paths.exe("uv")
    for parent in REPO.parents:
        candidate = parent / ".claude" / exe
        if candidate.is_file():
            return candidate
    return None


# -- hand-built wheels ----------------------------------------------------


def make_wheel(
    out: Path, name: str, version: str, requires: tuple[str, ...] = ()
) -> None:
    mod = name.replace("-", "_")
    dist = f"{mod}-{version}.dist-info"
    files = {
        f"{mod}/__init__.py": f'__version__ = "{version}"\n',
        f"{dist}/METADATA": "Metadata-Version: 2.1\n"
        f"Name: {name}\nVersion: {version}\n"
        + "".join(f"Requires-Dist: {r}\n" for r in requires),
        f"{dist}/WHEEL": "Wheel-Version: 1.0\nGenerator: check\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        f"{dist}/top_level.txt": f"{mod}\n",
    }
    files[f"{dist}/RECORD"] = "".join(f"{p},,\n" for p in [*files, f"{dist}/RECORD"])
    with zipfile.ZipFile(out / f"{mod}-{version}-py3-none-any.whl", "w") as z:
        for path, text in files.items():
            z.writestr(path, text)


def make_packaging_wheel(out: Path) -> None:
    """A wheel of the host's own `packaging`, so scratch venvs can evaluate markers.

    Every real brain venv that holds torch has packaging (transformers needs it).
    """
    import packaging

    root = Path(packaging.__file__).resolve().parent
    version = packaging.__version__
    dist = f"packaging-{version}.dist-info"
    files = {
        f"packaging/{p.relative_to(root).as_posix()}": p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    files[f"{dist}/METADATA"] = (
        f"Metadata-Version: 2.1\nName: packaging\nVersion: {version}\n".encode()
    )
    files[f"{dist}/WHEEL"] = (
        b"Wheel-Version: 1.0\nGenerator: check\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    )
    files[f"{dist}/top_level.txt"] = b"packaging\n"
    files[f"{dist}/RECORD"] = "".join(
        f"{p},,\n" for p in [*files, f"{dist}/RECORD"]
    ).encode()
    with zipfile.ZipFile(out / f"packaging-{version}-py3-none-any.whl", "w") as z:
        for path, data in files.items():
            z.writestr(path, data)


def build_wheels(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    make_packaging_wheel(out)
    make_wheel(out, "torch", "2.5.0")
    make_wheel(out, "sentence-transformers", "3.0.0", ("torch",))
    make_wheel(out, "other-tool", "1.0.0", ("torch",))
    make_wheel(out, "synaptra", "2.1.1", ("sentence-transformers",))
    make_wheel(out, "synaptra", "3.1.0")
    # #109: huggingface-hub names torch only behind an extra, as the real one does
    make_wheel(
        out,
        "huggingface-hub",
        "0.30.0",
        (
            "packaging",
            'torch; extra == "torch"',
            'safetensors[torch]; extra == "torch"',
        ),
    )
    make_wheel(out, "safetensors", "0.5.0", ('torch; extra == "torch"',))
    make_wheel(out, "wants-hf-torch", "1.0.0", ("huggingface-hub[torch]",))
    make_wheel(out, "old-python-only", "1.0.0", ('torch; python_version < "3"',))
    make_wheel(out, "new-python-only", "1.0.0", ('torch; python_version >= "3"',))


# -- scratch brains -------------------------------------------------------


class Env:
    def __init__(self, root: Path, uv: Path):
        self.root, self.uv = root, uv
        self.wheels = root / "wheels"
        build_wheels(self.wheels)
        self.count = 0

    def brain(self, *installs: list[str]) -> Path:
        """A scratch brain with a real venv; each *installs* entry is one uv install."""
        self.count += 1
        brain = self.root / f"brain{self.count}"
        claude = brain / ".claude"
        claude.mkdir(parents=True)
        shutil.copy(self.uv, claude / platform_paths.exe("uv"))
        venv = claude / ".venv"
        run([str(self.uv), "venv", str(venv), "--python", sys.executable])
        py = platform_paths.venv_python(venv)
        for specs in (["packaging"], *installs):
            run(
                [
                    str(self.uv),
                    "pip",
                    "install",
                    "--python",
                    str(py),
                    "--no-index",
                    "--find-links",
                    str(self.wheels),
                    *specs,
                ]
            )
        return brain

    def py(self, brain: Path) -> Path:
        return platform_paths.venv_python(brain / ".claude" / ".venv")


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])}...: {r.stderr.strip()[-300:]}")
    return r


def imports(env: Env, brain: Path, module: str) -> bool:
    r = subprocess.run(
        [str(env.py(brain)), "-c", f"import {module}"], capture_output=True, text=True
    )
    return r.returncode == 0


def synaptra_version(env: Env, brain: Path) -> str:
    r = subprocess.run(
        [str(env.py(brain)), "-c", "import synaptra; print(synaptra.__version__)"],
        capture_output=True,
        text=True,
    )
    return r.stdout.strip()


def load_variant(old: str, new: str) -> types.ModuleType:
    path = SHARED / "venv_cleanup.py"
    src = path.read_text(encoding="utf-8")
    if old not in src:
        raise AssertionError(f"mutation anchor not found: {old!r}")
    mod = types.ModuleType("venv_cleanup_variant")
    mod.__file__ = str(path)
    exec(compile(src.replace(old, new, 1), str(path), "exec"), mod.__dict__)
    return mod


# -- scenarios (each returns facts; the checks read the facts) --------------


def scenario_removal(env: Env, mod) -> dict:
    """Old synaptra pulled torch in; update to 3.1.0 left it behind."""
    brain = env.brain(["synaptra==2.1.1"], ["synaptra==3.1.0"])
    (brain / "projects" / "clone").mkdir(parents=True)
    (brain / "projects" / "clone" / "a.py").write_text(
        "import torch\n"
    )  # not the brain's code
    before = {m: imports(env, brain, m) for m in ("torch", "sentence_transformers")}
    lines = mod.cleanup(brain, "1.10.0")
    log_path = brain / ".claude" / ".cleanup-log.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else []
    again = mod.cleanup(brain, "1.10.0")
    log_after = json.loads(log_path.read_text()) if log_path.exists() else []
    facts = {
        "before": before,
        "lines": lines,
        "torch": imports(env, brain, "torch"),
        "st": imports(env, brain, "sentence_transformers"),
        "synaptra": synaptra_version(env, brain),
        "log": log,
        "again": again,
        "log_after": log_after,
        "brain": brain,
    }
    return facts


def scenario_dependent(env: Env, mod) -> dict:
    brain = env.brain(["synaptra==3.1.0", "sentence-transformers", "other-tool"])
    lines = mod.cleanup(brain, "1.10.0")
    return {
        "lines": lines,
        "torch": imports(env, brain, "torch"),
        "log": (brain / ".claude" / ".cleanup-log.json").exists(),
    }


def scenario_marker(env: Env, mod, *extra_installs: str) -> dict:
    """An old synaptra left torch behind; *extra_installs* are added on top (#109)."""
    brain = env.brain(["synaptra==2.1.1"], ["synaptra==3.1.0", *extra_installs])
    lines = mod.cleanup(brain, "1.10.1")
    return {"lines": lines, "torch": imports(env, brain, "torch")}


def scenario_imports(env: Env, mod) -> dict:
    brain = env.brain(["synaptra==2.1.1"], ["synaptra==3.1.0"])
    code = brain / ".claude" / "skills" / "mine"
    code.mkdir(parents=True)
    (code / "use.py").write_text("import torch\n")
    lines = mod.cleanup(brain, "1.10.0")
    return {
        "lines": lines,
        "torch": imports(env, brain, "torch"),
        "file": str(code / "use.py"),
        "log": (brain / ".claude" / ".cleanup-log.json").exists(),
    }


def scenario_failure(env: Env, mod) -> dict:
    brain = env.brain(["synaptra==2.1.1"], ["synaptra==3.1.0"])
    (brain / ".claude" / platform_paths.exe("uv")).unlink()  # removal cannot run
    try:
        lines, raised = mod.cleanup(brain, "1.10.0"), None
    except Exception as exc:  # noqa: BLE001
        lines, raised = None, exc
    return {"lines": lines, "raised": raised, "torch": imports(env, brain, "torch")}


# -- the checks -----------------------------------------------------------


def main() -> int:
    uv = find_uv()
    if uv is None:
        print(
            "SKIP: uv not found (PATH or a parent .claude/); cannot run the real-venv checks"
        )
        return 2

    scratch = REPO / ".tmp"  # the repo's own throwaway folder, never the system temp
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="torch-cleanup-", dir=scratch) as tmp:
        env = Env(Path(tmp), uv)

        # AC 1, 2, 6, 7, 8 -- the removal itself, its log, its silence the second time
        f = scenario_removal(env, venv_cleanup)
        record(
            "setup: torch and sentence-transformers present before the update",
            all(f["before"].values()),
            str(f["before"]),
        )
        record("AC 1  torch is gone: import torch fails in the venv", not f["torch"])
        record("AC 2  sentence-transformers goes with it", not f["st"])
        record(
            "AC 2  synaptra still imports at the pinned version",
            f["synaptra"] == "3.1.0",
            f["synaptra"],
        )
        names = sorted(p["package"] for e in f["log"] for p in e["removed"])
        record(
            "AC 6  the removal is logged with package, version, time, release",
            names == ["sentence-transformers", "torch"]
            and all(
                e["time"]
                and e["release"] == "1.10.0"
                and all(p["version"] for p in e["removed"])
                for e in f["log"]
            ),
            str(f["log"]),
        )
        record(
            "AC 7  a second update removes nothing, says nothing, logs nothing",
            f["again"] == [] and f["log_after"] == f["log"],
            f"{f['again']}",
        )
        text = " ".join(f["lines"])
        record(
            "AC 8  the owner is told what was removed, in words",
            "torch 2.5.0" in text and "sentence-transformers 3.0.0" in text,
            text[:200],
        )
        restore = next(
            (l for l in f["lines"] if l.startswith("To put them back: ")), ""
        )
        cmd = restore.removeprefix("To put them back: ")
        env_cmd = cmd.replace(
            "pip install", f'pip install --no-index --find-links "{env.wheels}"', 1
        )
        r = subprocess.run(env_cmd, shell=True, capture_output=True, text=True)
        record(
            "AC 8  the command it gives puts torch back",
            r.returncode == 0 and imports(env, f["brain"], "torch"),
            (r.stderr or "")[-200:],
        )

        # AC 3, 9 -- a dependent outside the set stops it
        d = scenario_dependent(env, venv_cleanup)
        record(
            "AC 3  a package that requires torch keeps it: torch still imports",
            d["torch"],
        )
        record(
            "AC 3  the update names that package",
            any("other-tool" in l for l in d["lines"]),
            str(d["lines"]),
        )
        record(
            "AC 9  one line, naming the reason", len(d["lines"]) == 1, str(d["lines"])
        )
        record("AC 3  nothing is logged when nothing is removed", not d["log"])

        # #109 -- markers are evaluated; an extra counts only when it is installed
        h = scenario_marker(env, venv_cleanup, "huggingface-hub", "safetensors")
        record(
            "#109 AC 1  huggingface-hub installed plainly does not keep torch",
            not h["torch"],
            str(h["lines"]),
        )
        h = scenario_marker(env, venv_cleanup, "wants-hf-torch")
        record(
            "#109 AC 1  an extra that IS installed (huggingface-hub[torch]) keeps torch",
            h["torch"] and any("huggingface-hub" in l for l in h["lines"]),
            str(h["lines"]),
        )
        h = scenario_marker(env, venv_cleanup, "old-python-only")
        record(
            "#109 AC 2  a python_version marker that is false here does not keep torch",
            not h["torch"],
            str(h["lines"]),
        )
        h = scenario_marker(env, venv_cleanup, "new-python-only")
        record(
            "#109 AC 2  a python_version marker that is true here keeps torch",
            h["torch"] and any("new-python-only" in l for l in h["lines"]),
            str(h["lines"]),
        )
        h = scenario_marker(env, venv_cleanup, "other-tool", "huggingface-hub")
        record(
            "#109 AC 3  a real dependent (other-tool) still keeps torch, hub present",
            h["torch"] and any("other-tool" in l for l in h["lines"]),
            str(h["lines"]),
        )

        # AC 4, 9 -- the brain's own code stops it
        i = scenario_imports(env, venv_cleanup)
        record(
            "AC 4  code that imports torch keeps it: torch still imports", i["torch"]
        )
        record(
            "AC 4  the update names the file",
            any(i["file"] in l for l in i["lines"]),
            str(i["lines"]),
        )
        record(
            "AC 9  one line, naming the reason", len(i["lines"]) == 1, str(i["lines"])
        )
        record("AC 4  nothing is logged when nothing is removed", not i["log"])

        # AC 5 -- a failure is a message, not an exception, and not a rollback trigger
        x = scenario_failure(env, venv_cleanup)
        record(
            "AC 5  a removal that cannot run does not raise",
            x["raised"] is None,
            str(x["raised"]),
        )
        record(
            "AC 5  it says the cleanup was skipped and that the update is complete",
            bool(x["lines"])
            and "skipped" in x["lines"][0]
            and "update itself is complete" in x["lines"][0],
            str(x["lines"]),
        )
        src = (SHARED / "update_brain.py").read_text(encoding="utf-8")
        last_except = src.rfind("rolled back to prior state")
        call = src.find("venv_cleanup.cleanup(")
        record(
            "AC 5  run_update calls the cleanup after the rollback-guarded steps",
            call != -1 and call > last_except,
            f"call@{call} after last rollback@{last_except}",
        )

        # Each safety check must FAIL against a copy with that behaviour removed
        m3 = load_variant("        if needs:\n", "        if False:\n")
        got = scenario_dependent(env, m3)
        record(
            "mutation: without the dependents check AC 3 fails (torch is removed)",
            not got["torch"],
        )

        m9 = load_variant(
            "    if req.marker is None:\n        return True\n",
            "    return True\n",
        )
        got = scenario_marker(env, m9, "huggingface-hub", "safetensors")
        record(
            "mutation: without marker evaluation #109 fails (torch is kept)",
            got["torch"],
        )

        m4 = load_variant(
            "    if imports:\n        path, module",
            "    if False:\n        path, module",
        )
        got = scenario_imports(env, m4)
        record(
            "mutation: without the import scan AC 4 fails (torch is removed)",
            not got["torch"],
        )

        m6 = load_variant("write_log(brain, release, to_remove)", "pass")
        got = scenario_removal(env, m6)
        record(
            "mutation: without the log AC 6 fails (nothing is logged)", got["log"] == []
        )

        m5 = load_variant(
            "except Exception as exc:  # AC 5",
            "except ZeroDivisionError as exc:  # AC 5",
        )
        got = scenario_failure(env, m5)
        record(
            "mutation: without the catch-all AC 5 fails (it raises)",
            got["raised"] is not None,
        )

    for name, ok, detail in RESULTS:
        print(
            f"[{'PASS' if ok else 'FAIL'}] {name}"
            + (f"  -- {detail}" if not ok and detail else "")
        )
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"\n#106: {passed}/{len(RESULTS)} checks pass.")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())

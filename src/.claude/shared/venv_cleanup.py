#!/usr/bin/env python3
"""Remove PyTorch from a brain's venv once nothing needs it (issue #106).

synaptra 3.1.0 embeds with fastembed (ONNX) and no longer needs torch.  A brain
that was installed on an older synaptra still holds torch and
sentence-transformers.  After an update to a synaptra that does not need them,
this removes them -- but only when that is safe:

  * nothing installed outside the removal set requires them   (AC 3)
  * nothing in the brain's own code imports them              (AC 4)

The removal set is torch and sentence-transformers, the chain old synaptra pulled
in.  Whatever else requires either of them (a synaptra that still does, torchvision,
accelerate, ...) is not ours to judge, so it keeps both.

A failure in here never fails the update (AC 5): the caller gets a result that
says what happened.  Stdlib only; reads the venv through the venv's own python.
"""

from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import platform_paths  # noqa: E402

TARGET = "torch"
# The only package besides torch that old synaptra pulled in for torch's sake.  Anything
# else that requires torch (torchvision, accelerate, ...) is someone's own and blocks.
OLD_SYNAPTRA_CHAIN = frozenset({"sentence-transformers"})
LOG = ".claude/.cleanup-log.json"

# Folders whose .py files are not "the brain's own code".
_SKIP_DIRS = frozenset(
    {
        ".venv",
        ".python",
        ".git",
        "synaptra-data",
        "dream-backups",
        ".update-backup",
        "__pycache__",
        "projects",  # managed project clones are other people's code, not the brain's
        "models",
    }
)

# Runs inside the brain's venv python: one JSON object of what is installed.
_DUMP = r"""
import json, importlib.metadata as m
out = {}
for d in m.distributions():
    name = d.metadata["Name"]
    if not name:
        continue
    tops = (d.read_text("top_level.txt") or "").split()
    if not tops:
        seen = set()
        for f in d.files or []:
            p = f.parts[0] if f.parts else ""
            if p and not p.endswith((".dist-info", ".data", "__pycache__")):
                seen.add(p[:-3] if p.endswith(".py") else p)
        tops = sorted(seen)
    out[name] = {
        "version": d.version,
        "requires": list(d.requires or []),
        "modules": tops,
    }
print(json.dumps(out))
"""

_REQ_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def norm(name: str) -> str:
    """PEP 503 normalised name."""
    return re.sub(r"[-_.]+", "-", name).lower()


def req_name(requirement: str) -> str | None:
    m = _REQ_NAME.match(requirement)
    return norm(m.group(1)) if m else None


# -- reading ------------------------------------------------------------


def read_installed(venv_python: Path) -> dict[str, dict]:
    """What the venv holds: normalised name -> version, requires, modules, requested."""
    result = subprocess.run(
        [str(venv_python), "-I", "-c", _DUMP],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"could not list the venv's packages: {result.stderr.strip()}"
        )
    raw = json.loads(result.stdout)
    installed = {}
    for name, info in raw.items():
        installed[norm(name)] = {
            "name": name,
            "version": info["version"],
            "requires": [r for r in (req_name(x) for x in info["requires"]) if r],
            "modules": info["modules"],
        }
    return installed


def brain_python_files(brain: Path):
    """The brain's own .py files, skipping the venv, store, backups and clones."""
    stack = [brain]
    while stack:
        folder = stack.pop()
        try:
            entries = list(folder.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name not in _SKIP_DIRS:
                    stack.append(entry)
            elif entry.suffix == ".py":
                yield entry


def find_imports(brain: Path, modules: set[str]) -> list[tuple[Path, str]]:
    """Files of the brain's own code that import one of *modules*."""
    if not modules:
        return []
    alt = "|".join(re.escape(m) for m in sorted(modules))
    pattern = re.compile(rf"^\s*(?:import|from)\s+({alt})\b", re.MULTILINE)
    hits = []
    for path in brain_python_files(brain):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = pattern.search(text)
        if m:
            hits.append((path, m.group(1)))
    return hits


# -- deciding -----------------------------------------------------------


def removal_set(installed: dict[str, dict]) -> set[str]:
    """torch plus every installed package that, directly or not, requires it."""
    if TARGET not in installed:
        return set()
    return {TARGET} | (OLD_SYNAPTRA_CHAIN & set(installed))


def plan(installed: dict[str, dict], imports: list[tuple[Path, str]] | None = None):
    """Decide.  Returns (to_remove, reason): reason is None when removing is safe.

    *imports* are the (file, module) hits already found for the removal set;
    pass None to skip the import check (the caller scans after it knows the set).
    """
    rset = removal_set(installed)
    if not rset:
        return [], None  # nothing to do, nothing to say

    for name in sorted(installed):
        if name in rset:
            continue
        needs = sorted(r for r in installed[name]["requires"] if r in rset)
        if needs:
            return [], f"{installed[name]['name']} requires {needs[0]}"
    if imports:
        path, module = imports[0]
        return [], f"{path} imports {module}"
    return [(installed[n]["name"], installed[n]["version"]) for n in sorted(rset)], None


# -- doing --------------------------------------------------------------


def _uv(brain: Path, venv_python: Path, verb: str, specs: list[str]):
    uv = platform_paths.uv_path(brain / ".claude")
    return subprocess.run(
        [str(uv), "pip", verb, "--python", str(venv_python), *specs],
        capture_output=True,
        text=True,
        timeout=600,
    )


def restore_command(brain: Path, removed: list[tuple[str, str]]) -> str:
    claude_dir = brain / ".claude"
    uv = platform_paths.uv_path(claude_dir)
    py = platform_paths.venv_python(claude_dir / ".venv")
    specs = " ".join(f"{n}=={v}" for n, v in removed)
    return f'"{uv}" pip install --python "{py}" {specs}'


def write_log(brain: Path, release: str, removed: list[tuple[str, str]]) -> Path:
    path = brain / LOG
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            entries = []
    except (OSError, ValueError):
        entries = []
    entries.append(
        {
            "time": datetime.datetime.now().astimezone().isoformat(),
            "release": release,
            "removed": [{"package": n, "version": v} for n, v in removed],
        }
    )
    path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    return path


def cleanup(brain: Path, release: str) -> list[str]:
    """Run the whole cleanup.  Never raises; returns the lines to tell the owner."""
    try:
        claude_dir = brain / ".claude"
        venv_python = platform_paths.venv_python(claude_dir / ".venv")
        installed = read_installed(venv_python)
        rset = removal_set(installed)
        if not rset:
            return []  # AC 7: nothing to remove, nothing said, nothing logged

        modules = {m for n in rset for m in installed[n]["modules"]}
        modules.add(TARGET)
        to_remove, reason = plan(installed, find_imports(brain, modules))
        if reason:
            return [f"PyTorch was left in place: {reason}."]  # AC 9

        result = _uv(brain, venv_python, "uninstall", [n for n, _ in to_remove])
        if result.returncode != 0:
            return [
                "PyTorch cleanup skipped: removing it failed "
                f"({result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'unknown error'}). "
                "The update itself is complete."
            ]

        check = subprocess.run(
            [str(venv_python), "-c", "import synaptra"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        restore = restore_command(brain, to_remove)
        if check.returncode != 0:
            _uv(brain, venv_python, "install", [f"{n}=={v}" for n, v in to_remove])
            return [
                "PyTorch cleanup undone: synaptra stopped importing after the removal, "
                "so the packages were put back. The update itself is complete."
            ]

        write_log(brain, release, to_remove)
        names = ", ".join(f"{n} {v}" for n, v in to_remove)
        return [
            f"Removed from this brain's Python: {names}.",
            "The synaptra now installed does not need them, and nothing else here did.",
            f"To put them back: {restore}",
            f"What was removed is recorded in {LOG}.",
        ]
    except Exception as exc:  # AC 5: never fail the update
        return [f"PyTorch cleanup skipped: {exc}. The update itself is complete."]

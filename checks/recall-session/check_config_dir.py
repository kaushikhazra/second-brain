#!/usr/bin/env python3
"""Issue #83 proofs: /recall-session finds transcripts where Claude Code actually keeps them.

Runs the real search.py against scratch config folders under C:/Projects/.tmp/sb-recall-cfg-*,
with USERPROFILE/HOME pointed at an empty folder so the real home never answers.

    AC 1  CLAUDE_CONFIG_DIR set: a match in <it>/projects/<this brain> is found
    AC 2  CLAUDE_CONFIG_DIR set: transcripts under the home default are not searched
    AC 3  CLAUDE_CONFIG_DIR unset or empty: the home default is searched
    AC 4  CLAUDE_CONFIG_DIR set, nothing there: the message names the folder under it
    AC 5  expand mode (--session) reads from the same place
    AC 6  the skill's text says it honours CLAUDE_CONFIG_DIR

Each criterion is shown to bite: the same scenarios run on copies of search.py / SKILL.md with one
behaviour removed, and the named criteria must FAIL.

    python checks/recall-session/check_config_dir.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH_BASE = Path("C:/Projects/.tmp")
SEARCH = SRC / ".claude" / "skills" / "recall-session" / "tools" / "search.py"
SKILL = SRC / ".claude" / "skills" / "recall-session" / "SKILL.md"

# One behaviour removed per mutant: (file, old, new, criteria that must fail).
MUTANTS = {
    "CLAUDE_CONFIG_DIR ignored": (
        SEARCH,
        'os.environ.get("CLAUDE_CONFIG_DIR")',
        "None",
        ("AC 1", "AC 2", "AC 4", "AC 5"),
    ),
    "an empty CLAUDE_CONFIG_DIR wins": (
        SEARCH,
        "if config_dir else",
        "if config_dir is not None else",
        ("AC 3",),
    ),
    "skill silent about it": (
        SKILL,
        "CLAUDE_CONFIG_DIR",
        "THE_CONFIG_FOLDER",
        ("AC 6",),
    ),
}


def encode_root(root: Path) -> str:
    return re.sub(r"[\\/:.]", "-", str(root))


def write_session(projects: Path, root: Path, sid: str, text: str) -> None:
    d = projects / encode_root(root)
    d.mkdir(parents=True, exist_ok=True)
    rec = {
        "type": "user",
        "timestamp": "2026-10-01T10:00:00.000Z",
        "message": {"role": "user", "content": text},
    }
    (d / f"{sid}.jsonl").write_text(json.dumps(rec) + "\n", encoding="utf-8")


def run(
    search_py: Path, base: Path, root: Path, args: list[str], config_dir: str | None
) -> str:
    home = base / "home"
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
    env["USERPROFILE"] = env["HOME"] = str(home)
    if config_dir is not None:
        env["CLAUDE_CONFIG_DIR"] = config_dir
    r = subprocess.run(
        [sys.executable, str(search_py), *args, "--root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=60,
    )
    return r.stdout + r.stderr


def scenarios(
    search_py: Path, skill_text: str, base: Path
) -> dict[str, tuple[bool, str]]:
    r: dict[str, tuple[bool, str]] = {}
    brain = base / "brain"
    (brain / ".claude").mkdir(parents=True)
    (brain / "CLAUDE.md").write_text("x", encoding="utf-8")
    cfg, home_projects = base / "cfg", base / "home" / ".claude" / "projects"
    write_session(cfg / "projects", brain, "cfgsession", "the CONFIGTOKEN lives here")
    write_session(home_projects, brain, "homesession", "the HOMETOKEN lives here")

    out = run(search_py, base, brain, ["CONFIGTOKEN"], str(cfg))
    r["AC 1"] = (
        "cfgsession" in out,
        f"match found via config dir: {'cfgsession' in out}",
    )

    out = run(search_py, base, brain, ["HOMETOKEN"], str(cfg))
    r["AC 2"] = (
        "homesession" not in out,
        f"home default searched anyway: {'homesession' in out}",
    )

    got = [run(search_py, base, brain, ["HOMETOKEN"], v) for v in (None, "")]
    r["AC 3"] = (
        all("homesession" in g for g in got),
        f"home default used when unset/empty: {['homesession' in g for g in got]}",
    )

    empty_cfg = base / "empty-cfg"
    empty_cfg.mkdir()
    out = run(search_py, base, brain, ["anything"], str(empty_cfg))
    r["AC 4"] = (
        str(empty_cfg) in out or empty_cfg.as_posix() in out,
        next(
            (
                l
                for l in out.splitlines()
                if "empty-cfg" in l or "not found" in l.lower()
            ),
            out[:120],
        ),
    )

    out = run(
        search_py, base, brain, ["--session", "cfgsession", "--slice", "1:1"], str(cfg)
    )
    r["AC 5"] = (
        "CONFIGTOKEN" in out,
        f"expand mode reads the config dir: {'CONFIGTOKEN' in out}",
    )

    r["AC 6"] = (
        "CLAUDE_CONFIG_DIR" in skill_text,
        f"skill names it: {'CLAUDE_CONFIG_DIR' in skill_text}",
    )
    return r


def main() -> int:
    SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    base = SCRATCH_BASE / "sb-recall-cfg-check"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir()

    failed = 0
    print("== shipped files ==")
    (base / "real").mkdir()
    real = scenarios(SEARCH, SKILL.read_text("utf-8"), base / "real")
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
        mutated = mdir / target.name
        mutated.write_text(text.replace(old, new), encoding="utf-8", newline="")
        got = scenarios(
            mutated if target == SEARCH else SEARCH,
            mutated.read_text("utf-8") if target == SKILL else SKILL.read_text("utf-8"),
            mdir,
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

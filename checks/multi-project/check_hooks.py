#!/usr/bin/env python3
"""Issue #45 -- the owner chooses which of a project's hooks the brain adopts.

Script check, no brain and no LLM (build-only mode): it drives
`manage/scripts/projecthooks.py` one process per command in a small brain under
`C:/Projects/.tmp/second-brain-loop-45/` -- the two scripts from `src/`, the
`CLAUDE.md` / `.claude/` marker, a `settings.json` carrying one brain hook, and two git
folders under `projects/` that carry hooks of their own.

AC 5 is proven by firing: the adopted command is read back from the brain's settings,
`$CLAUDE_PROJECT_DIR` is expanded to the *renamed* brain the way Claude Code does at the
moment a hook fires, and the hook is run. What this cannot show is Claude Code itself
firing it in a live session -- that, and the brain applying the skill, are
behaviour-pending.

  python check_hooks.py             run the five criteria against src/
  python check_hooks.py --self-test mutate the script once per behaviour and remove each
                                    wiring rule, requiring the check to fail
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_SCRIPTS = REPO_ROOT / "src" / ".claude" / "skills" / "manage" / "scripts"
SCRATCH = Path("C:/Projects/.tmp/second-brain-loop-45")
SCRIPT_FILES = ("projects.py", "projecthooks.py")

BRAIN_SETTINGS = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "mcp__guard",
                "hooks": [
                    {
                        "type": "command",
                        "command": 'python "$CLAUDE_PROJECT_DIR/.claude/hooks/brain_guard.py"',
                    }
                ],
            }
        ]
    }
}
PROJECT_SETTINGS = {
    "hooks": {
        "SessionStart": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": 'python "$CLAUDE_PROJECT_DIR/.claude/hooks/mark.py"',
                    }
                ]
            }
        ],
        "PreToolUse": [
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": 'python "$CLAUDE_PROJECT_DIR/.claude/hooks/bash_guard.py"',
                        "timeout": 5,
                    }
                ],
            },
            {
                "matcher": "mcp__guard",
                "hooks": [
                    {
                        "type": "command",
                        "command": 'python "$CLAUDE_PROJECT_DIR/.claude/hooks/other_guard.py"',
                    }
                ],
            },
        ],
    }
}
MARK_PY = (
    "import os, pathlib\n"
    "root = pathlib.Path(os.environ['CLAUDE_PROJECT_DIR'])\n"
    "(root / 'fired.log').open('a').write(f'{__file__}\\n')\n"
)


def remove_tree(path: Path) -> None:
    import os
    import stat

    def retry(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onexc=retry)


def build(root: Path, mutate: tuple[str, str, str] | None = None) -> Path:
    if root.exists():
        remove_tree(root)
    scripts = root / ".claude" / "skills" / "manage" / "scripts"
    scripts.mkdir(parents=True)
    (root / "CLAUDE.md").write_text("# scratch brain\n", encoding="utf-8")
    (root / ".claude" / "settings.json").write_text(
        json.dumps(BRAIN_SETTINGS, indent=2), encoding="utf-8"
    )
    for name in SCRIPT_FILES:
        shutil.copyfile(SRC_SCRIPTS / name, scripts / name)
    if mutate:
        name, pattern, repl = mutate
        f = scripts / name
        new, n = re.subn(
            pattern, repl, f.read_text(encoding="utf-8"), count=1, flags=re.S
        )
        if not n:
            raise SystemExit(f"mutation matched nothing in {name}: {pattern!r}")
        f.write_text(new, encoding="utf-8")
    p = root / "projects" / "proj-h"
    (p / ".claude" / "hooks").mkdir(parents=True)
    (p / ".claude" / "settings.json").write_text(
        json.dumps(PROJECT_SETTINGS, indent=2), encoding="utf-8"
    )
    for hook in ("mark.py", "bash_guard.py", "other_guard.py"):
        (p / ".claude" / "hooks" / hook).write_text(MARK_PY, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(p)], check=True)
    return root


class H:
    def __init__(self, root: Path):
        self.root = root
        self.script = (
            root / ".claude" / "skills" / "manage" / "scripts" / "projecthooks.py"
        )
        self.local = root / ".claude" / "settings.local.json"
        self.registry = root / ".claude" / "projects" / "adopted-hooks.json"

    def run(self, *args: str) -> tuple[int, dict[str, list[str]]]:
        p = subprocess.run(
            [sys.executable, "-I", str(self.script), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(self.root),
        )
        out: dict[str, list[str]] = {}
        for line in p.stdout.splitlines():
            k, _, v = line.partition(": ")
            out.setdefault(k, []).append(v)
        return p.returncode, out

    def local_commands(self, event: str) -> list[str]:
        if not self.local.is_file():
            return []
        groups = (
            json.loads(self.local.read_text("utf-8")).get("hooks", {}).get(event, [])
        )
        return [h["command"] for g in groups for h in g.get("hooks", [])]

    def digest(self, f: Path) -> str:
        return hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else "absent"


def scenario(root: Path, res: list[tuple[str, str, bool, str]]) -> None:
    h = H(root)

    def add(ac: str, name: str, ok: bool, detail: str = "") -> None:
        res.append((ac, name, ok, detail))

    brain_settings = root / ".claude" / "settings.json"
    before = (h.digest(brain_settings), h.digest(h.local), h.digest(h.registry))

    # --- AC1: list without adopting ---------------------------------------------
    code, out = h.run("list", "proj-h")
    rows = out.get("HOOK", [])
    add(
        "AC1",
        "the project's three hooks are listed, numbered, none adopted",
        code == 0 and len(rows) == 3 and all(r.endswith("adopted: no") for r in rows),
        f"rows={rows}",
    )
    add(
        "AC1",
        "listing changed nothing: no local settings, no registry, the brain's settings.json untouched",
        (h.digest(brain_settings), h.digest(h.local), h.digest(h.registry)) == before
        and not h.local.exists()
        and not h.registry.exists(),
        f"local={h.local.exists()} registry={h.registry.exists()}",
    )

    # #39's learned record prints the same lines it always did (hook_entries was
    # factored out of hooks_of for this issue)
    listing = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys, pathlib; sys.path.insert(0, sys.argv[1]); import projects; "
            "print('\\n'.join(projects.hooks_of(pathlib.Path(sys.argv[2]))))",
            str(h.script.parent),
            str(root / "projects" / "proj-h"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.splitlines()
    add(
        "AC1",
        "the learned record's hook lines (#39) are unchanged: event | matcher | command | file",
        listing[0]
        == 'SessionStart | * | python "$CLAUDE_PROJECT_DIR/.claude/hooks/mark.py" | .claude/settings.json'
        and len(listing) == 3,
        f"lines={listing}",
    )

    # --- AC2: adopt a named hook, say it applies to every project ---------------
    code, out = h.run("adopt", "proj-h", "1")
    cmds = h.local_commands("SessionStart")
    add(
        "AC2",
        "adopting hook 1 adds it to the brain's settings.local.json",
        code == 0 and out.get("STATUS") == ["ADOPTED"] and len(cmds) == 1,
        f"status={out.get('STATUS')} commands={cmds}",
    )
    add(
        "AC2",
        "it says plainly that the hook now applies to every project in this brain",
        out.get("APPLIES_TO") == ["every project in this brain"],
        f"applies_to={out.get('APPLIES_TO')}",
    )
    add(
        "AC2",
        "its command starts from $CLAUDE_PROJECT_DIR and the project's folder",
        bool(cmds)
        and "$CLAUDE_PROJECT_DIR/projects/proj-h/.claude/hooks/mark.py" in cmds[0],
        f"command={cmds[:1]}",
    )
    code, out = h.run("list", "proj-h")
    add(
        "AC2",
        "the list now shows hook 1 as adopted and the other two as not",
        [r.rsplit("adopted: ", 1)[1] for r in out.get("HOOK", [])]
        == ["yes", "no", "no"],
        f"rows={out.get('HOOK')}",
    )

    # --- AC3: remove an adopted hook --------------------------------------------
    code, out = h.run("adopt", "proj-h", "2")
    bash_id = (out.get("HOOK_ID") or ["?"])[0]
    code_a, adopted = h.run("adopted")
    add(
        "AC3",
        "the owner can see what was adopted",
        code_a == 0 and adopted.get("ADOPTED_COUNT") == ["2"],
        f"adopted={adopted.get('ADOPTED')}",
    )
    first_id = next(
        (a.split(" | ")[0] for a in adopted.get("ADOPTED", []) if "mark.py" in a), "?"
    )
    code, out = h.run("remove", first_id)
    add(
        "AC3",
        "removing an adopted hook takes it out of the brain's settings and leaves the other",
        code == 0
        and out.get("STATUS") == ["REMOVED"]
        and h.local_commands("SessionStart") == []
        and len(h.local_commands("PreToolUse")) == 1,
        f"status={out.get('STATUS')} session={h.local_commands('SessionStart')} pre={h.local_commands('PreToolUse')}",
    )
    code, out = h.run("remove", "999")
    add(
        "AC3",
        "removing something that was never adopted is refused",
        code == 1 and out.get("STATUS") == ["NOT_FOUND"],
        f"status={out.get('STATUS')}",
    )
    code, out = h.run("list", "proj-h")
    add(
        "AC3",
        "a removed hook can be listed as not adopted again",
        [r.rsplit("adopted: ", 1)[1] for r in out.get("HOOK", [])]
        == ["no", "yes", "no"],
        f"rows={out.get('HOOK')}",
    )

    # --- AC4: duplicate or conflict -> reported, not added ----------------------
    snapshot = h.digest(h.local)
    code, out = h.run("adopt", "proj-h", "2")
    add(
        "AC4",
        "adopting a hook already adopted is reported as a duplicate and not added again",
        code == 1
        and out.get("STATUS") == ["DUPLICATE"]
        and out.get("ADDED") == ["nothing"]
        and len(h.local_commands("PreToolUse")) == 1
        and h.digest(h.local) == snapshot,
        f"status={out.get('STATUS')} existing={out.get('EXISTING')}",
    )
    code, out = h.run("adopt", "proj-h", "3")
    add(
        "AC4",
        "a hook on the same event and matcher as the brain's own, with another command, is a conflict and not added",
        code == 1
        and out.get("STATUS") == ["CONFLICT"]
        and out.get("ADDED") == ["nothing"]
        and h.digest(h.local) == snapshot
        and bool(out.get("EXISTING"))
        and "brain_guard.py" in out["EXISTING"][0],
        f"status={out.get('STATUS')} existing={out.get('EXISTING')}",
    )
    code, out = h.run("adopt", "proj-h", "9")
    add(
        "AC4",
        "naming a hook the project does not have is refused",
        code == 1 and out.get("STATUS") == ["NO_SUCH_HOOK"],
        f"status={out.get('STATUS')}",
    )

    # --- AC5: still fires after the brain folder is renamed ---------------------
    h.run("adopt", "proj-h", "1")  # mark.py is the one that writes fired.log
    moved = root.parent / (root.name + "-renamed")
    if moved.exists():
        remove_tree(moved)
    shutil.copytree(root, moved)
    text = (moved / ".claude" / "settings.local.json").read_text("utf-8")
    old_forms = {
        str(root),
        str(root).replace("\\", "/"),
        str(root).replace("\\", "\\\\"),
    }
    add(
        "AC5",
        "the adopted settings carry no absolute path of the brain",
        not any(f in text for f in old_forms),
        f"found={[f for f in old_forms if f in text]}",
    )
    mh = H(moved)
    fired = []
    for cmd in mh.local_commands("SessionStart"):
        # what Claude Code does at the moment a hook fires: expand the variable, run it
        expanded = cmd.replace("$CLAUDE_PROJECT_DIR", str(moved).replace("\\", "/"))
        expanded = re.sub(r"^python ", lambda _m: f'"{sys.executable}" ', expanded)
        env = {**__import__("os").environ, "CLAUDE_PROJECT_DIR": str(moved)}
        r = subprocess.run(
            expanded, shell=True, capture_output=True, text=True, env=env
        )
        fired.append(r.returncode)
    log = moved / "fired.log"
    add(
        "AC5",
        "after the brain is renamed, the adopted hook runs and does its work",
        fired == [0]
        and log.is_file()
        and str(moved).replace("\\", "/") in log.read_text("utf-8").replace("\\", "/"),
        f"exit={fired} log={log.read_text('utf-8') if log.is_file() else None}",
    )
    remove_tree(moved)


MUTATIONS: list[tuple[str, str, str, str]] = [
    (
        "AC1",
        "listing adopts every hook",
        r'(    print\(f"HOOKS: \{len\(entries\)\}"\)\n)    return 0',
        r"\1    for _n in range(1, len(entries) + 1):\n        cmd_adopt(key, str(_n))\n    return 0",
    ),
    (
        "AC2",
        "adopting writes nothing to the brain's settings",
        r"    write_json\(settings_local\(\), settings\)\n    reg = load_registry\(\)",
        "    reg = load_registry()",
    ),
    (
        "AC2",
        "adopting does not say it applies to every project",
        r'    print\(f"APPLIES_TO: \{APPLIES\}"\)\n    return 0\n\n\ndef cmd_adopted',
        "    return 0\n\n\ndef cmd_adopted",
    ),
    (
        "AC3",
        "remove leaves the hook in the brain's settings",
        r"    if removed:\n        write_json\(settings_local\(\), settings\)\n",
        "",
    ),
    (
        "AC4",
        "a duplicate is added again",
        r'        if e\["command"\] == command:',
        "        if False:",
    ),
    (
        "AC4",
        "a conflicting hook is added",
        r"    if same_slot:\n        e = same_slot\[0\]",
        "    if False:\n        e = same_slot[0]",
    ),
    (
        "AC5",
        "the command is written with this machine's absolute path",
        r'base = f"\$CLAUDE_PROJECT_DIR/projects/\{project.name\}"',
        'base = f"{project}".replace("\\\\", "/")',
    ),
]

SKILL = Path(".claude/skills/manage/SKILL.md")
WIRING: list[tuple[str, str, Path, str]] = [
    (
        "AC1",
        "hooks are listed, never adopted by default",
        SKILL,
        r"listed, never adopted by default",
    ),
    ("AC1", "list changes nothing", SKILL, r"`list` changes nothing"),
    (
        "AC2",
        "adopt only a hook the owner names",
        SKILL,
        r"Adopt only a hook the owner \*\*names\*\*",
    ),
    (
        "AC2",
        "say it now applies to every project in this brain",
        SKILL,
        r"now applies to every project in this brain",
    ),
    (
        "AC3",
        "the owner can remove an adopted hook",
        SKILL,
        r"projecthooks\.py remove <id>",
    ),
    (
        "AC4",
        "a duplicate or conflict is reported and nothing is added",
        SKILL,
        r"`STATUS: DUPLICATE` or `STATUS: CONFLICT`.*?\*\*nothing was added\*\*",
    ),
    (
        "AC5",
        "the hook is rooted at $CLAUDE_PROJECT_DIR so a rename does not break it",
        SKILL,
        r"roots the hook's command at\s+`\$CLAUDE_PROJECT_DIR`.*?renamed or moved",
    ),
]


def wiring_eval(root: Path) -> list[bool]:
    texts: dict[Path, str] = {}
    out = []
    for _, _, rel, pattern in WIRING:
        if rel not in texts:
            f = root / rel
            texts[rel] = f.read_text(encoding="utf-8") if f.is_file() else ""
        out.append(bool(re.search(pattern, texts[rel], re.S)))
    return out


def run_scenario(root: Path) -> list[tuple[str, str, bool, str]]:
    res: list[tuple[str, str, bool, str]] = []
    try:
        scenario(root, res)
    except Exception as exc:  # a mutation that breaks the script outright
        res.append(("ALL", f"the script failed outright: {exc!r}", False, ""))
    return res


def run_check() -> int:
    res = run_scenario(build(SCRATCH / "brain"))
    for (ac, name, _, _), ok in zip(WIRING, wiring_eval(REPO_ROOT / "src")):
        res.append((ac, f"wiring: {name}", ok, ""))
    for ac, name, ok, detail in res:
        print(
            f"[{'PASS' if ok else 'FAIL'}] {ac}: {name}"
            + (f" -- {detail}" if not ok else "")
        )
    failed = [r for r in res if not r[2]]
    print(f"\n{len(res) - len(failed)}/{len(res)} script checks pass.")
    return 1 if failed else 0


def self_test() -> int:
    bad = 0
    for idx, (ac, what, pattern, repl) in enumerate(MUTATIONS):
        root = build(SCRATCH / f"mutant-{idx}", ("projecthooks.py", pattern, repl))
        failing = sorted({r[0] for r in run_scenario(root) if not r[2]})
        ok = ac in failing or "ALL" in failing
        print(
            f"[{'PASS' if ok else 'FAIL'}] mutation ({ac}) {what}: check fails for {failing or 'nothing'}"
        )
        bad += 0 if ok else 1
    for idx, (ac, what, rel, pattern) in enumerate(WIRING):
        copy = SCRATCH / f"wiring-{idx}"
        if copy.exists():
            remove_tree(copy)
        for r in {w[2] for w in WIRING}:
            (copy / r).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / "src" / r, copy / r)
        f = copy / rel
        cut, n = re.subn(
            pattern, "", f.read_text(encoding="utf-8"), count=1, flags=re.S
        )
        if not n:
            print(f"[FAIL] wiring removal ({ac}) {what}: rule matches nothing in src/")
            bad += 1
            continue
        f.write_text(cut, encoding="utf-8")
        ok = idx in [i for i, passed in enumerate(wiring_eval(copy)) if not passed]
        print(f"[{'PASS' if ok else 'FAIL'}] wiring removal ({ac}) {what}: check fails")
        bad += 0 if ok else 1
    total = len(MUTATIONS) + len(WIRING)
    print(f"\n{total - bad}/{total} removals noticed.")
    return 1 if bad else 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    return self_test() if args.self_test else run_check()


if __name__ == "__main__":
    sys.exit(main())

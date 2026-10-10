#!/usr/bin/env python3
"""Issue #45, the brain's half -- does a brain handle a project's hooks the way the skill says?

`check_hooks.py` proves the script. This drives a scratch brain built from `src/` through
the owner's door (`claude -p`) with `sb-sandbox-alpha` (it carries one SessionStart hook,
`mark_session.py`) cloned into `projects/`, and reads the brain's settings, the adoption
registry and the reply. Each mode has its own scratch root.

  --mode list     AC 1 -- the owner asks what hooks alpha declares: the brain lists them
                  and adopts nothing
  --mode adopt    AC 2 -- the owner names the hook: it is added, rooted at
                  $CLAUDE_PROJECT_DIR, and the brain says it now applies to every project
  --mode remove   AC 3 -- a hook adopted earlier is removed on request
  --mode dup      AC 4 -- the same hook asked for again: reported as already there, not added
  --mode conflict AC 4 -- the brain already has another SessionStart hook: reported, not added
  --mode live     AC 5 -- the brain folder is renamed after adopting; a real session opened
                  in the renamed folder fires the adopted hook (Claude Code itself)

Usage:  python check_hooks_brain.py --mode adopt      (builds, seeds, runs, verifies)
        python check_hooks_brain.py --mode adopt --verify-only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import scratch_brain as sb

BASE = Path(
    os.environ.get("SB_CHECK_SCRATCH", "C:/Projects/.tmp/second-brain-loop-45b")
)
MODES = ("list", "adopt", "remove", "dup", "conflict", "live")
HOOK_FILE = "mark_session.py"
BRAIN_SESSION_HOOK = {
    "hooks": {
        "SessionStart": [
            {
                "hooks": [
                    {"type": "command", "command": "python -c \"print('brain hook')\""}
                ]
            }
        ]
    }
}


class Ctx:
    def __init__(self, mode: str):
        self.root = BASE / mode
        self.brain = self.root / "brain"
        self.script = self.brain / ".claude/skills/manage/scripts/projecthooks.py"
        self.local = self.brain / ".claude/settings.local.json"
        self.registry = self.brain / ".claude/projects/adopted-hooks.json"
        self.shipped = self.brain / ".claude/settings.json"

    def events(self, tag: str) -> Path:
        return self.root / f"hb-events-{tag}.json"

    def owner(self, prompt: str, tag: str, cwd: Path | None = None) -> None:
        sb.run_owner(prompt, self.events(tag), cwd or self.brain, budget="1.5")

    def script_run(self, *args: str) -> str:
        return subprocess.run(
            [sys.executable, "-I", str(self.script), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(self.brain),
        ).stdout

    def digest(self, f: Path) -> str:
        return hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else "absent"

    def local_commands(self, event: str = "SessionStart") -> list[str]:
        if not self.local.is_file():
            return []
        groups = (
            json.loads(self.local.read_text("utf-8")).get("hooks", {}).get(event, [])
        )
        return [h["command"] for g in groups for h in g.get("hooks", [])]

    def registry_count(self) -> int:
        if not self.registry.is_file():
            return 0
        return len(json.loads(self.registry.read_text("utf-8")).get("items", []))


def setup(c: Ctx) -> None:
    c.root.mkdir(parents=True, exist_ok=True)
    sb.build(c.brain)
    (c.brain / "projects").mkdir(exist_ok=True)
    subprocess.run(
        [
            "git",
            "clone",
            "-q",
            sb.ALPHA_HTTPS,
            str(c.brain / "projects" / "sb-sandbox-alpha"),
        ],
        check=True,
    )


def do_run(mode: str, after_setup=None) -> Ctx:
    """`after_setup(ctx)` lets a removal demo cut the scratch brain before the owner speaks."""
    c = Ctx(mode)
    setup(c)
    if after_setup:
        after_setup(c)
    ask = "Adopt the mark_session hook from sb-sandbox-alpha into this brain."
    if mode == "list":
        (c.root / "digest.json").write_text(
            json.dumps([c.digest(c.shipped), c.digest(c.local), c.digest(c.registry)])
        )
        c.owner(
            "Which hooks does sb-sandbox-alpha declare? I only want to see them for now.",
            "list",
        )
    elif mode == "adopt":
        c.owner(ask, "adopt")
    elif mode == "remove":
        c.script_run("adopt", "sb-sandbox-alpha", "1")
        c.owner("Remove the hook we adopted from sb-sandbox-alpha.", "remove")
    elif mode == "dup":
        c.script_run("adopt", "sb-sandbox-alpha", "1")
        (c.root / "digest.json").write_text(
            json.dumps([c.digest(c.local), c.registry_count()])
        )
        c.owner(ask, "dup")
    elif mode == "conflict":
        c.local.write_text(json.dumps(BRAIN_SESSION_HOOK, indent=2), encoding="utf-8")
        (c.root / "digest.json").write_text(
            json.dumps([c.digest(c.local), c.registry_count()])
        )
        c.owner(ask, "conflict")
    else:  # live
        c.script_run("adopt", "sb-sandbox-alpha", "1")
        renamed = c.root / "brain-renamed"
        if renamed.exists():
            sb.remove_tree(renamed)
        shutil.move(str(c.brain), str(renamed))
        log = renamed / ".tmp" / "alpha-hook-fired.log"
        log.unlink(missing_ok=True)
        # a real session in the renamed folder: Claude Code fires SessionStart itself
        c.owner("Hello.", "live", cwd=renamed)
    return c


def do_verify(mode: str) -> int:
    c = Ctx(mode)
    res: list[tuple[str, bool, str]] = []
    if mode == "list":
        r = sb.final_text(c.events("list"))
        before = json.loads((c.root / "digest.json").read_text("utf-8"))
        after = [c.digest(c.shipped), c.digest(c.local), c.digest(c.registry)]
        res.append(
            (
                "AC1 (brain): lists the project's hooks and adopts nothing",
                sb.has(r"mark_session", r)
                and sb.has(r"SessionStart", r)
                and before == after
                and not c.local.exists()
                and not c.registry.exists(),
                f"names_hook={sb.has('mark_session', r)} unchanged={before == after} "
                f"local_exists={c.local.exists()} registry_exists={c.registry.exists()}",
            )
        )
    elif mode == "adopt":
        r = sb.final_text(c.events("adopt"))
        cmds = c.local_commands()
        rooted = any(
            "$CLAUDE_PROJECT_DIR/projects/sb-sandbox-alpha/.claude/hooks/mark_session.py"
            in x
            for x in cmds
        )
        says = sb.has(r"every project", r) and sb.has(r"appl(?:y|ies)", r)
        res.append(
            (
                "AC2 (brain): adds the named hook, rooted at $CLAUDE_PROJECT_DIR, and says it applies to every project",
                rooted and says and len(cmds) == 1,
                f"commands={cmds} says_every_project={says}",
            )
        )
    elif mode == "remove":
        r = sb.final_text(c.events("remove"))
        res.append(
            (
                "AC3 (brain): removes the adopted hook on request",
                c.local_commands() == []
                and c.registry_count() == 0
                and sb.has(r"remov", r),
                f"commands={c.local_commands()} registry={c.registry_count()} says_removed={sb.has('remov', r)}",
            )
        )
    elif mode == "dup":
        r = sb.final_text(c.events("dup"))
        before = json.loads((c.root / "digest.json").read_text("utf-8"))
        res.append(
            (
                "AC4 (brain): a hook already adopted is reported as already there and not added again",
                c.digest(c.local) == before[0]
                and c.registry_count() == before[1]
                and len(c.local_commands()) == 1
                and sb.has(r"already|duplicate|twice|same hook", r),
                f"commands={len(c.local_commands())} unchanged={c.digest(c.local) == before[0]} "
                f"says_already={sb.has('already|duplicate|twice|same hook', r)}",
            )
        )
    elif mode == "conflict":
        r = sb.final_text(c.events("conflict"))
        before = json.loads((c.root / "digest.json").read_text("utf-8"))
        res.append(
            (
                "AC4 (brain): a hook that conflicts with one the brain has is reported and not added",
                c.digest(c.local) == before[0]
                and c.registry_count() == 0
                and sb.has(r"conflict|already (?:has|have)|existing|clash", r),
                f"unchanged={c.digest(c.local) == before[0]} registry={c.registry_count()} "
                f"says_conflict={sb.has('conflict|already (?:has|have)|existing|clash', r)}",
            )
        )
    else:  # live
        renamed = c.root / "brain-renamed"
        log = renamed / ".tmp" / "alpha-hook-fired.log"
        text = log.read_text("utf-8") if log.is_file() else ""
        res.append(
            (
                "AC5 (live): after the brain folder is renamed, Claude Code fires the adopted hook in a real session",
                log.is_file() and "alpha hook fired" in text,
                f"log_exists={log.is_file()} content={text.strip()[:80]!r}",
            )
        )
    return sb.report(res)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=MODES, required=True)
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args()
    if not a.verify_only:
        do_run(a.mode)
    return do_verify(a.mode)


if __name__ == "__main__":
    sys.exit(main())

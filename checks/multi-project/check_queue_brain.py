#!/usr/bin/env python3
"""Issue #44, the brain's half -- does a brain use the work queue the way the skill says?

`check_queue.py` proves the script. This drives a scratch brain built from `src/` through
the owner's door (`claude -p`, `--resume`) with the sandbox projects already in
`projects/` (cloned by git: the folder is the registry) and the queue seeded by the
script, then reads the queue file and the reply. Each mode has its own scratch root, so
modes can run side by side.

  --mode add   : alpha #1 is running; the owner approves beta #1 -> it waits (AC 1),
                 nothing is started in beta, the owner is told
  --mode view  : the owner asks what is queued -> project, issue, state, order (AC 3)
  --mode edit  : "alpha #2 first", then "drop beta #1" -> the queue file shows both (AC 3)
  --mode next  : the owner stops the running item -> the next one starts (AC 4)
  --mode boot  : a session starts with an item left `active` -> it is reported by project
                 and issue, kept as interrupted, the queue moves on (AC 5)

Usage:  python check_queue_brain.py --mode add      (builds, seeds, runs, verifies)
        python check_queue_brain.py --all
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import scratch_brain as sb

BASE = Path(
    os.environ.get("SB_CHECK_SCRATCH", "C:/Projects/.tmp/second-brain-loop-44b")
)
MODES = ("add", "view", "edit", "next", "boot")


class Ctx:
    def __init__(self, mode: str):
        self.root = BASE / mode
        self.brain = self.root / "brain"
        self.alpha = self.brain / "projects" / "sb-sandbox-alpha"
        self.beta = self.brain / "projects" / "sb-sandbox-beta"
        self.script = self.brain / ".claude/skills/manage/scripts/workqueue.py"
        self.queue = self.brain / ".claude/projects/queue.json"

    def events(self, tag: str) -> Path:
        return self.root / f"qb-events-{tag}.json"

    def owner(self, prompt: str, tag: str, resume: str | None = None) -> None:
        sb.run_owner(prompt, self.events(tag), self.brain, resume=resume, budget="1.5")

    def wq(self, *args: str) -> str:
        return subprocess.run(
            [sys.executable, "-I", str(self.script), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(self.brain),
        ).stdout

    def items(self) -> list[dict]:
        if not self.queue.is_file():
            return []
        return json.loads(self.queue.read_text("utf-8"))["items"]

    def states(self) -> dict[str, str]:
        return {f"{i['project']}#{i['issue']}": i["state"] for i in self.items()}

    def order(self) -> list[str]:
        return [
            f"{i['project']}#{i['issue']}"
            for i in self.items()
            if i["state"] == "queued"
        ]

    def git_state(self, p: Path) -> dict:
        loop = p / ".claude" / "loop"
        return {
            "branches": sb.git(
                "branch", "--format=%(refname:short)", cwd=p
            ).stdout.split(),
            "status": sb.git(
                "status", "--porcelain", "--untracked-files=all", cwd=p
            ).stdout.splitlines(),
            "loop": sorted(str(f) for f in loop.rglob("*")) if loop.exists() else [],
        }


def setup(c: Ctx, seed: list[tuple[str, str, str]]) -> None:
    c.root.mkdir(parents=True, exist_ok=True)
    sb.build(c.brain)
    (c.brain / "projects").mkdir(exist_ok=True)
    for url in (sb.ALPHA_HTTPS, sb.BETA_HTTPS):
        subprocess.run(
            ["git", "clone", "-q", url, str(c.brain / "projects" / Path(url).stem)],
            check=True,
        )
    for project, issue, title in seed:
        c.wq("add", project, issue, "--title", title)


SEEDS = {
    "add": [("sb-sandbox-alpha", "1", "User greets someone in their own language")],
    "view": [
        ("sb-sandbox-alpha", "1", "User greets someone in their own language"),
        ("sb-sandbox-beta", "1", "User deletes a note by its number"),
        ("sb-sandbox-alpha", "2", "User gets a clear error for an empty name"),
    ],
    "next": [
        ("sb-sandbox-alpha", "1", "User greets someone in their own language"),
        ("sb-sandbox-beta", "1", "User deletes a note by its number"),
    ],
}
SEEDS["edit"] = SEEDS["view"]
SEEDS["boot"] = SEEDS["next"]


def do_run(mode: str, after_setup=None) -> Ctx:
    """`after_setup(ctx)` lets a removal demo cut the scratch brain before the owner speaks."""
    c = Ctx(mode)
    setup(c, SEEDS[mode])
    if after_setup:
        after_setup(c)
    if mode == "add":
        (c.root / "snap-beta.json").write_text(
            json.dumps(c.git_state(c.beta)), encoding="utf-8"
        )
        c.owner(
            "I approve sb-sandbox-beta issue #1 (the delete-a-note one). The due diligence is "
            "done; go ahead and start it.",
            "add",
        )
    elif mode == "view":
        c.owner("What is on the work queue right now?", "view")
    elif mode == "edit":
        c.owner(
            "Put sb-sandbox-alpha issue #2 first in the work queue, ahead of beta #1.",
            "edit1",
        )
        c.owner(
            "Now take sb-sandbox-beta issue #1 off the queue altogether.",
            "edit2",
            resume=sb.session_id(c.events("edit1")),
        )
    elif mode == "next":
        c.owner(
            "I'm stopping the sb-sandbox-alpha issue #1 work. Stop it and carry on with whatever "
            "is next on the queue.",
            "next",
        )
    else:  # boot
        # the previous session ended with alpha #1 active -- it is still `active` in the file
        c.owner("Hello.", "boot")
    return c


def do_verify(mode: str) -> int:
    c = Ctx(mode)
    res: list[tuple[str, bool, str]] = []
    if mode == "add":
        r = sb.final_text(c.events("add"))
        s = c.states()
        before = json.loads((c.root / "snap-beta.json").read_text("utf-8"))
        after = c.git_state(c.beta)
        waits = sb.has(
            r"queue|wait|behind|after|position|next in line|once .* (?:finish|done)", r
        )
        res.append(
            (
                "AC1 (brain): approved while another item runs -> it waits, nothing is started",
                s.get("sb-sandbox-beta#1") == "queued"
                and s.get("sb-sandbox-alpha#1") == "active"
                and list(s.values()).count("active") == 1
                and before == after
                and waits,
                f"states={s} beta_unchanged={before == after} reply_says_it_waits={waits}",
            )
        )
    elif mode == "view":
        r = sb.final_text(c.events("view"))
        names = all(sb.has(p, r) for p in (r"alpha", r"beta", r"#?1\b", r"#?2\b"))
        states = sb.has(r"active|running|in progress|now", r) and sb.has(
            r"queued|waiting|next|then", r
        )
        order = r.lower().find("beta") != -1 and r.lower().find(
            "beta"
        ) < r.lower().rfind("alpha")
        res.append(
            (
                "AC3 (brain): the owner sees the queue -- project, issue, state, order",
                names and states and order,
                f"names={names} states={states} beta_before_alpha2={order}",
            )
        )
    elif mode == "edit":
        s = c.states()
        res.append(
            (
                "AC3 (brain): reorder on request, then remove on request",
                s.get("sb-sandbox-beta#1") is None
                and s.get("sb-sandbox-alpha#2") == "queued"
                and s.get("sb-sandbox-alpha#1") == "active",
                f"states={s} queued_order={c.order()}",
            )
        )
        first = [i for i in c.items() if i["state"] == "queued"]
        res.append(
            (
                "AC3 (brain): the reorder happened before the removal (alpha #2 was moved, not just beta dropped)",
                any("move" in json.dumps(e).lower() or True for e in [first])
                and bool(sb.tool_uses(c.events("edit1"), "Bash"))
                and any(
                    "workqueue.py move" in str(t)
                    for t in sb.tool_uses(c.events("edit1"), "Bash")
                ),
                f"edit1_bash={[str(t)[:100] for t in sb.tool_uses(c.events('edit1'), 'Bash')][:4]}",
            )
        )
    elif mode == "next":
        r = sb.final_text(c.events("next"))
        s = c.states()
        beta = next((i for i in c.items() if i["project"] == "sb-sandbox-beta"), {})
        # "started" = it left the queue for the work: active, or already done by the time
        # the turn ended (the brain may well finish a small item inside its budget)
        started = bool(beta.get("started_at")) and beta.get("state") in ("active", "done")
        res.append((
            "AC4 (brain): the running item is stopped and the next one starts",
            s.get("sb-sandbox-alpha#1") == "stopped"
            and started
            and list(s.values()).count("active") <= 1
            and sb.has(r"beta", r),
            f"states={s} beta_started={started} reply_names_beta={sb.has('beta', r)}",
        ))
    else:  # boot
        r = sb.final_text(c.events("boot"))
        s = c.states()
        named = (
            sb.has(r"alpha", r)
            and sb.has(r"#?\s*1\b", r)
            and sb.has(
                r"interrupt|cut off|did not finish|didn't finish|left off|unfinished|ended",
                r,
            )
        )
        res.append(
            (
                "AC5 (brain): at boot the cut-off work is reported by project and issue, kept, and the queue moves on",
                named
                and s.get("sb-sandbox-alpha#1") == "interrupted"
                and s.get("sb-sandbox-beta#1") == "active",
                f"reply_names_it={named} states={s}",
            )
        )
    return sb.report(res)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=MODES)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    a = ap.parse_args()
    modes = MODES if a.all else (a.mode,) if a.mode else ()
    if not modes:
        ap.print_help()
        return 1
    failed = 0
    for m in modes:
        if not a.verify_only:
            do_run(m)
        failed += do_verify(m)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Issue #44 -- the brain queues work across projects, one active at a time.

Script check, no brain and no LLM (build-only mode): it drives the queue script
`manage/scripts/workqueue.py` the way the skill does -- one process per command, state
only in the queue file -- in a small brain built under
`C:/Projects/.tmp/second-brain-loop-44/`. The brain is the two scripts from `src/`, the
`CLAUDE.md` / `.claude/` marker that tells them where the brain is, and two git
folders under `projects/` (the folder is the registry).

This proves the script's behaviour. Whether a brain calls it at the right moments is
the skill's job and is behaviour-pending.

  python check_queue.py             run the five criteria against src/
  python check_queue.py --self-test mutate the script once per behaviour and require
                                    the check to fail for exactly that criterion
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_SCRIPTS = REPO_ROOT / "src" / ".claude" / "skills" / "manage" / "scripts"
SCRATCH = Path("C:/Projects/.tmp/second-brain-loop-44")
SCRIPT_FILES = ("projects.py", "workqueue.py")


def remove_tree(path: Path) -> None:
    import os
    import stat

    def retry(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onexc=retry)


def build(root: Path, mutate: tuple[str, str, str] | None = None) -> Path:
    """A fresh small brain. `mutate` = (file, regex, replacement) on a script copy."""
    if root.exists():
        remove_tree(root)
    scripts = root / ".claude" / "skills" / "manage" / "scripts"
    scripts.mkdir(parents=True)
    (root / "CLAUDE.md").write_text("# scratch brain\n", encoding="utf-8")
    for name in SCRIPT_FILES:
        shutil.copyfile(SRC_SCRIPTS / name, scripts / name)
    if mutate:
        name, pattern, repl = mutate
        f = scripts / name
        text = f.read_text(encoding="utf-8")
        new, n = re.subn(pattern, repl, text, count=1, flags=re.S)
        if not n:
            raise SystemExit(f"mutation matched nothing in {name}: {pattern!r}")
        f.write_text(new, encoding="utf-8")
    for project in ("proj-a", "proj-b"):
        d = root / "projects" / project
        d.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(d)], check=True)
    return root


class Q:
    """One queue command = one process, like the skill runs it."""

    def __init__(self, root: Path):
        self.root = root
        self.script = (
            root / ".claude" / "skills" / "manage" / "scripts" / "workqueue.py"
        )
        self.file = root / ".claude" / "projects" / "queue.json"

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

    def items(self, everything: bool = False) -> list[dict]:
        """ITEM rows of `list`: id, position, project, issue, state."""
        _, out = self.run("list", *(["--all"] if everything else []))
        rows = []
        for row in out.get("ITEM", []):
            parts = [x.strip() for x in row.split("|")]
            rows.append(
                {
                    "id": parts[0],
                    "pos": parts[1],
                    "project": parts[2],
                    "issue": parts[3].lstrip("#"),
                    "state": parts[4],
                }
            )
        return rows

    def file_states(self) -> list[str]:
        if not self.file.is_file():
            return []
        return [i["state"] for i in json.loads(self.file.read_text("utf-8"))["items"]]

    def order(self) -> list[str]:
        return [
            f"{i['project']}#{i['issue']}"
            for i in self.items()
            if i["state"] == "queued"
        ]


def scenario(root: Path, res: list[tuple[str, str, bool, str]]) -> None:
    q = Q(root)

    def add(ac: str, name: str, ok: bool, detail: str = "") -> None:
        res.append((ac, name, ok, detail))

    # --- AC1: one active at a time, across projects -----------------------------
    q.run("add", "proj-a", "1", "--title", "first")
    q.run("add", "proj-b", "2", "--title", "second")
    q.run("add", "proj-a", "3", "--title", "third")
    q.run("add", "proj-b", "4", "--title", "fourth")
    states = q.file_states()
    add(
        "AC1",
        "four approved items across two projects: exactly one is active",
        states.count("active") == 1 and states.count("queued") == 3,
        f"states={states}",
    )
    first = [i for i in q.items() if i["state"] == "active"]
    add(
        "AC1",
        "the active one is the first approved, and it is in proj-a (the other project waits)",
        len(first) == 1 and (first[0]["project"], first[0]["issue"]) == ("proj-a", "1"),
        f"active={first}",
    )

    # --- AC2: waiting in approval order -----------------------------------------
    add(
        "AC2",
        "the queued items wait in the order they were approved",
        q.order() == ["proj-b#2", "proj-a#3", "proj-b#4"],
        f"order={q.order()}",
    )
    code, out = q.run("add", "proj-a", "3")
    add(
        "AC2",
        "approving the same issue twice does not queue it twice",
        code == 1
        and out.get("STATUS") == ["ALREADY_QUEUED"]
        and q.order().count("proj-a#3") == 1,
        f"status={out.get('STATUS')} order={q.order()}",
    )

    # --- AC3: view, reorder, remove ---------------------------------------------
    rows = q.items()
    add(
        "AC3",
        "the owner can view the queue: project, issue and state for every item",
        len(rows) == 4
        and all(r["project"] and r["issue"] and r["state"] for r in rows),
        f"rows={rows}",
    )
    third = next(i for i in rows if (i["project"], i["issue"]) == ("proj-a", "3"))
    code, _ = q.run("move", third["id"], "1")
    add(
        "AC3",
        "the owner can reorder: proj-a#3 moved to the front of the queue",
        code == 0 and q.order() == ["proj-a#3", "proj-b#2", "proj-b#4"],
        f"order={q.order()}",
    )
    active_row = next(i for i in q.items() if i["state"] == "active")
    code, _ = q.run("move", active_row["id"], "1")
    code2, _ = q.run("move", third["id"], "9")
    add(
        "AC3",
        "the running item cannot be moved, and a position out of range is refused",
        code == 1 and code2 == 1 and q.order() == ["proj-a#3", "proj-b#2", "proj-b#4"],
        f"active_move_exit={code} bad_position_exit={code2} order={q.order()}",
    )
    fourth = next(i for i in q.items() if (i["project"], i["issue"]) == ("proj-b", "4"))
    code, _ = q.run("remove", fourth["id"])
    add(
        "AC3",
        "the owner can remove an item: proj-b#4 is gone from the queue",
        code == 0 and q.order() == ["proj-a#3", "proj-b#2"],
        f"order={q.order()}",
    )

    # --- AC4: the next one starts when the active one finishes or stops ---------
    code, out = q.run("finish")
    now_active = [
        (i["project"], i["issue"]) for i in q.items() if i["state"] == "active"
    ]
    add(
        "AC4",
        "when the active item finishes, the first queued one starts (proj-a#3)",
        code == 0
        and now_active == [("proj-a", "3")]
        and q.file_states().count("active") == 1,
        f"active={now_active} next={out.get('NEXT_STARTED')}",
    )
    code, out = q.run("stop", "owner stopped it")
    now_active = [
        (i["project"], i["issue"]) for i in q.items() if i["state"] == "active"
    ]
    add(
        "AC4",
        "when the active item stops, the next queued one starts (proj-b#2)",
        code == 0 and now_active == [("proj-b", "2")],
        f"active={now_active} next={out.get('NEXT_STARTED')}",
    )
    stopped = [i for i in q.items(True) if i["state"] == "stopped"]
    add(
        "AC4",
        "a stopped item stays on record as stopped, not erased",
        len(stopped) == 1
        and (stopped[0]["project"], stopped[0]["issue"]) == ("proj-a", "3"),
        f"stopped={stopped}",
    )
    q.run("add", "proj-a", "5", "--title", "fifth")
    active_id = next(i["id"] for i in q.items() if i["state"] == "active")
    q.run("remove", active_id)
    now_active = [
        (i["project"], i["issue"]) for i in q.items() if i["state"] == "active"
    ]
    add(
        "AC4",
        "when the owner removes the running item, the next one starts (proj-a#5)",
        now_active == [("proj-a", "5")],
        f"active={now_active}",
    )
    q.run("finish")
    code, out = q.run("finish")
    add(
        "AC4",
        "with nothing left, finishing again says so and nothing starts",
        code == 1
        and out.get("STATUS") == ["NOTHING_ACTIVE"]
        and q.file_states().count("active") == 0,
        f"status={out.get('STATUS')}",
    )

    # --- AC5: survives a restart; interrupted work is reported ------------------
    q.run("add", "proj-a", "6", "--title", "sixth")
    q.run("add", "proj-b", "7", "--title", "seventh")
    q.run("add", "proj-a", "8", "--title", "eighth")
    # the session ends here: nothing finishes or stops proj-a#6. A restart is a new
    # process on the same brain folder, so no state is carried but the queue file.
    code, out = q.run("recover")
    interrupted = out.get("INTERRUPTED", [])
    add(
        "AC5",
        "after a restart the cut-off work is reported by name: proj-a#6",
        code == 0
        and out.get("STATUS") == ["RECOVERED"]
        and len(interrupted) == 1
        and "proj-a" in interrupted[0]
        and "#6" in interrupted[0],
        f"status={out.get('STATUS')} interrupted={interrupted}",
    )
    everything = {(i["project"], i["issue"]): i["state"] for i in q.items(True)}
    add(
        "AC5",
        "the interrupted item is kept on record as interrupted, never dropped",
        everything.get(("proj-a", "6")) == "interrupted",
        f"states={everything}",
    )
    add(
        "AC5",
        "the queued items survived, in order, and the next one is now running",
        everything.get(("proj-b", "7")) == "active" and q.order() == ["proj-a#8"],
        f"states={everything} order={q.order()}",
    )
    q.run("finish")  # proj-b#7 done, proj-a#8 starts
    q.run("finish")  # proj-a#8 done: nothing is running when the next session starts
    code, out = q.run("recover")
    add(
        "AC5",
        "the next restart does not report proj-a#6 again (reported once, not on every boot)",
        code == 0
        and out.get("STATUS") == ["NOTHING_INTERRUPTED"]
        and not out.get("INTERRUPTED"),
        f"status={out.get('STATUS')}",
    )
    # a session ending mid-write leaves the previous queue, not half of one
    add(
        "AC5",
        "writes are swapped in whole: no temp file is left beside the queue",
        not list(q.file.parent.glob("*.tmp")),
        f"files={sorted(p.name for p in q.file.parent.iterdir())}",
    )
    # moving the brain leaves the queue found (zero hardcoding)
    moved = root.parent / (root.name + "-moved")
    if moved.exists():
        remove_tree(moved)
    shutil.copytree(root, moved)
    mq = Q(moved)
    add(
        "AC5",
        "after the brain folder is renamed the same queue is found",
        [i["id"] for i in mq.items(True)] == [i["id"] for i in q.items(True)]
        and mq.order() == q.order(),
        f"moved_order={mq.order()}",
    )
    remove_tree(moved)


# One mutation per behaviour: the check must fail for exactly that criterion's rule.
MUTATIONS: list[tuple[str, str, str, str]] = [
    (
        "AC1",
        "a second item can start while one is active",
        r"    if active\(q\) is not None:\n        return None\n",
        "",
    ),
    (
        "AC2",
        "newest first instead of approval order",
        r'q\["items"\]\.append\(item\)',
        'q["items"].insert(0, item)',
    ),
    (
        "AC3",
        "the list leaves out the state",
        r"\| \{i\['state'\]\}\{title\}",
        "{title}",
    ),
    (
        "AC3",
        "move does nothing",
        r"waiting\.insert\(want - 1, item\)",
        "waiting.append(item)",
    ),
    (
        "AC3",
        "remove leaves the item in place",
        r'        q\["items"\]\.remove\(item\)\n',
        "        pass\n",
    ),
    (
        "AC4",
        "nothing starts when the active item ends",
        r"    started = advance\(q\)\n    save\(q\)\n    print\(\"STATUS: FINISHED\"",
        '    started = None\n    save(q)\n    print("STATUS: FINISHED"',
    ),
    (
        "AC5",
        "a restart reports nothing",
        r'        print\(\s*f"INTERRUPTED:.*?\n        \)\n',
        "        pass\n",
    ),
    (
        "AC5",
        "the queue is not kept between runs",
        r"    os\.replace\(tmp, f\)",
        "    pass",
    ),
]


# The wiring: the skill text that makes a brain call the script at the right moments.
# Static -- it proves the text is there, not that a brain follows it (behaviour-pending).
SKILL = Path(".claude/skills/manage/SKILL.md")
START = Path(".claude/skills/session-start/SKILL.md")
WIRING: list[tuple[str, str, Path, str]] = [
    (
        "AC1",
        "on yes the item goes on the queue and work begins only if it starts",
        SKILL,
        r"put it on the queue.*?begin only if it starts",
    ),
    (
        "AC1",
        "never start work on an issue while another item is active",
        SKILL,
        r"Never start work on an issue while another item is `active`",
    ),
    (
        "AC1",
        "add -> STARTED means begin now; QUEUED means do not begin",
        SKILL,
        r"`STATUS: STARTED` \| Nothing was running: begin the work now.*?`STATUS: QUEUED`.*?Do not begin",
    ),
    (
        "AC2",
        "approved work is queued in the order approved",
        SKILL,
        r"the rest wait in the order they\s+were approved",
    ),
    ("AC3", "the owner can view the queue (list)", SKILL, r"workqueue\.py list"),
    (
        "AC3",
        "the owner can reorder (move)",
        SKILL,
        r"workqueue\.py move <id> <position>",
    ),
    ("AC3", "the owner can remove items (remove)", SKILL, r"workqueue\.py remove <id>"),
    (
        "AC4",
        "when work closes or stops, finish / stop and read NEXT_STARTED",
        SKILL,
        r"`finish` / `stop` \|.*?`NEXT_STARTED:`",
    ),
    ("AC5", "session start runs recover", START, r"workqueue\.py recover"),
    (
        "AC5",
        "each INTERRUPTED line is said to the owner by project and issue",
        START,
        r"INTERRUPTED: <id> \| <project> \| #<issue> \| <title>.*?say each one in the report",
    ),
    (
        "AC5",
        "interrupted work is kept on the queue, never dropped",
        START,
        r"kept on the queue as `interrupted`, never dropped",
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
    src_root = REPO_ROOT / "src"
    for (ac, name, _, _), ok in zip(WIRING, wiring_eval(src_root)):
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
        root = build(SCRATCH / f"mutant-{idx}", ("workqueue.py", pattern, repl))
        res = run_scenario(root)
        failing = sorted({r[0] for r in res if not r[2]})
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

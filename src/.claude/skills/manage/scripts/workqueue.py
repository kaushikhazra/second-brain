#!/usr/bin/env python3
"""The work queue -- approved work across all managed projects, one piece active.

    python .claude/skills/manage/scripts/workqueue.py add <project> <issue> [--title <text>]
    python .claude/skills/manage/scripts/workqueue.py list [--all]
    python .claude/skills/manage/scripts/workqueue.py move <id> <position>
    python .claude/skills/manage/scripts/workqueue.py remove <id>
    python .claude/skills/manage/scripts/workqueue.py finish
    python .claude/skills/manage/scripts/workqueue.py stop [<reason>]
    python .claude/skills/manage/scripts/workqueue.py recover

The queue is one file, `<brain root>/.claude/projects/queue.json` -- machine-local,
beside the per-project records, and found from this script's own location, so
moving or renaming the brain leaves it found. Only the brain's one session writes
it; each change is written whole and swapped in, so a session ending mid-write
leaves the previous queue, never half of one.

An item is `queued`, `active`, `done`, `stopped` or `interrupted`. At most one is
`active`, across every project. Items wait in the order they were approved. When
the active item is finished, stopped or removed, the first queued one starts.

`recover` is run once at the start of a session. A session that ends leaves
nothing running, so an item still `active` at that moment was cut off: it becomes
`interrupted`, is reported (`INTERRUPTED:` lines), and the queue moves on. It is
never dropped from the list.

Output is `KEY: value` lines, the first one `STATUS: <code>`. Exit 0 on success,
1 on a refusal. Standard library only.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import projects  # noqa: E402  -- the manage skill's own script, beside this one

LIVE = ("active", "queued")


def queue_path() -> Path:
    return projects.brain_root() / ".claude" / "projects" / "queue.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load() -> dict:
    f = queue_path()
    try:
        data = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    except (ValueError, OSError):
        data = {}
    data.setdefault("items", [])
    data.setdefault("next_id", 1)
    return data


def save(q: dict) -> None:
    f = queue_path()
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(q, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, f)


def active(q: dict) -> dict | None:
    return next((i for i in q["items"] if i["state"] == "active"), None)


def queued(q: dict) -> list[dict]:
    return [i for i in q["items"] if i["state"] == "queued"]


def advance(q: dict) -> dict | None:
    """Start the first queued item if nothing is active. Returns the one started."""
    if active(q) is not None:
        return None
    waiting = queued(q)
    if not waiting:
        return None
    waiting[0]["state"] = "active"
    waiting[0]["started_at"] = now()
    return waiting[0]


def describe(i: dict) -> str:
    title = f" | {i['title']}" if i.get("title") else ""
    return f"{i['project']} | #{i['issue']} | {i['state']}{title}"


def print_next(started: dict | None) -> None:
    if started:
        print(f"NEXT_STARTED: {started['id']} | {describe(started)}")
    else:
        print("NEXT_STARTED: none")


def find_item(q: dict, ident: str) -> dict | None:
    return next((i for i in q["items"] if str(i["id"]) == str(ident).lstrip("#")), None)


def cmd_add(key: str, issue: str, title: str) -> int:
    p = projects.find(key)
    if p is None:
        return projects.not_managed(key)
    issue = issue.lstrip("#")
    q = load()
    twin = next(
        (
            i
            for i in q["items"]
            if i["project"] == p.name and i["issue"] == issue and i["state"] in LIVE
        ),
        None,
    )
    if twin:
        print("STATUS: ALREADY_QUEUED")
        print(f"ITEM: {twin['id']} | {describe(twin)}")
        return 1
    item = {
        "id": q["next_id"],
        "project": p.name,
        "issue": issue,
        "title": title,
        "state": "queued",
        "approved_at": now(),
    }
    q["next_id"] += 1
    q["items"].append(item)
    started = advance(q)
    save(q)
    print("STATUS: STARTED" if started is item else "STATUS: QUEUED")
    print(f"ITEM: {item['id']} | {describe(item)}")
    if started is not item:
        print(f"POSITION: {queued(q).index(item) + 1}")
        print(f"ACTIVE: {describe(active(q))}")
    return 0


def cmd_list(everything: bool) -> int:
    q = load()
    shown = [i for i in q["items"] if everything or i["state"] in LIVE]
    # active first, then the queue in approval order, then the rest by id
    rank = {"active": 0, "queued": 1}
    shown.sort(
        key=lambda i: (rank.get(i["state"], 2), 0 if i["state"] in rank else i["id"])
    )
    print("STATUS: LISTED")
    print(f"ACTIVE: {'yes' if active(q) else 'no'}")
    print(f"QUEUED: {len(queued(q))}")
    pos = 0
    for i in shown:
        if i["state"] == "queued":
            pos += 1
            where = str(pos)
        else:
            where = "-"
        print(f"ITEM: {i['id']} | {where} | {describe(i)}")
    return 0


def cmd_move(ident: str, position: str) -> int:
    q = load()
    item = find_item(q, ident)
    if item is None:
        print("STATUS: NOT_FOUND")
        print(f"ITEM: {ident}")
        return 1
    if item["state"] != "queued":
        print("STATUS: NOT_QUEUED")
        print(f"ITEM: {item['id']} | {describe(item)}")
        return 1
    try:
        want = int(position)
    except ValueError:
        want = 0
    waiting = queued(q)
    if not 1 <= want <= len(waiting):
        print("STATUS: BAD_POSITION")
        print(f"QUEUED: {len(waiting)}")
        return 1
    waiting.remove(item)
    waiting.insert(want - 1, item)
    q["items"] = [i for i in q["items"] if i["state"] != "queued"] + waiting
    save(q)
    print("STATUS: MOVED")
    print(f"ITEM: {item['id']} | {describe(item)}")
    print(f"POSITION: {want}")
    return 0


def cmd_remove(ident: str) -> int:
    q = load()
    item = find_item(q, ident)
    if item is None:
        print("STATUS: NOT_FOUND")
        print(f"ITEM: {ident}")
        return 1
    if item["state"] not in LIVE:
        print("STATUS: NOT_IN_QUEUE")
        print(f"ITEM: {item['id']} | {describe(item)}")
        return 1
    was_active = item["state"] == "active"
    if was_active:
        # the owner takes the running work off the queue: it stops, and is kept
        item["state"] = "stopped"
        item["ended_at"] = now()
        item["reason"] = "removed by the owner"
    else:
        q["items"].remove(item)
    started = advance(q)
    save(q)
    print("STATUS: REMOVED")
    print(f"ITEM: {item['id']} | {item['project']} | #{item['issue']}")
    print(f"WAS_ACTIVE: {'yes' if was_active else 'no'}")
    print_next(started)
    return 0


def end_active(state: str, reason: str) -> int:
    q = load()
    item = active(q)
    if item is None:
        print("STATUS: NOTHING_ACTIVE")
        return 1
    item["state"] = state
    item["ended_at"] = now()
    if reason:
        item["reason"] = reason
    started = advance(q)
    save(q)
    print("STATUS: FINISHED" if state == "done" else "STATUS: STOPPED")
    print(f"ITEM: {item['id']} | {describe(item)}")
    print_next(started)
    return 0


def cmd_recover() -> int:
    q = load()
    cut = [i for i in q["items"] if i["state"] == "active"]
    for i in cut:
        i["state"] = "interrupted"
        i["ended_at"] = now()
        i["reason"] = "the session ended while it was active"
    started = advance(q) if cut else None
    if cut:
        save(q)
    print("STATUS: RECOVERED" if cut else "STATUS: NOTHING_INTERRUPTED")
    for i in cut:
        print(
            f"INTERRUPTED: {i['id']} | {i['project']} | #{i['issue']} | {i.get('title', '')}"
        )
    if cut:
        print_next(started)
    print(f"QUEUED: {len(queued(q))}")
    return 0


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    if cmd == "add" and len(rest) >= 2:
        title = ""
        if "--title" in rest:
            at = rest.index("--title")
            title = " ".join(rest[at + 1 :])
            rest = rest[:at]
        return cmd_add(rest[0], rest[1], title)
    if cmd == "list":
        return cmd_list("--all" in rest)
    if cmd == "move" and len(rest) == 2:
        return cmd_move(rest[0], rest[1])
    if cmd == "remove" and len(rest) == 1:
        return cmd_remove(rest[0])
    if cmd == "finish" and not rest:
        return end_active("done", "")
    if cmd == "stop":
        return end_active("stopped", " ".join(rest))
    if cmd == "recover" and not rest:
        return cmd_recover()
    print(
        "usage: workqueue.py add <project> <issue> [--title <text>] | list [--all]"
        " | move <id> <position> | remove <id> | finish | stop [<reason>] | recover",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

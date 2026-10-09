#!/usr/bin/env python3
"""A project's hooks -- list them, adopt one the owner names, remove an adopted one.

    python .claude/skills/manage/scripts/projecthooks.py list <project>
    python .claude/skills/manage/scripts/projecthooks.py adopt <project> <number>
    python .claude/skills/manage/scripts/projecthooks.py adopted
    python .claude/skills/manage/scripts/projecthooks.py remove <id>

`list` only reads: it prints the project's hooks, numbered, and changes nothing. A
project's hooks never become the brain's own until the owner names one to `adopt`.

An adopted hook is written to the brain's `.claude/settings.local.json` -- machine-local,
so a brain update that replaces `settings.json` leaves it alone -- and applies to every
project in this brain. Its command is rewritten to start from `$CLAUDE_PROJECT_DIR` (the
brain root, which Claude Code resolves at the moment the hook fires) plus
`projects/<name>/`, so the hook keeps firing when the brain folder is renamed or moved.
Nothing records an absolute path of the brain.

A hook that duplicates one the brain already has (same event, matcher and command), or
conflicts with one (same event and matcher, a different command), is reported and not
added. What was adopted is remembered in `.claude/projects/adopted-hooks.json`.

Output is `KEY: value` lines, the first one `STATUS: <code>`. Exit 0 on success, 1 on a
refusal. Standard library only.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import projects  # noqa: E402  -- the manage skill's own script, beside this one

APPLIES = "every project in this brain"
VAR = re.compile(r"\$\{CLAUDE_PROJECT_DIR\}|\$CLAUDE_PROJECT_DIR")


def settings_local() -> Path:
    return projects.brain_root() / ".claude" / "settings.local.json"


def registry_path() -> Path:
    return projects.brain_root() / ".claude" / "projects" / "adopted-hooks.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(f: Path, data: dict) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(f.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, f)


def read_json(f: Path) -> dict:
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    except (ValueError, OSError):
        return {}


def load_registry() -> dict:
    data = read_json(registry_path())
    data.setdefault("items", [])
    data.setdefault("next_id", 1)
    return data


def portable(command: str, project: Path) -> str:
    """The command as it must be written in the brain's settings: rooted at
    $CLAUDE_PROJECT_DIR + projects/<name>, never at an absolute path of this machine."""
    base = f"$CLAUDE_PROJECT_DIR/projects/{project.name}"
    out = VAR.sub(base, command)
    # an absolute path of the project, then of the brain, in either slash style
    for absolute, replacement in (
        (str(project).replace("\\", "/"), base),
        (str(projects.brain_root()).replace("\\", "/"), "$CLAUDE_PROJECT_DIR"),
    ):
        for form in (absolute, absolute.replace("/", "\\")):
            out = out.replace(form, replacement)
    return out


def describe(e: dict) -> str:
    return f"{e['event']} | {e['matcher']} | {e['command']}"


def cmd_list(key: str) -> int:
    p = projects.find(key)
    if p is None:
        return projects.not_managed(key)
    entries, notes = projects.hook_entries(p)
    adopted = {
        (i["project"], i["event"], i["matcher"], i["original_command"])
        for i in load_registry()["items"]
    }
    print("STATUS: LISTED")
    print(f"PROJECT: {p.name}")
    print("NOTE: listing adopts nothing")
    for n in notes:
        print(f"UNREADABLE: {n}")
    for n, e in enumerate(entries, 1):
        mine = (p.name, e["event"], e["matcher"], e["command"]) in adopted
        print(
            f"HOOK: {n} | {describe(e)} | {e['file']} | adopted: {'yes' if mine else 'no'}"
        )
    print(f"HOOKS: {len(entries)}")
    return 0


def existing_brain_hooks() -> list[dict]:
    entries, _ = projects.hook_entries(projects.brain_root())
    return entries


def cmd_adopt(key: str, number: str) -> int:
    p = projects.find(key)
    if p is None:
        return projects.not_managed(key)
    entries, _ = projects.hook_entries(p)
    if not number.isdigit() or not 1 <= int(number) <= len(entries):
        print("STATUS: NO_SUCH_HOOK")
        print(f"PROJECT: {p.name}")
        print(f"HOOKS: {len(entries)}")
        return 1
    chosen = entries[int(number) - 1]
    command = portable(chosen["command"], p)
    same_slot = [
        e
        for e in existing_brain_hooks()
        if e["event"] == chosen["event"] and e["matcher"] == chosen["matcher"]
    ]
    for e in same_slot:
        if e["command"] == command:
            print("STATUS: DUPLICATE")
            print(f"HOOK: {describe({**chosen, 'command': command})}")
            print(f"EXISTING: {describe(e)} | {e['file']}")
            print("ADDED: nothing")
            return 1
    if same_slot:
        e = same_slot[0]
        print("STATUS: CONFLICT")
        print(f"HOOK: {describe({**chosen, 'command': command})}")
        print(f"EXISTING: {describe(e)} | {e['file']}")
        print("ADDED: nothing")
        return 1
    settings = read_json(settings_local())
    hook = {**chosen["hook"], "command": command}
    group: dict = {"hooks": [hook]}
    if chosen["matcher"] != "*":
        group = {"matcher": chosen["matcher"], **group}
    settings.setdefault("hooks", {}).setdefault(chosen["event"], []).append(group)
    write_json(settings_local(), settings)
    reg = load_registry()
    item = {
        "id": reg["next_id"],
        "project": p.name,
        "event": chosen["event"],
        "matcher": chosen["matcher"],
        "original_command": chosen["command"],
        "command": command,
        "adopted_at": now(),
    }
    reg["next_id"] += 1
    reg["items"].append(item)
    write_json(registry_path(), reg)
    print("STATUS: ADOPTED")
    print(f"HOOK_ID: {item['id']}")
    print(f"PROJECT: {p.name}")
    print(f"HOOK: {describe({**chosen, 'command': command})}")
    print("WHERE: .claude/settings.local.json")
    print(f"APPLIES_TO: {APPLIES}")
    return 0


def cmd_adopted() -> int:
    reg = load_registry()
    print("STATUS: LISTED")
    for i in reg["items"]:
        print(
            f"ADOPTED: {i['id']} | {i['project']} | {i['event']} | {i['matcher']} | {i['command']}"
        )
    print(f"ADOPTED_COUNT: {len(reg['items'])}")
    print(f"APPLIES_TO: {APPLIES}")
    return 0


def cmd_remove(ident: str) -> int:
    reg = load_registry()
    item = next((i for i in reg["items"] if str(i["id"]) == ident.lstrip("#")), None)
    if item is None:
        print("STATUS: NOT_FOUND")
        print(f"HOOK_ID: {ident}")
        return 1
    settings = read_json(settings_local())
    groups = settings.get("hooks", {}).get(item["event"], [])
    removed = False
    for group in list(groups):
        if (group.get("matcher", "*") or "*") != item["matcher"]:
            continue
        for h in list(group.get("hooks", [])):
            if h.get("command") == item["command"]:
                group["hooks"].remove(h)
                removed = True
        if not group.get("hooks"):
            groups.remove(group)
    if not groups:
        settings.get("hooks", {}).pop(item["event"], None)
    if not settings.get("hooks", True):
        settings.pop("hooks", None)
    if removed:
        write_json(settings_local(), settings)
    reg["items"].remove(item)
    write_json(registry_path(), reg)
    print("STATUS: REMOVED")
    print(f"HOOK_ID: {item['id']}")
    print(f"PROJECT: {item['project']}")
    print(f"HOOK: {item['event']} | {item['matcher']} | {item['command']}")
    print(f"SETTINGS_ENTRY: {'removed' if removed else 'was already gone'}")
    return 0


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) == 2 and argv[0] == "list":
        return cmd_list(argv[1])
    if len(argv) == 3 and argv[0] == "adopt":
        return cmd_adopt(argv[1], argv[2])
    if argv == ["adopted"]:
        return cmd_adopted()
    if len(argv) == 2 and argv[0] == "remove":
        return cmd_remove(argv[1])
    print(
        "usage: projecthooks.py list <project> | adopt <project> <number>"
        " | adopted | remove <id>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

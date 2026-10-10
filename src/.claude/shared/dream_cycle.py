"""Shared state, run gate and saved plan for the heartbeat's dream cycle (issue #46).

A dream cycle is one small batch of reversible consolidation, run from the heartbeat on
a quiet beat while the owner has switched it on. This module holds everything about the
cycle that can be decided without talking to synaptra:

  * the owner's switch, batch size and progress -- one entry (`dream_cycle`) in the
    activation record, through `activation.py`, so it survives a restart and `/update`
    exactly as the other habits do;
  * the run gate (`should_run`) -- one function, so the heartbeat and a hand-run cycle
    ask the same question;
  * the day's saved plan -- the dry-run action list, computed once a day and kept in
    `.claude/dream-cycle-plan.json`, from which each cycle takes its next batch.

Only reversible actions are planned: `promote` (a retype) and `archive`. A `merge`
rewrites a memory's content and a `flag_contradiction` adds edges; both stay for a hand
`/dream` and are only counted (`needs_dream`).

Pure functions over dicts, except `plan_path` / `load_plan` / `save_plan`. Nothing here
talks to synaptra.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from activation import brain_root, load_record, record_path, save_record

HABIT = "dream_cycle"
DEFAULT_BATCH = 25
PLAN_FILE = "dream-cycle-plan.json"
LOG_FILE = "dream-cycle-log.md"
REVERSIBLE = ("promote", "archive")


def _entry(record: dict) -> dict:
    e = record.get(HABIT)
    return e if isinstance(e, dict) else {}


def switch(record: dict, version: str, active: bool) -> dict:
    """NEW record with the cycle switched on or off. Unlike `activation.set_answer`
    this keeps the batch size and the progress -- switching must never lose them."""
    updated = dict(record)
    updated[HABIT] = {
        **_entry(record),
        "answered_at_version": str(version),
        "active": bool(active),
    }
    return updated


def set_batch_size(record: dict, n: int) -> dict:
    """NEW record with the batch size set. Refuses anything below 1."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError(f"batch size must be a whole number of at least 1, got {n!r}")
    entry = _entry(record)
    updated = dict(record)
    updated[HABIT] = {
        "answered_at_version": entry.get("answered_at_version"),
        "active": bool(entry.get("active", False)),
        **entry,
        "batch_size": n,
    }
    return updated


def status(record: dict) -> dict:
    """What the owner is told: on or off, batch size, cycles run, backlog (None until a
    plan has been made)."""
    e = _entry(record)
    return {
        "active": bool(e.get("active", False)),
        "batch_size": e.get("batch_size", DEFAULT_BATCH),
        "cycles_run": int(e.get("cycles_run", 0)),
        "backlog": e.get("backlog"),
        "needs_dream": e.get("needs_dream", 0),
        "last_cycle": e.get("last_cycle"),
    }


def record_cycle(
    record: dict, done: dict, backlog_after: int, needs_dream: int | None = None
) -> dict:
    """NEW record after one cycle. Called the same way for a cycle started by hand and
    one started by the heartbeat, and whether or not the switch is on (AC 10)."""
    entry = _entry(record)
    updated = dict(record)
    new = {
        "answered_at_version": entry.get("answered_at_version"),
        "active": bool(entry.get("active", False)),
        **entry,
        "cycles_run": int(entry.get("cycles_run", 0)) + 1,
        "backlog": int(backlog_after),
        "last_cycle": dict(done),
    }
    if needs_dream is not None:
        new["needs_dream"] = int(needs_dream)
    updated[HABIT] = new
    return updated


def should_run(
    record: dict, quiet: bool, curiosity_ran: bool, owner_active: bool
) -> bool:
    """The heartbeat's gate. A cycle runs only while the switch is on, on a quiet beat,
    never in the same beat as curiosity, and never while the owner is in conversation."""
    return (
        bool(_entry(record).get("active", False))
        and quiet
        and not curiosity_ran
        and not owner_active
    )


# --- the day's saved plan -------------------------------------------------------------


def plan_path(root: Path | None = None) -> Path | None:
    root = root or brain_root()
    return None if root is None else root / ".claude" / PLAN_FILE


def _key(action: dict) -> str:
    return f"{action['action']}:{action['source_ids'][0]}"


def new_plan(actions: list[dict], today: str) -> dict:
    """The dry-run action list, reduced to what a cycle may apply. Everything else is
    only counted, so the status can say what needs a hand `/dream`."""
    todo = [
        {**a, "key": _key(a), "applied": False}
        for a in actions
        if a.get("action") in REVERSIBLE and a.get("source_ids")
    ]
    return {
        "date": today,
        "actions": todo,
        "needs_dream": sum(1 for a in actions if a.get("action") not in REVERSIBLE),
    }


def pending(plan: dict) -> list[dict]:
    return [a for a in plan.get("actions", []) if not a.get("applied")]


def backlog(plan: dict) -> int:
    return len(pending(plan))


def plan_is_stale(plan: dict | None, today: str) -> bool:
    """Re-run the dry run only on a new day, or when the list is used up."""
    return not plan or plan.get("date") != today or backlog(plan) == 0


def next_batch(plan: dict, n: int) -> list[dict]:
    """The next `n` actions not yet applied, in plan order."""
    return pending(plan)[: max(0, int(n))]


def mark_applied(plan: dict, keys: list[str]) -> dict:
    """NEW plan with the named actions marked applied. A blocked action (a protected id)
    is marked too, by the caller, so it is not retried every cycle."""
    done = set(keys)
    return {
        **plan,
        "actions": [
            {**a, "applied": a["applied"] or a["key"] in done} for a in plan["actions"]
        ],
    }


def load_plan(path: Path | None) -> dict | None:
    if path is None or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def save_plan(path: Path | None, plan: dict) -> None:
    if path is None:
        raise ValueError("save_plan: no path -- brain root could not be resolved")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# --- the brain's log ------------------------------------------------------------------


def log_path(root: Path | None = None) -> Path | None:
    root = root or brain_root()
    return None if root is None else root / ".claude" / LOG_FILE


def log_line(
    by: str,
    done: dict,
    backlog_before: int,
    backlog_after: int,
    now: datetime | None = None,
) -> str:
    """One line per cycle, the same shape whether it was started by hand or by the
    heartbeat (AC 9, AC 10)."""
    stamp = (now or datetime.now()).strftime("%Y-%m-%d %H:%M")
    return (
        f"{stamp} by={by} promoted={done.get('promoted', 0)} "
        f"archived={done.get('archived', 0)} skipped={done.get('skipped', 0)} "
        f"backlog {backlog_before}->{backlog_after}"
    )


def append_log(path: Path | None, line: str) -> None:
    if path is None:
        raise ValueError("append_log: no path -- brain root could not be resolved")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# --- the command line the skill drives ------------------------------------------------


def _version(root: Path | None) -> str:
    v = (root / "VERSION") if root else None
    return v.read_text(encoding="utf-8").strip() if v and v.is_file() else "unknown"


def _describe(rec: dict) -> str:
    s = status(rec)
    backlog_txt = (
        "unknown until the first plan" if s["backlog"] is None else str(s["backlog"])
    )
    extra = f", {s['needs_dream']} more need a hand /dream" if s["needs_dream"] else ""
    return (
        f"Dream cycle is {'on' if s['active'] else 'off'}. Batch size {s['batch_size']}. "
        f"Cycles run {s['cycles_run']}. Backlog {backlog_txt}{extra}."
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="dream_cycle")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("on")
    sub.add_parser("off")
    sz = sub.add_parser("size")
    sz.add_argument("n", type=int)
    sub.add_parser("status")
    pf = sub.add_parser(
        "plan-from", help="save the day's plan from a dry-run actions JSON file"
    )
    pf.add_argument("actions_file")
    sub.add_parser(
        "batch", help="print the next batch as JSON; STALE means re-run the dry run"
    )
    fin = sub.add_parser("finish", help="record one finished cycle")
    fin.add_argument("--by", choices=("hand", "heartbeat"), required=True)
    fin.add_argument("--promoted", type=int, default=0)
    fin.add_argument("--archived", type=int, default=0)
    fin.add_argument("--skipped", type=int, default=0)
    fin.add_argument(
        "--keys", default="", help="comma-separated keys of every action handled"
    )
    a = p.parse_args(argv)

    root = brain_root()
    rpath = record_path(root)
    rec = load_record(rpath)
    today = datetime.now().date().isoformat()

    if a.cmd in ("on", "off"):
        rec = switch(rec, _version(root), active=a.cmd == "on")
        save_record(rpath, rec)
        print(f"Dream cycle is {a.cmd}.")
    elif a.cmd == "size":
        try:
            rec = set_batch_size(rec, a.n)
        except ValueError as e:
            print(f"Not changed: {e}.")
            return 2
        save_record(rpath, rec)
        print(f"Batch size is {a.n}.")
    elif a.cmd == "status":
        print(_describe(rec))
    elif a.cmd == "plan-from":
        actions = json.loads(Path(a.actions_file).read_text(encoding="utf-8"))
        plan = new_plan(actions, today)
        save_plan(plan_path(root), plan)
        entry = {
            **_entry(rec),
            "backlog": backlog(plan),
            "needs_dream": plan["needs_dream"],
        }
        rec = {**rec, HABIT: {"active": False, "answered_at_version": None, **entry}}
        save_record(rpath, rec)
        print(
            f"Plan saved: {backlog(plan)} to apply, {plan['needs_dream']} need a hand /dream."
        )
    elif a.cmd == "batch":
        plan = load_plan(plan_path(root))
        if plan_is_stale(plan, today):
            print("STALE")
            return 0
        print(json.dumps(next_batch(plan, status(rec)["batch_size"])))
    elif a.cmd == "finish":
        plan = load_plan(plan_path(root))
        if not plan:
            print("No plan to finish against.")
            return 2
        before = backlog(plan)
        keys = [k for k in a.keys.split(",") if k]
        plan = mark_applied(plan, keys)
        save_plan(plan_path(root), plan)
        done = {"promoted": a.promoted, "archived": a.archived, "skipped": a.skipped}
        rec = record_cycle(rec, done, backlog_after=backlog(plan))
        save_record(rpath, rec)
        append_log(log_path(root), log_line(a.by, done, before, backlog(plan)))
        print(f"Cycle logged. Backlog {before} -> {backlog(plan)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

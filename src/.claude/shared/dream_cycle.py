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

import json
from pathlib import Path

from activation import brain_root

HABIT = "dream_cycle"
DEFAULT_BATCH = 25
PLAN_FILE = "dream-cycle-plan.json"
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

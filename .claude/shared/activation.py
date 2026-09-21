"""Shared activation-record mechanism for opt-in idle habits.

Issue #6 registers the first habit, `curiosity`. A later habit (issue #7,
`news`) registers a second entry in the *same* record through the *same*
`/session-start` step -- this module is what keeps that a one-line addition
rather than a second block of logic.

The record is one git-ignored JSON file at the brain root,
`.claude/activations.json`, holding one entry per habit:

    {"curiosity": {"answered_at_version": "0.3.1", "active": true}}

Every reader and writer of the record -- `/session-start`'s activation step,
`/curiosity`'s own `on` / `off` / `status` handling, and the heartbeat's
quiet-cycle gate -- goes through the functions below. There is exactly one
place that knows the record's shape.

Reads and writes only this one file; nothing here talks to synaptra.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def brain_root(start: Path | None = None) -> Path | None:
    """Walk up from `start` (default: this file's own directory) to the first
    directory holding both `.claude/` and `CLAUDE.md`. Never hardcoded --
    resolved fresh, every call, relative to where this module actually lives."""
    here = start or Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / ".claude").is_dir() and (candidate / "CLAUDE.md").is_file():
            return candidate
    return None


def record_path(root: Path | None = None) -> Path | None:
    """The activation record's path, or None if the brain root cannot be
    resolved. Callers that get None should treat activation as unavailable --
    same posture as a missing self map: report it, don't crash the boot."""
    root = root or brain_root()
    if root is None:
        return None
    return root / ".claude" / "activations.json"


def load_record(path: Path | None) -> dict:
    """Reads the record. Missing path, missing file, or a file that fails to
    parse as a JSON object all return `{}` -- a corrupt or absent record must
    not crash a boot, and re-asking (the safe direction) is what an empty
    record naturally produces via `needs_ask`."""
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_record(path: Path | None, record: dict) -> None:
    """Writes the whole record in one shot -- callers resolve every habit's
    answer first, then save once, so a boot that asks about two habits does
    not write the file twice."""
    if path is None:
        raise ValueError("save_record: no path -- brain root could not be resolved")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _entry(record: dict, habit: str) -> dict | None:
    entry = record.get(habit)
    return entry if isinstance(entry, dict) else None


def needs_ask(record: dict, habit: str, version: str) -> bool:
    """True when `habit` has never been answered, or was answered against a
    different VERSION than the one passed in now."""
    entry = _entry(record, habit)
    if entry is None:
        return True
    return entry.get("answered_at_version") != version


def is_active(record: dict, habit: str) -> bool:
    entry = _entry(record, habit)
    if entry is None:
        return False
    return bool(entry.get("active", False))


def answered_at_version(record: dict, habit: str) -> str | None:
    entry = _entry(record, habit)
    if entry is None:
        return None
    v = entry.get("answered_at_version")
    return v if isinstance(v, str) else None


def set_answer(record: dict, habit: str, version: str, active: bool) -> dict:
    """Returns a NEW record with `habit`'s entry set to `(version, active)`.
    Pure -- does not touch disk. A pure function is what keeps every caller
    (the session-start step, `/curiosity on|off`, `/news on|off`) producing
    the exact same entry shape instead of three slightly different ones.

    Resets `last_run` (issue #7) -- a fresh answer is a fresh start, and a
    habit that was just re-asked (a VERSION change) should be free to run
    again today rather than staying silent because of a run recorded under
    the old answer."""
    updated = dict(record)
    updated[habit] = {"answered_at_version": str(version), "active": bool(active)}
    return updated


def last_run(record: dict, habit: str) -> str | None:
    """The ISO date (`YYYY-MM-DD`) `habit` last ran on, or None if it has
    never run (or the record predates issue #7 and has no such field)."""
    entry = _entry(record, habit)
    if entry is None:
        return None
    v = entry.get("last_run")
    return v if isinstance(v, str) else None


def ran_today(record: dict, habit: str, today: str | None = None) -> bool:
    """True when `habit`'s `last_run` is today's date. `today` is injectable
    for tests; real callers omit it and get the local calendar date."""
    today = today or datetime.now().date().isoformat()
    return last_run(record, habit) == today


def set_last_run(record: dict, habit: str, today: str | None = None) -> dict:
    """Returns a NEW record with `habit`'s `last_run` set to today's date,
    leaving `answered_at_version`/`active` untouched. Raises if `habit` has
    no entry yet -- a habit that was never activated has nothing to stamp a
    run against."""
    entry = _entry(record, habit)
    if entry is None:
        raise ValueError(f"set_last_run: {habit!r} has no activation entry yet")
    today = today or datetime.now().date().isoformat()
    updated = dict(record)
    updated[habit] = {**entry, "last_run": today}
    return updated

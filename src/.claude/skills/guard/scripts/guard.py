#!/usr/bin/env python3
"""The owner's switch for the command guard: `/guard on | off | status`.

    python guard.py on | off | status | line

The setting is the "guard" entry of the activation record
(.claude/activations.json), written through shared/activation.py like /curiosity
and /news. hooks/command_guard.py reads the same entry on every tool call.
`line` is what /session-start prints: one sentence when the guard is off,
nothing when it is on.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / ".claude" / "shared"))

from activation import (  # noqa: E402
    answered_at_version,
    is_active,
    load_record,
    record_path,
    save_record,
    set_answer,
)

HABIT = "guard"
OFF_LINE = "The command guard is off. Switch it on with /guard on."


def version():
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def main(argv):
    action = argv[1] if len(argv) > 1 else "status"
    record = load_record(record_path(ROOT))
    if action in ("on", "off"):
        record = set_answer(record, HABIT, version(), active=action == "on")
        save_record(record_path(ROOT), record)
        print(f"The command guard is {action}.")
    elif action == "status":
        seen = answered_at_version(record, HABIT)
        state = "active" if is_active(record, HABIT) else "inactive"
        print(f"{state} (set at {seen})" if seen else f"{state} (never set)")
    elif action == "line":
        if not is_active(record, HABIT):
            print(OFF_LINE)
    else:
        print("usage: guard.py on | off | status | line", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

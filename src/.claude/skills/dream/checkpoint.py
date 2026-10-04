"""Pre-dream checkpoint: a file copy of the memory store, proven by count.

Run by /dream with this brain's own interpreter, before anything is reshaped:

    .claude/.venv/Scripts/python.exe .claude/skills/dream/checkpoint.py --expect <N>

<N> is memory_stats' storage.memory_count, read from the live store just
before. The store is SurrealKV, which is plain files, so copying the folder
is the whole backup. synaptra's own backup command is not used.

The brain is running while this copies, so the copy is taken live. That is
why the count exists: the copy is opened on its own and must hold exactly
<N> memories, or the checkpoint is refused and there is no dream.
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

# This file lives at <brain>/.claude/skills/dream/checkpoint.py.
ROOT = Path(__file__).resolve().parents[3]
LIVE = ROOT / ".claude" / "synaptra-data"
BACKUPS = ROOT / ".claude" / "dream-backups"


def count_memories(path):
    """Count memories in a store folder, opened raw -- no synaptra schema."""
    from surrealdb import Surreal

    db = Surreal("surrealkv://" + str(path).replace("\\", "/"))
    db.connect()
    db.use("cognitive", "memory")
    res = db.query("SELECT count() FROM memory GROUP ALL")
    db.close()
    rows = res if isinstance(res, list) else [res]
    if rows and isinstance(rows[0], dict) and "result" in rows[0]:
        rows = rows[0]["result"] or []
    return rows[0].get("count", 0) if rows else 0


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--expect",
        type=int,
        required=True,
        help="live memory count from memory_stats (storage.memory_count)",
    )
    args = ap.parse_args()

    if not LIVE.is_dir() or not any(LIVE.iterdir()):
        print(f"STOPPED: no memory store at {LIVE}")
        return 1

    dest = BACKUPS / datetime.now().strftime("%Y-%m-%d_%H%M%S") / "synaptra-data"
    print(f"copying  {LIVE}")
    print(f"     to  {dest}")
    shutil.copytree(LIVE, dest)

    def discard():
        # A refused copy looks exactly like a rollback point and is not one.
        # It is this run's own folder, so it goes.
        shutil.rmtree(dest.parent, ignore_errors=True)

    try:
        got = count_memories(dest)
    except Exception as e:  # noqa: BLE001
        discard()
        print(
            f"STOPPED: the copy would not open ({type(e).__name__}: {e}). "
            "It was probably caught mid-write. Wait a minute and run the "
            "checkpoint again. No dream without a checkpoint."
        )
        return 1

    print(f"live     {args.expect:,} memories")
    print(f"copy     {got:,} memories")
    if got != args.expect:
        discard()
        print(
            f"STOPPED: DEFECT -- the copy holds {got:,} memories, the live "
            f"store {args.expect:,}. This copy is not a rollback point. "
            "No dream."
        )
        return 1

    backup = dest.parent
    print("\nCHECKPOINT OK")
    print(f"backup   {backup}")
    print("rollback close every session of this brain, then")
    print(f"         rename  {LIVE}  to  synaptra-data.before-rollback")
    print(f"         copy    {dest}")
    print(f"         to      {LIVE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

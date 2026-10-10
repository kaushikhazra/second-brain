#!/usr/bin/env python3
"""Issue #46 -- the cycle against a REAL store: AC 4, 9, 10.

Why this exists. `check_dream_cycle_cli.py` proves the cycle's bookkeeping, but the counts
it records are the skill's own tally. This check does not take anyone's word for them: it
seeds a scratch synaptra store, takes a real `consolidate(dry_run=True)`, applies one
batch of its `promote` and `archive` actions through the engine, takes a second dry run
and compares the backlog the STORE reports before and after.

Scratch only. The store lives at `C:/Projects/.tmp/second-brain-loop-46/store` and is
opened in-process (no server, no port), so it can never be the live memory.

Run it with a Python that has `synaptra` installed -- this brain's own interpreter:

    .claude/.venv/Scripts/python.exe checks/dream-cycle/check_dream_cycle_store.py

Exit 0 all pass, 1 a check failed, 2 synaptra is not importable (nothing was checked).
"""

from __future__ import annotations

import asyncio
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src" / ".claude" / "shared"))

STORE = Path("C:/Projects/.tmp/second-brain-loop-46/store")
RATER = "check-dream-cycle"
BATCH = 5

PROMOTE_TEXTS = [
    "Kaushik prefers short status reports with the result first.",
    "The kettle in the workshop whistles at about ninety degrees.",
    "Bicycle tyres should be kept near forty pounds in cold weather.",
    "The harbour ferry timetable changes on the first of March.",
]
ARCHIVE_TEXTS = [
    "Scratch note: remember to water the fern on the balcony.",
    "Scratch note: the parcel courier will knock twice on Tuesday.",
    "Scratch note: the lamp bulb in the hallway is the warm kind.",
    "Scratch note: the library book is due after the long weekend.",
]
KEEP_TEXTS = [
    "Photosynthesis converts light, water and carbon dioxide into sugar and oxygen.",
    "The Treaty of Westphalia in 1648 ended the Thirty Years War in Europe.",
    "A binary search halves the remaining range on every comparison it makes.",
]


async def main() -> int:
    try:
        import dream_cycle as dc
        from synaptra.engine import MemoryEngine
    except ImportError as e:
        print(f"[SKIP] cannot import: {e}. Run with a Python that has synaptra.")
        return 2

    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, bool(ok), detail))

    if STORE.exists():
        shutil.rmtree(STORE)
    STORE.mkdir(parents=True)
    engine = MemoryEngine(db_path="surrealkv://" + str(STORE).replace("\\", "/"))
    today = datetime.now().date().isoformat()
    now = datetime.now(timezone.utc)

    async def seed(texts: list[str], mtype: str, importance: float) -> list[str]:
        ids = []
        for t in texts:
            m = await engine.store_memory(
                t,
                memory_type=mtype,
                importance=importance,
                tags=["dc-check"],
                rater=RATER,
            )
            ids.append(m.id)
        return ids

    promote_ids = await seed(PROMOTE_TEXTS, "working", 0.6)
    archive_ids = await seed(ARCHIVE_TEXTS, "working", 0.2)
    keep_ids = await seed(KEEP_TEXTS, "semantic", 0.7)
    for mid in promote_ids:
        await engine.storage.update_memory_fields(mid, access_count=3)
    for mid in archive_ids:
        await engine.storage.update_memory_fields(
            mid, last_accessed=now - timedelta(days=90)
        )
    everything = promote_ids + archive_ids + keep_ids

    # --- the first dry run: the plan the store itself produces -------------------------
    actions0 = await engine.consolidate(dry_run=True)
    plan0 = dc.new_plan(actions0, today)
    before = dc.backlog(plan0)
    kinds = sorted({a["action"] for a in plan0["actions"]})
    check(
        "STORE-1: a real dry run yields reversible work to do (promote and archive)",
        before >= BATCH and "promote" in kinds and "archive" in kinds,
        f"backlog={before} kinds={kinds} needs_dream={plan0['needs_dream']}",
    )
    seeded_keep_touched = [
        a for a in plan0["actions"] if a["source_ids"][0] in keep_ids
    ]
    check(
        "STORE-2: the healthy memories are not in the plan",
        not seeded_keep_touched,
        f"touched={[a['key'] for a in seeded_keep_touched]}",
    )

    # --- one cycle: the next batch, applied one action at a time -----------------------
    batch = dc.next_batch(plan0, BATCH)
    check(
        "AC4: a cycle takes at most the batch size",
        0 < len(batch) <= BATCH,
        f"{len(batch)}",
    )
    promoted = archived = skipped = 0
    handled: list[str] = []
    for a in batch:
        mid = a["source_ids"][0]
        handled.append(a["key"])
        mem = await engine.storage.get_memory(mid)
        if mem is None or mem.state.value != "active":
            skipped += 1
            continue
        if a["action"] == "promote":
            if mem.memory_type.value != a["from_type"]:
                skipped += 1
                continue
            await engine.update_memory(mid, memory_type=a["to_type"])
            promoted += 1
        else:
            await engine.archive_memory(mid)
            archived += 1
    plan1 = dc.mark_applied(plan0, handled)
    check(
        "AC9a: the plan's own count falls by the batch",
        dc.backlog(plan0) - dc.backlog(plan1) == len(batch),
        f"{dc.backlog(plan0)} -> {dc.backlog(plan1)}",
    )

    # --- the second dry run: what the STORE now says is left ---------------------------
    actions1 = await engine.consolidate(dry_run=True)
    after = dc.backlog(dc.new_plan(actions1, today))
    check(
        "AC9b: the store's own backlog fell after the cycle",
        after < before,
        f"store dry run: {before} -> {after} (applied: promoted={promoted} archived={archived} skipped={skipped})",
    )
    check(
        "AC9c: it fell by exactly what the cycle applied",
        before - after == promoted + archived,
        f"before-after={before - after} applied={promoted + archived}",
    )

    # --- reversibility -----------------------------------------------------------------
    states = {}
    for mid in everything:
        m = await engine.storage.get_memory(mid)
        states[mid] = m
    check(
        "Reversible: nothing was deleted, every seeded memory still exists",
        all(m is not None for m in states.values()),
        f"missing={[i for i, m in states.items() if m is None]}",
    )
    check(
        "Reversible: promoted memories changed type only, content intact",
        all(
            states[a["source_ids"][0]].content in (PROMOTE_TEXTS + ARCHIVE_TEXTS)
            for a in batch
            if a["action"] == "promote"
        ),
    )
    arch = [a["source_ids"][0] for a in batch if a["action"] == "archive"]
    if arch:
        victim = arch[0]
        original = states[victim].content
        restored = await engine.restore_memory(victim)
        check(
            "Reversible: an archived memory restores intact",
            restored is not None
            and restored.state.value == "active"
            and restored.content == original,
            f"id={victim}",
        )
    else:
        check(
            "Reversible: an archived memory restores intact",
            False,
            "no archive in batch",
        )

    # --- hand and heartbeat finish through the same record -----------------------------
    rec = dc.record_cycle(
        {},
        {"promoted": promoted, "archived": archived},
        backlog_after=dc.backlog(plan1),
    )
    rec = dc.record_cycle(
        rec, {"promoted": 0, "archived": 0}, backlog_after=dc.backlog(plan1)
    )
    check(
        "AC10: two cycles, whoever started them, are counted the same way",
        dc.status(rec)["cycles_run"] == 2
        and dc.status(rec)["backlog"] == dc.backlog(plan1),
        f"{dc.status(rec)}",
    )

    engine.close()

    width = max(len(n) for n, _, _ in results)
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name.ljust(width)}  {detail}")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} checks pass")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

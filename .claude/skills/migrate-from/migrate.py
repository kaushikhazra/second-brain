"""Move an old second brain (SB + cognitive-memory) into this one (SB + synaptra).

Run by /migrate-from with this brain's own interpreter:

    .claude/.venv/Scripts/python.exe .claude/skills/migrate-from/migrate.py \
        --old-brain <path> [--old-store <path>]

Copy only. Nothing in the old brain or the old memory store is changed, so the
old brain keeps working and can run in parallel until the owner is satisfied.

Steps, each one stops the run on failure:
  1. resolve the old memory store
  2. copy it into .claude/synaptra-data
  3. count the copy as the old CM wrote it (raw surrealdb, no synaptra)
  4. open the copy with synaptra -- this applies synaptra's schema -- and
     count again; every number must match
  5. carry the owner's files across from the old brain folder
  6. block the old cognitive-memory tools inside this brain only
"""

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# This file lives at <brain>/.claude/skills/migrate-from/migrate.py.
# The brain resolves its own root; nothing is baked in.
ROOT = Path(__file__).resolve().parents[3]
CLAUDE_DIR = ROOT / ".claude"
DEST_STORE = CLAUDE_DIR / "synaptra-data"
PARK_DIR = CLAUDE_DIR / "migrated-from-old"
REPORT = CLAUDE_DIR / "migration-report.json"

RELS = [
    "causes",
    "follows",
    "contradicts",
    "supports",
    "relates_to",
    "supersedes",
    "part_of",
    "describes",
]

# Every file a pre-synaptra second brain shipped with, by git blob hash.
# Commits b91a948, f58e282, 47c6e75 (7 Jul 2026) -- the only releases that
# used cognitive-memory. A file matching one of these is stock and is not
# carried; the new brain ships its own version.
STOCK = {
    ".claude/skills/dream/SKILL.md": {"2f7d65b29b93afd80ba86fad3480596a1d6c796f"},
    ".claude/skills/heartbeat/SKILL.md": {
        "190c2f21fc1edf2ab0342bead88c62eb2a16c31d",
        "06dfd85f7426241e00105041fed8b19971220860",
    },
    ".claude/skills/init-brain/SKILL.md": {"8278ca61a61dfcc16d215116f2a31400f56330fe"},
    ".claude/skills/session-end/SKILL.md": {"6f688fcd246b539ed784bb765eaacb152cf11587"},
    ".claude/skills/session-start/SKILL.md": {
        "b8b4bf1e5786e3d48c4f66da0d26d69770b63428"
    },
    ".gitignore": {"74dd69060648ab8649ccb0e9a8c2051ff9c70813"},
    "CLAUDE.md": {"54645c1a17ac40352d95b22dc94986231c9915de"},
    "README.md": {"1304ebb00dd9ebf6ef9bae3844bca7eacf376ff0"},
}

# Never carried: version control and machine-local runtime of the old brain.
SKIP_DIRS = {
    ".git",
    ".venv",
    ".python",
    "__pycache__",
    "synaptra-data",
    ".claude-config",
}

DENY_RULE = "mcp__cognitive-memory"


def say(msg=""):
    print(msg, flush=True)


def fail(msg):
    say(f"\nSTOPPED: {msg}")
    sys.exit(1)


def blob_hashes(data):
    """Git blob hash of the bytes as-is, and with CRLF folded to LF.

    A checkout with autocrlf on has CRLF on disk while git hashed LF, so a
    stock file would otherwise look edited.
    """
    out = set()
    for body in {data, data.replace(b"\r\n", b"\n")}:
        h = hashlib.sha1(b"blob %d\0" % len(body) + body)
        out.add(h.hexdigest())
    return out


def resolve_old_store(arg):
    if arg:
        raw, source = arg, "--old-store"
    elif os.environ.get("COGNITIVE_MEMORY_DB"):
        raw, source = os.environ["COGNITIVE_MEMORY_DB"], "COGNITIVE_MEMORY_DB"
    else:
        raw, source = str(Path.home() / ".cognitive-memory" / "data"), "default"
    if raw.startswith("surrealkv://"):
        raw = raw[len("surrealkv://") :]
    path = Path(raw).expanduser().resolve()
    return path, source


def surreal_url(path):
    return "surrealkv://" + str(path).replace("\\", "/")


def count_raw(path):
    """Count the copy exactly as the old CM left it -- no synaptra import."""
    from surrealdb import Surreal

    db = Surreal(surreal_url(path))
    db.connect()
    db.use("cognitive", "memory")

    def n(sql):
        res = db.query(sql)
        rows = res if isinstance(res, list) else [res]
        if rows and isinstance(rows[0], dict) and "result" in rows[0]:
            rows = rows[0]["result"] or []
        return rows[0].get("count", 0) if rows else 0

    counts = {
        "memories": n("SELECT count() FROM memory GROUP ALL"),
        "active": n("SELECT count() FROM memory WHERE state = 'active' GROUP ALL"),
        "edges": sum(n(f"SELECT count() FROM {r} GROUP ALL") for r in RELS),
        "versions": n("SELECT count() FROM memory_version GROUP ALL"),
    }
    db.close()
    return counts


async def open_with_synaptra(path):
    """Open the copy the way the brain will, count, and read it back."""
    from synaptra.surreal_storage import SurrealStorage

    st = SurrealStorage(surreal_url(path))

    def n(sql):
        rows = st._rows(st._db.query(sql))
        return rows[0]["count"] if rows else 0

    counts = {
        "memories": n("SELECT count() FROM memory GROUP ALL"),
        "active": n("SELECT count() FROM memory WHERE state = 'active' GROUP ALL"),
        "edges": sum(n(f"SELECT count() FROM {r} GROUP ALL") for r in RELS),
        "versions": n("SELECT count() FROM memory_version GROUP ALL"),
    }

    reads = {}
    newest = st._rows(
        st._db.query(
            "SELECT id, created_at FROM memory WHERE state = 'active' "
            "ORDER BY created_at DESC LIMIT 1"
        )
    )
    if newest:
        mid = str(newest[0]["id"]).split(":", 1)[1].strip("⟨⟩`")
        got = await st.get_memory(mid)
        reads["newest"] = got.content[:140] if got else None
        reads["newest_created"] = str(newest[0].get("created_at"))
        if got and got.embedding:
            reads["vector_hits"] = len(await st.vector_search(got.embedding, top_k=5))
        if got:
            words = [w for w in got.content.split() if len(w) > 4][:3]
            if words:
                reads["keyword_hits"] = len(
                    await st.keyword_search(" ".join(words), limit=5)
                )
    return counts, reads


def carry_files(old_brain):
    """Copy the owner's files; park anything that would overwrite the new brain."""
    copied, parked, skipped = [], [], []
    for src in sorted(old_brain.rglob("*")):
        if not src.is_file():
            continue
        rel_parts = src.relative_to(old_brain).parts
        if any(p in SKIP_DIRS for p in rel_parts):
            continue
        rel = "/".join(rel_parts)
        data = src.read_bytes()

        if STOCK.get(rel, set()) & blob_hashes(data):
            skipped.append(rel)
            continue

        dest = ROOT / rel
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            copied.append(rel)
        elif dest.read_bytes() == data:
            skipped.append(rel)
        else:
            park = PARK_DIR / rel
            park.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, park)
            parked.append(rel)
    return copied, parked, skipped


def block_old_tools():
    """Deny the old cognitive-memory MCP inside this brain only.

    The old CM is registered user-wide, so without this its tools appear here
    too and a write can land in the old store. settings.local.json is
    project-scoped and gitignored by Claude Code; the old brain is unaffected.
    """
    path = CLAUDE_DIR / "settings.local.json"
    cfg = {}
    if path.exists():
        try:
            cfg = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            fail(f"{path} is not valid JSON; fix or remove it and re-run")
    deny = cfg.setdefault("permissions", {}).setdefault("deny", [])
    if DENY_RULE not in deny:
        deny.append(DENY_RULE)
        path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--old-brain", required=True)
    ap.add_argument("--old-store")
    args = ap.parse_args()

    old_brain = Path(args.old_brain).expanduser().resolve()
    if not old_brain.is_dir():
        fail(f"old brain folder not found: {old_brain}")
    if old_brain == ROOT:
        fail("the old brain and this brain are the same folder")

    say(f"this brain   {ROOT}")
    say(f"old brain    {old_brain}")

    # 1. resolve
    store, source = resolve_old_store(args.old_store)
    say(f"old memories {store}   ({source})")
    if not store.is_dir() or not any(store.iterdir()):
        fail(
            f"no memory store at {store}. Pass --old-store <path> if CM keeps "
            "it somewhere else."
        )
    size = sum(f.stat().st_size for f in store.rglob("*") if f.is_file())
    say(f"             {size / 1_048_576:,.0f} MB")

    # 2. copy
    if DEST_STORE.exists() and any(DEST_STORE.iterdir()):
        fail(
            f"{DEST_STORE} already holds a store. Nothing was changed. Move it "
            "aside and re-run if you mean to replace it."
        )
    say("\n[1/4] copying memories (the old store is only read) ...")
    shutil.copytree(store, DEST_STORE, dirs_exist_ok=True)
    say("      done")

    # 3. count as the old CM wrote it
    say("[2/4] counting the copy as the old memory system wrote it ...")
    try:
        before = count_raw(DEST_STORE)
    except Exception as e:  # noqa: BLE001
        shutil.rmtree(DEST_STORE, ignore_errors=True)
        fail(
            f"the copied store would not open ({e}). The old CM was probably "
            "mid-write. Stop the CognitiveMemory scheduled task, re-run, then "
            "start it again."
        )
    say(f"      {before}")

    # 4. open with synaptra
    say("[3/4] opening it with synaptra ...")
    try:
        after, reads = asyncio.run(open_with_synaptra(DEST_STORE))
    except Exception as e:  # noqa: BLE001
        fail(f"synaptra could not open the copy: {e}")
    say(f"      {after}")
    if before != after:
        fail(f"counts differ -- before {before}, after {after}")
    if before["memories"] == 0:
        fail("the store opened but holds no memories")

    # 5. files
    say("[4/4] carrying your files ...")
    copied, parked, skipped = carry_files(old_brain)
    blocked = block_old_tools()

    report = {
        "migrated_at": datetime.now().astimezone().isoformat(),
        "old_brain": str(old_brain),
        "old_store": str(store),
        "before": before,
        "after": after,
        "reads": reads,
        "copied": copied,
        "parked": parked,
        "skipped_stock": skipped,
        "old_tools_blocked_here": blocked or DENY_RULE,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    say("\n================ MIGRATION COMPLETE ================")
    say(f"memories   {before['memories']:,} before  ->  {after['memories']:,} after")
    say(f"active     {before['active']:,}  ->  {after['active']:,}")
    say(f"links      {before['edges']:,}  ->  {after['edges']:,}")
    say(f"versions   {before['versions']:,}  ->  {after['versions']:,}")
    if reads.get("newest"):
        say(f"\nnewest memory ({reads.get('newest_created', '')[:10]}):")
        say(f"  {reads['newest']!r}")
    say(f"\ncopied in   {len(copied)}: {', '.join(copied) or '-'}")
    if parked:
        say(f"parked      {len(parked)} (yours, but the new brain has its own):")
        for p in parked:
            say(f"  .claude/migrated-from-old/{p}")
    say(f"stock, left {len(skipped)}")
    say(f"\nreport: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

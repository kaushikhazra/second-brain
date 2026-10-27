#!/usr/bin/env python3
"""Issue #79 proofs: the session-end conformance scan judges only memories written under the rule.

Builds scratch brains under C:/Projects/.tmp/sb-79-check and runs the real verify_memory.py
(from a scratch copy, so its baseline file is found from its own location) and the real
update_brain.py run_update / restore_backup (--skip-synaptra: the machine is not touched).

    AC 1  a memory with a null rater is not reported
    AC 2  the output says how many memories it did not judge, and why
    AC 3  a memory with a rater and a source without the create-memory: prefix is reported
    AC 4  a list with no rater field at all is judged by source as before
    AC 5  a baseline date: older memories are not judged, newer ones are
    AC 6  an update writes a baseline when there is none, and never overwrites one
    AC 7  --restore removes a baseline the update added and keeps the owner's own
    AC 8  no baseline file: no date limit

Each criterion is shown to bite: the same scenarios run on copies of the two files with one
behaviour removed, and the named criteria must FAIL.

    python checks/session-end/check_conformance_baseline.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH_BASE = Path("C:/Projects/.tmp")
VERIFY = SRC / ".claude" / "skills" / "session-end" / "verify_memory.py"
UPDATE = SRC / ".claude" / "shared" / "update_brain.py"

LEGACY = "aaaaaaaa-0000-0000-0000-000000000001"
LEGACY_OLD_SOURCE = "aaaaaaaa-0000-0000-0000-000000000002"
DIRECT = "bbbbbbbb-0000-0000-0000-000000000003"
CONFORMING = "cccccccc-0000-0000-0000-000000000004"
NO_FIELD = "dddddddd-0000-0000-0000-000000000005"
OLD_DIRECT = "eeeeeeee-0000-0000-0000-000000000006"
NEW_DIRECT = "ffffffff-0000-0000-0000-000000000007"
PAST = "2026-01-01T00:00:00+00:00"
CUT = "2026-06-01T00:00:00+00:00"
AFTER = "2026-09-01T00:00:00+00:00"


def mem(mid, source, rater, created=AFTER, **extra):
    m = {
        "id": mid,
        "state": "active",
        "source": source,
        "created_at": created,
        "tags": [],
        "content": f"memory {mid[:8]}",
        **extra,
    }
    if rater != "__absent__":
        m["rater"] = rater
    return m


# One behaviour removed per mutant: (file, old, new, criteria that must fail).
MUTANTS = {
    "null rater is judged": (
        VERIFY,
        'if "rater" in mem and mem["rater"] is None:',
        "if False:",
        ("AC 1", "AC 2"),
    ),
    "a missing rater field counts as legacy": (
        VERIFY,
        'if "rater" in mem and mem["rater"] is None:',
        'if mem.get("rater") is None:',
        ("AC 4",),
    ),
    "baseline ignored": (VERIFY, "if since and", "if False and", ("AC 5",)),
    "update writes no baseline": (
        UPDATE,
        "        keep_conformance_baseline(brain, backup_dir)\n",
        "",
        ("AC 6",),
    ),
    "update overwrites the baseline": (
        UPDATE,
        "    path = brain / BASELINE\n    if path.exists():\n        return\n",
        "    path = brain / BASELINE\n",
        ("AC 6",),
    ),
    "restore leaves the baseline the update added": (
        UPDATE,
        "(brain / BASELINE).unlink(missing_ok=True)",
        "pass",
        ("AC 7",),
    ),
    "restore removes any baseline": (
        UPDATE,
        'if meta.get("baseline_added") is True:',
        "if True:",
        ("AC 7",),
    ),
}


def load(path: Path):
    spec = importlib.util.spec_from_file_location(f"um_{abs(hash(str(path)))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scan(verify_py: Path, base: Path, name: str, memories, baseline: str | None):
    """Run verify_memory.py from a scratch .claude/skills/session-end/ and return its stdout."""
    claude = base / name / ".claude"
    where = claude / "skills" / "session-end"
    where.mkdir(parents=True)
    shutil.copy(verify_py, where / "verify_memory.py")
    if baseline:
        (claude / "conformance-baseline.json").write_text(
            json.dumps({"since": baseline}), encoding="utf-8"
        )
    data = base / f"{name}.json"
    data.write_text(
        json.dumps({"memories": memories, "resolved": {}}), encoding="utf-8"
    )
    r = subprocess.run(
        [sys.executable, str(where / "verify_memory.py"), str(data)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return r.stdout + r.stderr


def flagged(out: str, mid: str) -> bool:
    return f"id={mid}" in out


def quiet(fn, *a, **kw):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            return out.getvalue(), fn(*a, **kw), None
        except SystemExit as exc:
            return out.getvalue(), None, exc


def make_brain(base: Path, name: str):
    brain, release = base / name, base / f"{name}-release"
    for d in (brain, release):
        shutil.copytree(SRC, d, ignore=shutil.ignore_patterns("__pycache__"))
    (brain / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    return brain, release


def only_backup(brain: Path) -> Path:
    return next((brain / ".claude" / ".update-backup").iterdir())


def scenarios(
    verify_py: Path, update_py: Path, base: Path
) -> dict[str, tuple[bool, str]]:
    r: dict[str, tuple[bool, str]] = {}

    out = scan(
        verify_py,
        base,
        "s1",
        [
            mem(LEGACY, None, None),
            mem(LEGACY_OLD_SOURCE, "cognitive-memory-migration", None),
            mem(DIRECT, None, "claude-sonnet-5-5"),
            mem(CONFORMING, "create-memory:claude-sonnet-5-5", "claude-sonnet-5-5"),
            mem(NO_FIELD, "somewhere-else", "__absent__"),
        ],
        baseline=None,
    )
    r["AC 1"] = (
        not flagged(out, LEGACY) and not flagged(out, LEGACY_OLD_SOURCE),
        f"legacy flagged: {flagged(out, LEGACY)}/{flagged(out, LEGACY_OLD_SOURCE)}",
    )
    r["AC 2"] = (
        "2 active memories not judged" in out and "rater" in out,
        next(
            (l.strip() for l in out.splitlines() if "not judged" in l), "no such line"
        ),
    )
    r["AC 3"] = (
        flagged(out, DIRECT) and not flagged(out, CONFORMING),
        f"direct flagged: {flagged(out, DIRECT)}, conforming flagged: {flagged(out, CONFORMING)}",
    )
    r["AC 4"] = (
        flagged(out, NO_FIELD),
        f"no-rater-field memory flagged: {flagged(out, NO_FIELD)}",
    )

    out = scan(
        verify_py,
        base,
        "s5",
        [
            mem(OLD_DIRECT, None, "x", created=PAST),
            mem(NEW_DIRECT, None, "x", created=AFTER),
        ],
        baseline=CUT,
    )
    r["AC 5"] = (
        not flagged(out, OLD_DIRECT)
        and flagged(out, NEW_DIRECT)
        and "before the baseline" in out,
        f"older flagged: {flagged(out, OLD_DIRECT)}, newer flagged: {flagged(out, NEW_DIRECT)}",
    )

    out = scan(
        verify_py,
        base,
        "s8",
        [mem(OLD_DIRECT, None, "x", created="2000-01-01T00:00:00+00:00")],
        baseline=None,
    )
    r["AC 8"] = (
        flagged(out, OLD_DIRECT),
        f"year-2000 memory flagged without a baseline: {flagged(out, OLD_DIRECT)}",
    )

    um = load(update_py)

    # AC 6 / AC 7: brain without a baseline.
    brain, release = make_brain(base, "u1")
    path = brain / ".claude" / "conformance-baseline.json"
    before = datetime.now(timezone.utc)
    quiet(um.run_update, brain, release, skip_synaptra=True)
    wrote = path.is_file()
    since = None
    if wrote:
        since = datetime.fromisoformat(json.loads(path.read_text("utf-8"))["since"])
    stamped = wrote and before - timedelta(seconds=5) <= since <= datetime.now(
        timezone.utc
    ) + timedelta(seconds=5)
    _, _, _ = quiet(um.restore_backup, brain, only_backup(brain), skip_synaptra=True)
    removed = not path.exists()

    # Brain that already has a baseline.
    brain2, release2 = make_brain(base, "u2")
    path2 = brain2 / ".claude" / "conformance-baseline.json"
    path2.write_text(json.dumps({"since": CUT}), encoding="utf-8")
    quiet(um.run_update, brain2, release2, skip_synaptra=True)
    kept = path2.is_file() and json.loads(path2.read_text("utf-8"))["since"] == CUT
    quiet(um.restore_backup, brain2, only_backup(brain2), skip_synaptra=True)
    kept_after_restore = (
        path2.is_file() and json.loads(path2.read_text("utf-8"))["since"] == CUT
    )

    r["AC 6"] = (
        bool(stamped) and kept,
        f"written and dated now: {bool(stamped)}; existing baseline untouched: {kept}",
    )
    r["AC 7"] = (
        removed and kept_after_restore,
        f"added baseline removed on restore: {removed}; owner's kept: {kept_after_restore}",
    )
    return r


def main() -> int:
    SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    base = SCRATCH_BASE / "sb-79-check"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir()

    failed = 0
    print("== shipped files ==")
    (base / "real").mkdir()
    real = scenarios(VERIFY, UPDATE, base / "real")
    for ac in sorted(real):
        ok, note = real[ac]
        print(f"  {'PASS' if ok else 'FAIL'}  {ac}  {note}")
        failed += not ok

    print("== each criterion bites ==")
    for i, (name, (target, old, new, must_fail)) in enumerate(MUTANTS.items()):
        mdir = base / f"m{i}"
        mdir.mkdir()
        text = target.read_text("utf-8")
        if old not in text:
            print(f"  FAIL  mutant '{name}': text to remove not found in {target.name}")
            failed += 1
            continue
        mutated = mdir / target.name
        mutated.write_text(text.replace(old, new, 1), encoding="utf-8", newline="")
        got = scenarios(
            mutated if target == VERIFY else VERIFY,
            mutated if target == UPDATE else UPDATE,
            mdir,
        )
        for ac in must_fail:
            bit = not got[ac][0]
            print(f"  {'PASS' if bit else 'FAIL'}  '{name}' makes {ac} fail")
            failed += not bit

    shutil.rmtree(base, ignore_errors=True)
    print("\nOK" if not failed else f"\n{failed} check(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

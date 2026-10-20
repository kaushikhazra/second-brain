#!/usr/bin/env python3
"""Proofs: the update backs up the memory store, and --restore puts it back.

Builds scratch brains under C:/Projects/.tmp/sb-store-* from a copy of src/ and drives the
real run_update / restore_backup of update_brain.py. Only the three calls that touch the
machine (stop synaptra, pip-install synaptra, import-verify it) are replaced; the fake
install "migrates" the store the way synaptra 2.1.1 does on reopen, so a store that was not
backed up first is visibly lost.

    AC 1  the store is copied into the update's backup before synaptra is installed
    AC 2  synaptra is stopped before the store is copied
    AC 3  the copy equals the store as it was before the update
    AC 4  --restore puts that store back, with the prior synaptra version
    AC 5  the store a restore replaces is kept aside and named, not deleted
    AC 6  an update that fails after the install rolls the store back too
    AC 7  a brain with no store updates and restores cleanly
    AC 8  /update's text names the store in what it backs up and what it restores

Each criterion is shown to bite: the same scenarios run on copies of update_brain.py (or
SKILL.md) with one behaviour removed, and the named criteria must FAIL.

    python checks/update/check_store_backup.py
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC = REPO / "src"
SCRATCH_BASE = Path("C:/Projects/.tmp")
UPDATE_PY = SRC / ".claude" / "shared" / "update_brain.py"
SKILL_MD = SRC / ".claude" / "skills" / "update" / "SKILL.md"

STORE_FILES = {"data.db": b"memories as of synaptra 2.0.0", "idx/a.sst": b"index one"}
NEW_SYNAPTRA = "2.1.1"
OLD_SYNAPTRA = "2.0.0"

# One behaviour removed per mutant: (file, old, new, criteria that must fail).
MUTANTS = {
    "store never backed up": (
        UPDATE_PY,
        "            backup_store(brain, backup_dir)\n",
        "            pass\n",
        ("AC 1", "AC 3", "AC 4", "AC 5", "AC 6"),
    ),
    "store copied before synaptra stops": (
        UPDATE_PY,
        "        stop_synaptra(brain)\n\n        # 2b.",
        "        pass\n\n        # 2b.",
        ("AC 2",),
    ),
    "restore leaves the migrated store": (
        UPDATE_PY,
        "                restore_store(brain, backup_dir)\n",
        "                pass\n",
        ("AC 4", "AC 5", "AC 6"),
    ),
    "restore deletes the store it replaces": (
        UPDATE_PY,
        "shutil.move(str(store), str(aside))",
        "shutil.rmtree(store); aside.mkdir()",
        ("AC 5",),
    ),
    "skill text silent about the store": (
        SKILL_MD,
        "memory store",
        "data",
        ("AC 8",),
    ),
}


def load(path: Path):
    spec = importlib.util.spec_from_file_location(f"um_{abs(hash(str(path)))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tree(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def make_store(brain: Path) -> dict[str, str]:
    store = brain / ".claude" / "synaptra-data"
    for rel, data in STORE_FILES.items():
        f = store / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
    return tree(store)


def make_brain(
    base: Path, name: str, with_store: bool = True
) -> tuple[Path, Path, dict]:
    brain, release = base / name, base / f"{name}-release"
    for d in (brain, release):
        shutil.copytree(SRC, d, ignore=shutil.ignore_patterns("__pycache__"))
    (brain / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    (release / "SYNAPTRA_VERSION").write_text(NEW_SYNAPTRA + "\n", encoding="utf-8")
    original = make_store(brain) if with_store else {}
    return brain, release, original


class Fakes:
    """Stand-ins for the three machine-touching calls; they record what they saw."""

    def __init__(self, um, brain: Path, fail_after_install: bool = False):
        self.um, self.brain = um, brain
        self.stopped = False
        self.store_in_backup_at_install: bool | None = None
        self.stopped_at_install: bool | None = None
        self.stopped_at_copy: bool | None = None
        self.installed: list[str] = []
        self.fail = fail_after_install
        um._read_synaptra_version = lambda b: OLD_SYNAPTRA
        um.stop_synaptra = self.stop
        um.install_synaptra = self.install
        um.verify_synaptra_version = self.verify
        # Note whether synaptra was stopped at the moment the store got copied.
        real_backup = getattr(um, "backup_store", None)
        if real_backup:

            def spy(b, d):
                self.stopped_at_copy = self.stopped
                return real_backup(b, d)

            um.backup_store = spy

    def stop(self, brain):
        self.stopped = True
        return True

    def install(self, brain, version):
        backups = list((brain / ".claude" / ".update-backup").glob("*/_store"))
        self.store_in_backup_at_install = bool(backups) and any(backups[0].rglob("*"))
        self.stopped_at_install = self.stopped
        self.installed.append(version)
        store = brain / ".claude" / "synaptra-data"
        if store.is_dir():  # the 2.1.1 migration on reopen: rewrites data, adds fields
            (store / "data.db").write_bytes(b"migrated: adds rater / rated_at")
            (store / "migrated.flag").write_bytes(b"1")

    def verify(self, brain, expected):
        if self.fail and expected == NEW_SYNAPTRA:
            raise SystemExit("FAIL: injected verify failure")


def quiet(fn, *a, **kw):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            return fn(*a, **kw), out.getvalue(), None
        except SystemExit as exc:
            return None, out.getvalue(), exc


def only_backup(brain: Path) -> Path:
    return next((brain / ".claude" / ".update-backup").iterdir())


def scenarios(um, skill_text: str, base: Path) -> dict[str, tuple[bool, str]]:
    r: dict[str, tuple[bool, str]] = {}

    # Successful update, then restore.
    brain, release, original = make_brain(base, "ok")
    fk = Fakes(um, brain)
    _, log, err = quiet(um.run_update, brain, release)
    bdir = only_backup(brain)
    copy = bdir / "_store"
    r["AC 1"] = (
        err is None and fk.store_in_backup_at_install is True,
        f"update exit={err}; store already in backup at install: {fk.store_in_backup_at_install}",
    )
    r["AC 2"] = (
        fk.stopped_at_copy is True and fk.stopped_at_install is True,
        f"stopped at copy={fk.stopped_at_copy}, at install={fk.stopped_at_install}",
    )
    r["AC 3"] = (
        copy.is_dir() and tree(copy) == original,
        f"backup copy files: {sorted(tree(copy)) if copy.is_dir() else 'none'}",
    )
    migrated = tree(brain / ".claude" / "synaptra-data")
    fk.installed.clear()
    _, rlog, rerr = quiet(um.restore_backup, brain, bdir)
    store_now = tree(brain / ".claude" / "synaptra-data")
    r["AC 4"] = (
        rerr is None
        and store_now == original
        and fk.installed == [OLD_SYNAPTRA]
        and migrated != original,
        f"store restored={store_now == original}, reinstalled={fk.installed}, "
        f"migration had changed it={migrated != original}",
    )
    asides = [
        p
        for p in (brain / ".claude").iterdir()
        if p.is_dir() and p.name.startswith("synaptra-data.") and tree(p) == migrated
    ]
    r["AC 5"] = (
        len(asides) == 1 and asides[0].name in rlog,
        f"aside dirs holding the migrated store: {[p.name for p in asides]}; named in output: "
        f"{bool(asides) and asides[0].name in rlog}",
    )

    # Failure after the install.
    brain, release, original = make_brain(base, "fail")
    Fakes(um, brain, fail_after_install=True)
    _, flog, ferr = quiet(um.run_update, brain, release)
    after = tree(brain / ".claude" / "synaptra-data")
    r["AC 6"] = (
        ferr is not None and after == original,
        f"update failed={ferr is not None}; store back to original={after == original}",
    )

    # No store at all.
    brain, release, _ = make_brain(base, "empty", with_store=False)
    Fakes(um, brain)
    _, _, uerr = quiet(um.run_update, brain, release)
    _, _, rerr2 = quiet(um.restore_backup, brain, only_backup(brain))
    r["AC 7"] = (uerr is None and rerr2 is None, f"update={uerr}, restore={rerr2}")

    # The skill names the store where it lists what the update does and what restore does.
    def section(title: str) -> str:
        m = re.search(rf"^## {title}.*?(?=^## )", skill_text, re.S | re.M)
        return m.group(0) if m else ""

    run_s, restore_s = section("Run the update"), section("Restore")
    r["AC 8"] = (
        "memory store" in run_s.lower() and "memory store" in restore_s.lower(),
        f"in Run the update: {'memory store' in run_s.lower()}, in Restore: "
        f"{'memory store' in restore_s.lower()}",
    )
    return r


def main() -> int:
    SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    base = SCRATCH_BASE / "sb-store-check"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir()

    failed = 0
    print("== shipped files ==")
    (base / "real").mkdir()
    real = scenarios(load(UPDATE_PY), SKILL_MD.read_text("utf-8"), base / "real")
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
        py = mutated if target == UPDATE_PY else UPDATE_PY
        skill = (
            mutated.read_text("utf-8")
            if target == SKILL_MD
            else SKILL_MD.read_text("utf-8")
        )
        got = scenarios(load(py), skill, mdir)
        for ac in must_fail:
            bit = not got[ac][0]
            print(f"  {'PASS' if bit else 'FAIL'}  '{name}' makes {ac} fail")
            failed += not bit

    shutil.rmtree(base, ignore_errors=True)
    print("\nOK" if not failed else f"\n{failed} check(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

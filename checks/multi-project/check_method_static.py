#!/usr/bin/env python3
"""Issue #43 -- the script half. No brain, no LLM.

What can be proven without a brain is that the product *says* what each criterion
needs it to say, in the one place the brain reads it: `manage/SKILL.md`, and the
learned-record template in `projects.py` that the method line comes from. That is
not the criterion -- the criteria are the brain's behaviour -- so this check does
not count anything as met. It proves the product text is there, and that the check
notices when it is not.

  python check_method_static.py             check src/
  python check_method_static.py --self-test remove each rule from a copy of src/ and
                                            require the check to fail for exactly it

Criteria whose proof needs a brain (AC 1-5) are behaviour-pending in build-only
mode; AC 1, 2 and 4 were proven by brain runs in cycles 1-2 of the loop.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src"
SCRATCH = Path("C:/Projects/.tmp/second-brain-loop-43/static")

SKILL = Path(".claude/skills/manage/SKILL.md")
SCRIPT = Path(".claude/skills/manage/scripts/projects.py")

# (criterion, what the text must carry, file, regex that finds it)
RULES: list[tuple[str, str, Path, str]] = [
    (
        "AC1",
        "the learned record carries a development method row",
        SKILL,
        r"\|\s*Development method\s*\|",
    ),
    (
        "AC1",
        "the project script's record template has a Development method field",
        SCRIPT,
        r'"Development method"',
    ),
    (
        "AC1",
        "on yes, the brain states the development method before starting",
        SKILL,
        r"\*\*the development method\*\*",
    ),
    (
        "AC2",
        "the project's own method wins while working there",
        SKILL,
        r"the project's rules win over the brain's own",
    ),
    (
        "AC3",
        "no method -> loop engineering, the issue's criteria are the goal",
        SKILL,
        r"loop engineering\*\*: the issue's acceptance criteria are the\s+goal",
    ),
    (
        "AC3",
        "the loop lives in the project's .claude/loop/{issue}-{slug}/",
        SKILL,
        r"\*\*the project's\*\* `\.claude/loop/\{issue\}-\{slug\}/`",
    ),
    (
        "AC3",
        "never in the brain's own .claude/loop/",
        SKILL,
        r"never in the brain's own `\.claude/loop/`",
    ),
    (
        "AC4",
        "work only on a feature branch in the project",
        SKILL,
        r"Work only on a feature branch in the project",
    ),
    (
        "AC4",
        "never commit to the default branch",
        SKILL,
        r"Never commit to the\s+default branch",
    ),
    (
        "AC4",
        "never merge; the owner merges",
        SKILL,
        r"\*\*Never merge\*\*.*?The owner merges\.",
    ),
    (
        "AC5",
        "the closing comment says N of N criteria met",
        SKILL,
        r"\*\"N of N criteria met\"\*",
    ),
    (
        "AC5",
        "one line per criterion saying what proved it",
        SKILL,
        r"one\s+line per criterion saying what proved it",
    ),
    (
        "AC5",
        "the comment goes on the issue in the project's tracker",
        SKILL,
        r"comment on the issue in the project's\s+tracker",
    ),
]


def evaluate(root: Path) -> list[tuple[str, str, bool]]:
    texts: dict[Path, str] = {}
    out = []
    for crit, what, rel, pattern in RULES:
        if rel not in texts:
            f = root / rel
            texts[rel] = f.read_text(encoding="utf-8") if f.is_file() else ""
        out.append((crit, what, bool(re.search(pattern, texts[rel], re.S))))
    return out


def run_check(root: Path) -> int:
    rows = evaluate(root)
    for crit, what, ok in rows:
        print(f"[{'PASS' if ok else 'FAIL'}] {crit}: {what}")
    failed = [r for r in rows if not r[2]]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} product-text rules present.")
    return 1 if failed else 0


def self_test() -> int:
    """Remove each rule's text from a copy and require exactly that rule to fail."""
    bad = 0
    for idx, (crit, what, rel, pattern) in enumerate(RULES):
        copy = SCRATCH / f"rule-{idx}"
        if copy.exists():
            shutil.rmtree(copy)
        (copy / rel).parent.mkdir(parents=True, exist_ok=True)
        for r in {r[2] for r in RULES}:
            (copy / r).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SRC / r, copy / r)
        f = copy / rel
        text = f.read_text(encoding="utf-8")
        cut, n = re.subn(pattern, "", text, count=1, flags=re.S)
        if not n:
            print(f"[FAIL] self-test {crit}: {what} -- rule matches nothing in src/")
            bad += 1
            continue
        f.write_text(cut, encoding="utf-8")
        rows = evaluate(copy)
        failing = [i for i, r in enumerate(rows) if not r[2]]
        ok = idx in failing
        print(
            f"[{'PASS' if ok else 'FAIL'}] self-test {crit}: removing it fails the check"
            f" ({what})" + ("" if len(failing) == 1 else f" [also failed: {failing}]")
        )
        bad += 0 if ok else 1
    print(f"\n{len(RULES) - bad}/{len(RULES)} removals noticed.")
    return 1 if bad else 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    return self_test() if args.self_test else run_check(SRC)


if __name__ == "__main__":
    sys.exit(main())

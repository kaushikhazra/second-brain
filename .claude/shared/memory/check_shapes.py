#!/usr/bin/env python3
"""Check script for issue #2 — AC 1, 2, 3, 4, 23.

Stdlib only, no synaptra import — these criteria are about file shape, not
store behaviour. Run from anywhere; paths are resolved relative to this
file, never to the caller's cwd, so it survives being invoked from a
different directory.

Usage: python check_shapes.py
Exit code 0 iff every criterion checked here holds; non-zero otherwise. The
per-criterion PASS/FAIL lines are the record a cycle log quotes — read those,
not just the exit code.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent
CLAUDE_DIR = SHARED_DIR.parent.parent  # .claude/shared/memory -> .claude
SKILLS_DIR = CLAUDE_DIR / "skills"
REPO_ROOT = CLAUDE_DIR.parent  # .claude -> repo root
SHAPES_FILE = SHARED_DIR / "memory-shapes.md"
SHAPES_FILE_REL = ".claude/shared/memory/memory-shapes.md"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

MEMORY_SKILLS = ["create-memory", "read-memory", "update-memory", "delete-memory"]
FOUR_SHAPES = ["fact", "learning", "persona", "person-model"]
SHAPE_HEADER_RE = {
    shape: re.compile(rf"^#\s+Shape:\s+`{re.escape(shape)}`", re.MULTILINE)
    for shape in FOUR_SHAPES
}
OPERATIONS = ["create", "read", "update", "delete"]
# A level-3 heading whose text contains the operation word, anywhere after the
# '###' — tolerates a leading emphasis marker like '### 🔴 read'.
OP_HEADER_RE = {
    op: re.compile(rf"^###[^\n]*\b{op}\b", re.MULTILINE | re.IGNORECASE)
    for op in OPERATIONS
}

FORBIDDEN_DIRECT_CALLS = re.compile(r"memory_store|memory_update|memory_delete")


def check_ac1() -> tuple[bool, str]:
    """AC1: shapes file exists and defines four shapes, each with create/read/update/delete."""
    if not SHAPES_FILE.is_file():
        return False, f"{SHAPES_FILE_REL} does not exist"
    text = SHAPES_FILE.read_text(encoding="utf-8")
    missing = []
    for shape in FOUR_SHAPES:
        m = SHAPE_HEADER_RE[shape].search(text)
        if not m:
            missing.append(f"no '# Shape: `{shape}`' header")
            continue
        # Slice from this shape's header to the next top-level '# ' header (or EOF)
        start = m.end()
        next_top = re.search(r"^#\s+(?!Shape)", text[start:], re.MULTILINE)
        section = text[start : start + next_top.start()] if next_top else text[start:]
        # Also stop at the next shape header, in case two shapes are adjacent with no other # between
        next_shape = re.search(r"^#\s+Shape:", text[start:], re.MULTILINE)
        if next_shape and (not next_top or next_shape.start() < next_top.start()):
            section = text[start : start + next_shape.start()]
        for op in OPERATIONS:
            if not OP_HEADER_RE[op].search(section):
                missing.append(f"'{shape}' section missing a '### {op}' heading")
    if missing:
        return False, "; ".join(missing)
    return (
        True,
        f"all four shapes ({', '.join(FOUR_SHAPES)}) present with create/read/update/delete",
    )


def check_ac2() -> tuple[bool, str, dict[str, bool]]:
    """AC2: four skills exist and load — SKILL.md present, frontmatter has name + description."""
    present: dict[str, bool] = {}
    problems = []
    for skill in MEMORY_SKILLS:
        skill_md = SKILLS_DIR / skill / "SKILL.md"
        if not skill_md.is_file():
            present[skill] = False
            problems.append(f"{skill}: SKILL.md missing")
            continue
        text = skill_md.read_text(encoding="utf-8")
        fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if not fm:
            present[skill] = False
            problems.append(f"{skill}: no frontmatter block")
            continue
        frontmatter = fm.group(1)
        has_name = re.search(r"^name:\s*\S+", frontmatter, re.MULTILINE) is not None
        has_desc = (
            re.search(r"^description:\s*\S+", frontmatter, re.MULTILINE) is not None
        )
        ok = has_name and has_desc
        present[skill] = ok
        if not ok:
            missing_fields = []
            if not has_name:
                missing_fields.append("name")
            if not has_desc:
                missing_fields.append("description")
            problems.append(f"{skill}: frontmatter missing {', '.join(missing_fields)}")
    all_ok = all(present.values())
    detail = "; ".join(problems) if problems else "all four skills present and load"
    return all_ok, detail, present


def check_ac3(present: dict[str, bool]) -> tuple[bool, str]:
    """AC3: each EXISTING memory skill points at the shapes file and restates none of it.

    Scoped to skills that exist (per AC2) — a skill that hasn't been written yet
    is AC2's failure, not this one's. Restatement is checked for by the presence
    of any of the four shape headers, or the fork's own header, inside the skill.
    """
    existing = [s for s in MEMORY_SKILLS if present.get(s)]
    if not existing:
        return False, "no memory skills exist yet to check"
    problems = []
    for skill in existing:
        text = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
        points_at_file = SHAPES_FILE_REL in text
        restates = False
        restate_reasons = []
        for shape in FOUR_SHAPES:
            if SHAPE_HEADER_RE[shape].search(text):
                restates = True
                restate_reasons.append(f"restates '# Shape: `{shape}`' header")
        if re.search(r"^##\s+The fork", text, re.MULTILINE):
            restates = True
            restate_reasons.append("restates '## The fork' section")
        if not points_at_file:
            problems.append(f"{skill}: does not reference {SHAPES_FILE_REL}")
        if restates:
            problems.append(f"{skill}: {'; '.join(restate_reasons)}")
    ok = not problems
    detail = (
        "; ".join(problems)
        if problems
        else f"{', '.join(existing)} point at the shapes file, restate nothing"
    )
    return ok, detail


def check_ac23() -> tuple[bool, str]:
    """AC23: no skill other than the four memory skills contains a direct memory_store/
    memory_update/memory_delete call."""
    offenders = []
    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        skill_name = skill_md.parent.name
        if skill_name in MEMORY_SKILLS:
            continue
        text = skill_md.read_text(encoding="utf-8")
        if FORBIDDEN_DIRECT_CALLS.search(text):
            offenders.append(skill_name)
    ok = not offenders
    detail = (
        "clean — no direct calls outside the four memory skills"
        if ok
        else f"direct calls found in: {', '.join(sorted(offenders))}"
    )
    return ok, detail


def check_ac4() -> tuple[bool, str]:
    """AC4: CLAUDE.md routes memory writes/changes/removals to the four skills and no
    longer instructs a direct memory_store/memory_update/memory_delete call.

    Heuristic, stated plainly rather than hidden: requires the three "Never call
    `memory_X` directly" prohibitions to be present (proves the routing rule is
    actually stated, not just that the forbidden words are gone), AND requires the
    three writer skills to be named in the same file (proves it points somewhere).
    """
    if not CLAUDE_MD.is_file():
        return False, "CLAUDE.md not found at repo root"
    text = CLAUDE_MD.read_text(encoding="utf-8")
    required_prohibitions = [
        ("memory_store", re.compile(r"[Nn]ever call `memory_store`")),
        ("memory_update", re.compile(r"[Nn]ever call `memory_update`")),
        ("memory_delete", re.compile(r"[Nn]ever call `memory_delete`")),
    ]
    missing_prohibitions = [
        name for name, pat in required_prohibitions if not pat.search(text)
    ]
    required_pointers = ["/create-memory", "/update-memory", "/delete-memory"]
    missing_pointers = [p for p in required_pointers if p not in text]
    ok = not missing_prohibitions and not missing_pointers
    if ok:
        detail = "CLAUDE.md states all three 'never call directly' prohibitions and points at all three writer skills"
    else:
        parts = []
        if missing_prohibitions:
            parts.append(
                f"missing prohibition(s) for: {', '.join(missing_prohibitions)}"
            )
        if missing_pointers:
            parts.append(f"missing pointer(s) to: {', '.join(missing_pointers)}")
        detail = "; ".join(parts)
    if not ok:
        return ok, detail

    # Also confirm the stability-days NUMBERS match the shapes file's — the point of
    # putting them in both places is that they can't silently drift apart.
    claude_stability: dict[str, float] = {}
    for m in re.finditer(
        r"^\|\s*`([\w-]+)`\s*\|.*\|.*\|\s*([\d.]+)\s*\|\s*$", text, re.MULTILINE
    ):
        claude_stability[m.group(1)] = float(m.group(2))

    shapes_text = (
        SHAPES_FILE.read_text(encoding="utf-8") if SHAPES_FILE.is_file() else ""
    )
    stability_block_m = re.search(
        r"Initial stability by type.*?:\*\*(.*?)\.\s*$",
        shapes_text,
        re.MULTILINE | re.DOTALL,
    )
    shapes_stability: dict[str, float] = {}
    if stability_block_m:
        for m in re.finditer(r"`([\w-]+)`\s+([\d.]+)", stability_block_m.group(1)):
            shapes_stability[m.group(1)] = float(m.group(2))

    mismatches = []
    all_types = set(claude_stability) | set(shapes_stability)
    for t in sorted(all_types):
        c, s = claude_stability.get(t), shapes_stability.get(t)
        if c is None:
            mismatches.append(f"{t}: missing from CLAUDE.md's table")
        elif s is None:
            mismatches.append(f"{t}: missing from the shapes file's stability line")
        elif c != s:
            mismatches.append(f"{t}: CLAUDE.md={c} vs shapes file={s}")

    if mismatches:
        return (
            False,
            f"routing text OK, but stability numbers disagree: {'; '.join(mismatches)}",
        )
    return (
        True,
        f"{detail}; stability numbers match the shapes file for all {len(all_types)} types",
    )


def main() -> int:
    results = []

    ok1, detail1 = check_ac1()
    results.append(("AC1", ok1, detail1))

    ok2, detail2, present = check_ac2()
    results.append(("AC2", ok2, detail2))

    ok3, detail3 = check_ac3(present)
    results.append(("AC3", ok3, detail3))

    ok4, detail4 = check_ac4()
    results.append(("AC4", ok4, detail4))

    ok23, detail23 = check_ac23()
    results.append(("AC23", ok23, detail23))

    passed = 0
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"[{status}] {name}: {detail}")

    print(f"\n{passed}/{len(results)} of this script's criteria pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

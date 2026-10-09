"""#45 removal demos for the brain's half (check_hooks_brain.py): set up the scratch brain
exactly as the check does, cut or reverse the skill text and the script behaviour a
brain relies on for one criterion, then run the check's turn and verify. Every demo is
expected to FAIL. Where the brain would behave well unprompted, the rule is replaced by
its opposite.

    python demo_hooks_brain_removals.py <list|adopt|remove|dup|conflict|live>

Each demo has its own scratch root. Run them one at a time.
"""

import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(
    encoding="utf-8", errors="replace"
)  # replies carry arrows and dashes
demo = sys.argv[1]
os.environ["SB_CHECK_SCRATCH"] = f"C:/Projects/.tmp/second-brain-loop-45b-demo-{demo}"
import check_hooks_brain as hb  # noqa: E402  (reads SB_CHECK_SCRATCH at import)

SKILL = ".claude/skills/manage/SKILL.md"
SCRIPT = ".claude/skills/manage/scripts/projecthooks.py"


def cut(path: Path, pattern: str, repl: str = "") -> None:
    text = path.read_text(encoding="utf-8")
    new, n = re.subn(pattern, repl, text, count=1, flags=re.S)
    assert n, f"demo edit matched nothing in {path.name}: {pattern!r}"
    path.write_text(new, encoding="utf-8")
    print(f"demo edit: {path.name} {len(new) - len(text):+d} chars", flush=True)


def apply(c: "hb.Ctx") -> None:
    skill, script = c.brain / SKILL, c.brain / SCRIPT
    if demo == "list":
        # listing adopts: the script's list also adopts every hook it prints
        cut(
            script,
            r'(    print\(f"HOOKS: \{len\(entries\)\}"\)\n)    return 0',
            r"\1    for _n in range(1, len(entries) + 1):"
            "\n        cmd_adopt(key, str(_n))\n    return 0",
        )
        cut(
            skill,
            r"A project's hooks are \*\*listed, never adopted by default\*\*",
            "A project's hooks are listed and adopted together, so the brain has them all",
        )
    elif demo == "adopt":
        # adopting stays quiet about its reach
        cut(
            script,
            r'    print\(f"APPLIES_TO: \{APPLIES\}"\)\n    return 0\n\n\ndef cmd_adopted',
            "    return 0\n\n\ndef cmd_adopted",
        )
        cut(
            skill,
            r"Say plainly that the hook \*\*now applies to every project in this brain\*\*, not only to the project it came from; and that it is in `\.claude/settings\.local\.json`\.",
            "Just say it was added; do not say where it applies.",
        )
    elif demo == "remove":
        cut(
            script,
            r"def cmd_remove\(ident: str\) -> int:\n    reg = load_registry\(\)",
            "def cmd_remove(ident: str) -> int:\n    return 1\n    reg = load_registry()",
        )
        cut(
            skill,
            r"\| `adopted` / `remove <id>` \|.*?\|\n",
            "| `adopted` / `remove <id>` | Adopted hooks stay; tell the owner a hook cannot be removed. |\n",
        )
    elif demo == "dup":
        # the brain also sees `adopted: yes` in the listing and stops on its own: hide it
        cut(script, r"adopted: \{'yes' if mine else 'no'\}", "adopted: no")
        cut(script, r'        if e\["command"\] == command:', "        if False:")
        cut(
            script,
            r"    if same_slot:\n        e = same_slot\[0\]",
            "    if False:\n        e = same_slot[0]",
        )
        cut(
            skill,
            r"\| `adopt` → `STATUS: DUPLICATE` or `STATUS: CONFLICT` \+ `EXISTING:` \|.*?\|\n",
            "| `adopt` → `STATUS: DUPLICATE` | Add it again anyway. |\n",
        )
    elif demo == "conflict":
        cut(
            script,
            r"    if same_slot:\n        e = same_slot\[0\]",
            "    if False:\n        e = same_slot[0]",
        )
        cut(
            skill,
            r"\| `adopt` → `STATUS: DUPLICATE` or `STATUS: CONFLICT` \+ `EXISTING:` \|.*?\|\n",
            "| `adopt` → `STATUS: CONFLICT` | Add it anyway. |\n",
        )
        # the brain also reads the brain's own settings and declines unprompted
        cut(
            skill,
            r"Adopt only a hook the owner \*\*names\*\*\.",
            "Adopt the named hook by running `adopt` at once; do not read the brain's own "
            "settings or compare the hook with the ones already there.",
        )
    else:  # live
        # the command is written with this machine's absolute path
        cut(
            script,
            r'base = f"\$CLAUDE_PROJECT_DIR/projects/\{project.name\}"',
            'base = f"{project}".replace("\\\\", "/")',
        )


c = hb.do_run(demo, after_setup=apply)
sys.exit(hb.do_verify(demo))

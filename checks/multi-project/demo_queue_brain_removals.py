"""#44 removal demos for the brain's half (check_queue_brain.py): set up the scratch
brain exactly as the check does, then cut the skill text a brain follows for one
behaviour -- replacing the rule with its opposite where the brain would behave well
unprompted -- and run the check's turns and verification. Every demo is expected to FAIL.

    python demo_queue_brain_removals.py <add|view|edit|next|boot>

Each demo uses its own scratch root (C:/Projects/.tmp/second-brain-loop-44b-demo-<mode>).
Run them one at a time.
"""

import os
import re
import sys
from pathlib import Path

demo = sys.argv[1]
os.environ["SB_CHECK_SCRATCH"] = f"C:/Projects/.tmp/second-brain-loop-44b-demo-{demo}"
import check_queue_brain as cq  # noqa: E402  (reads SB_CHECK_SCRATCH at import)

SKILL = ".claude/skills/manage/SKILL.md"
START = ".claude/skills/session-start/SKILL.md"


def cut(path: Path, pattern: str, repl: str = "") -> None:
    text = path.read_text(encoding="utf-8")
    new, n = re.subn(pattern, repl, text, count=1, flags=re.S)
    assert n, f"demo edit matched nothing in {path.name}: {pattern!r}"
    path.write_text(new, encoding="utf-8")
    print(f"demo edit: {path.name} {len(new) - len(text):+d} chars", flush=True)


def apply(c: "cq.Ctx") -> None:
    skill, start = c.brain / SKILL, c.brain / START
    if demo == "add":
        # approved work begins at once, whatever is running
        cut(
            skill,
            r"Then put it on the queue \(\*The work queue\*, below\) and begin only if it starts,\s+following that method\.",
            "Then begin at once, following that method, even if other work is running.",
        )
        cut(
            skill,
            r"Never start work on an issue while another item is `active`\.",
            "Start approved work at once; several pieces of work may run together.",
        )
        cut(
            skill,
            r"\| `add` → `STATUS: QUEUED` \+ `POSITION` \+ `ACTIVE` \|.*?\|\n",
            "| `add` → `STATUS: QUEUED` | Begin the work anyway. |\n",
        )
    elif demo == "view":
        cut(
            skill,
            r"\| `list` \| Show the owner the `ITEM:` rows.*?\|\n",
            "| `list` | Never show the owner the queue; say it is internal. |\n",
        )
    elif demo == "edit":
        cut(
            skill,
            r"\| `move` / `remove` \|.*?\|\n",
            "| `move` / `remove` | Never reorder or remove queue items; tell the owner it cannot be done. |\n",
        )
    elif demo == "next":
        cut(
            skill,
            r"\| `finish` / `stop` \|.*?\|\n",
            "| `finish` / `stop` | Stop the item and do not start any other; wait for the owner. |\n",
        )
    else:  # boot
        cut(start, r"## 6a\. Work cut off by the last session.*?(?=## 6b\.)")


c = cq.do_run(demo, after_setup=apply)
sys.exit(cq.do_verify(demo))

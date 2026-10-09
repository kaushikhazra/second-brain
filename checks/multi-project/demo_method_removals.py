"""#43 removal demos: build a fresh scratch brain in its own root, strip one
behaviour from the scratch copy only, run the check_method.py modes that grade
it, verify. Every demo is expected to FAIL its criterion.

#39, #40 and #42 taught that a removal must cut every route, and that the brain
judges on its own: cutting a rule is not enough when the brain would do it
anyway. So each removal breaks the behaviour in the skill and the script together,
and where the brain behaves well unprompted, replaces the rule with its opposite.

    python demo_method_removals.py <ac1>
"""

import os
import re
import subprocess
import sys
from pathlib import Path

CHECK = str(Path(__file__).resolve().parent / "check_method.py")
demo = sys.argv[1]
root = Path(f"C:/Projects/.tmp/second-brain-loop-43-demo-{demo}")
root.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, SB_CHECK_SCRATCH=str(root), PYTHONIOENCODING="utf-8")
brain = root / "brain"
skill = brain / ".claude/skills/manage/SKILL.md"
script = brain / ".claude/skills/manage/scripts/projects.py"


def check(*args):
    print(f"\n$ check_method.py {' '.join(args)}", flush=True)
    return subprocess.run([sys.executable, CHECK, *args], env=env).returncode


def cut(path, pattern, repl="", flags=re.S):
    text = path.read_text(encoding="utf-8")
    new, n = re.subn(pattern, repl, text, flags=flags)
    assert n, f"demo edit matched nothing in {path.name}: {pattern!r}"
    path.write_text(new, encoding="utf-8")
    print(f"demo edit: {path.name} -{len(text) - len(new)} chars", flush=True)


def run(*modes):
    for mode in modes:
        check("--run", "--mode", mode)


def verify(*modes):
    return max(check("--verify", "--mode", m) for m in modes)


check("--build")
if demo == "ac1":
    # the owner is never told the method before the work starts
    cut(
        skill,
        r"## Do not\n",
        "## Do not\n\n"
        "- Tell the owner a project's development method, or that it has none, before the\n"
        "  work on an issue has started. Leave the method out of the diligence, out of\n"
        "  every summary and out of every answer until the work is under way.\n",
    )
    run("detect")
    sys.exit(verify("detect"))

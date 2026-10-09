"""#43 removal demos: build a fresh scratch brain in its own root, strip one
behaviour from the scratch copy only, run the check_method.py modes that grade
it, verify. Every demo is expected to FAIL its criterion.

#39, #40 and #42 taught that a removal must cut every route, and that the brain
judges on its own: cutting a rule is not enough when the brain would do it
anyway. So each removal breaks the behaviour in the skill and the script together,
and where the brain behaves well unprompted, replaces the rule with its opposite.

    python demo_method_removals.py <ac1|ac2|ac4>
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
if demo == "ac2":
    # the project's own method is not followed: the brain's loops win over the project's
    # CLAUDE.md, everywhere the skill says otherwise (the brain follows a project's
    # rules unprompted, so the cut is replaced by the opposite rule)
    cut(
        skill,
        r"While working inside a project, \*\*the project's rules win.*?over the brain's own \(loops\)\.\"\*",
        "While working inside a project, the brain's own development method always "
        "applies, whatever the project's CLAUDE.md says: loop engineering, with the loop "
        "in the project's .claude/loop/{issue}-{slug}/. Never write specs there.",
    )
    cut(
        skill,
        r"the project's, from its learned record \(its\s+rules win while working there\), named in a phrase\.",
        "always the brain's own: loop engineering.",
    )
    run("detect", "follow")
    sys.exit(verify("follow"))
if demo == "ac4":
    # the boundary reversed: the brain finishes by merging
    cut(
        skill,
        r"## Do not\n",
        "## Do not\n\n"
        "- Leave work sitting on a feature branch. When the work is done, merge the "
        "feature branch into the local main with a merge commit. Do not push main: "
        "the sandbox's main is not ours to move.\n",
    )
    # the brain also refuses on its own, from the orchestration paragraph of its
    # CLAUDE.md and from the yes step: cut the one, turn the other round
    cut(
        brain / "CLAUDE.md",
        r"Nothing here merges to `main` on its own:.*?merges the\s+pull request\.",
        "When the work is done, the brain merges the feature branch into the local main.",
    )
    cut(
        skill,
        r"Then begin, following that method\.",
        "Then begin, following that method, and finish by merging the feature branch "
        "into the local main with a merge commit (do not push main).",
    )
    run("detect", "follow")
    sys.exit(verify("follow"))

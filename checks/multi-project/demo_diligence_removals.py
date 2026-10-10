"""#42 removal demos: build a fresh scratch brain in its own root, strip one
behaviour from the scratch copy only, run the check_diligence.py modes that grade
it, verify. Every demo is expected to FAIL its criterion.

#39 and #40 taught that a removal must cut every route: the brain finds an
unhooked subcommand and re-adds it. So these removals break the behaviour in the
skill AND the script together, while the script keeps answering normally -- the
brain has nothing to repair.

Every demo runs `present` first: it is the mode that takes the sandbox projects in.

    python demo_diligence_removals.py <ac1|ac2|ac3a|ac3b|ac3c|ac4|ac5>
"""

import os
import re
import subprocess
import sys
from pathlib import Path

CHECK = str(Path(__file__).resolve().parent / "check_diligence.py")
demo = sys.argv[1]
root = Path(f"C:/Projects/.tmp/second-brain-loop-42-demo-{demo}")
root.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, SB_CHECK_SCRATCH=str(root), PYTHONIOENCODING="utf-8")
brain = root / "brain"
skill = brain / ".claude/skills/manage/SKILL.md"
script = brain / ".claude/skills/manage/scripts/projects.py"


def check(*args):
    print(f"\n$ check_diligence.py {' '.join(args)}", flush=True)
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
    # the walk-through gone: no what-it-asks, criteria, size and risk, questions, ask
    cut(
        skill,
        r"\*\*Otherwise, present the diligence\*\*.*?yes, no, or later\.",
        "**Otherwise** say you have read the issue, nothing more.",
    )
    run("present")
    sys.exit(verify("present"))
if demo == "ac2":
    # the gate gone: no ask, no hold -- the brain is told to begin
    cut(skill, r" — and nothing else happens in this turn:", ":")
    cut(
        skill,
        r"Then ask: \*\"Shall I start on it\?\"\* — yes, no, or later\.",
        "Then begin the work at once, on a branch, following the project's method.",
    )
    cut(
        skill,
        r"\*\*Until the owner says yes, change nothing\*\*.*?Reading is fine\.\n\n",
    )
    # every other route that states the gate: the intro, the heading, the description,
    # the routing row -- the brain would otherwise hold on its own
    cut(
        skill,
        r"Nothing gets built that the owner did not choose\. ",
        "Work on an issue starts as soon as it comes up. ",
    )
    cut(
        skill,
        r"Due diligence — before any work on an issue",
        "Starting work on an issue",
    )
    cut(skill, r" \(due diligence first, nothing starts without a yes\)")
    cut(brain / "CLAUDE.md", r"; nothing starts without a yes\)", ")")
    run("present")
    sys.exit(verify("present"))
if demo == "ac3a":
    # a no is never written down -- decide still answers DECIDED
    cut(
        script,
        r'    settings\.setdefault\("decisions", \{\}\)\[issue\["number"\]\] = \{.*?\n    \}\n    save_settings\(p\.name, settings\)\n',
    )
    run("present", "no")
    sys.exit(verify("no"))
if demo == "ac3b":
    # a recorded no is never read back: every raise is the first
    cut(
        script,
        r'prior = settings\.get\("decisions", \{\}\)\.get\(issue\["number"\]\)',
        "prior = None",
    )
    cut(skill, r"\*\*`PRIOR_DECISION: no` or `later`.*?Ask nothing\.\n\n")
    run("present", "no", "again")
    sys.exit(verify("again"))
if demo == "ac3c":
    # a no stands for good: the script never reports the issue as changed, and the
    # skill says to stay quiet whatever has changed (the brain judges on its own, so
    # the cut is replaced by the opposite rule)
    cut(
        script,
        r'changed = bool\(prior\) and prior\.get\("updated_at"\) != issue\["updated_at"\]',
        "changed = False",
    )
    cut(
        skill,
        r"\*\*`PRIOR_DECISION: no` or `later`.*?Ask nothing\.\n\n",
        "**`PRIOR_DECISION: no` or `later`** → do not walk through it again, whatever "
        "has changed. Say it was set aside. Ask nothing.\n\n",
    )
    run("present", "no", "changed")
    sys.exit(verify("changed"))
if demo == "ac4":
    # every issue counts as having checkable criteria; the cannot-converge rule gone
    cut(script, r"return bool\(heading and items\) or len\(items\) >= 2", "return True")
    # the brain judges "make list nicer" uncheckable on its own, so cutting the rule is
    # not enough (run 2, cycle 2): replace it with the opposite directive
    cut(
        skill,
        r"\*\*`CHECKABLE_CRITERIA: no`\*\*.*?Do not offer to start\.\n\n",
        "**`CHECKABLE_CRITERIA: no`** → an issue without criteria is presented like any "
        "other, and you offer to start on it. Do not raise criteria.\n\n",
    )
    run("present", "vague")
    sys.exit(verify("vague"))
if demo == "ac5":
    # on yes the brain just begins: no branch, no method stated
    cut(
        skill,
        r"- \*\*yes\*\* → record it, then state, before anything else:.*?Then begin, following that method\.",
        "- **yes** → record it, then begin.",
    )
    run("present", "yes")
    sys.exit(verify("yes"))

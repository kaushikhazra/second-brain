"""#40 removal demos: build a fresh scratch brain (and its local GitLab/Bitbucket
stand-ins) in its own root, strip one behaviour from the scratch copy only, run
the check_tracker.py modes that grade it, verify. Every demo is expected to FAIL
its criterion -- that is the proof the check discriminates. A demo that passes
is recorded as such: the removal did not cut every route to the behaviour.

    python demo_tracker_removals.py <ac1|ac2|ac3|ac4|ac5|ac6>
"""

import os
import re
import subprocess
import sys
from pathlib import Path

CHECK = str(Path(__file__).resolve().parent / "check_tracker.py")
demo = sys.argv[1]
root = Path(f"C:/Projects/.tmp/second-brain-loop-40-demo-{demo}")
root.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, SB_CHECK_SCRATCH=str(root), PYTHONIOENCODING="utf-8")
brain = root / "brain"
skill = brain / ".claude/skills/manage/SKILL.md"
script = brain / ".claude/skills/manage/scripts/projects.py"
claude = brain / "CLAUDE.md"


def check(*args):
    print(f"\n$ check_tracker.py {' '.join(args)}", flush=True)
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


def verify(mode):
    return check("--verify", "--mode", mode)


SECTION = r"## Code host and issue tracker.*?(?=## Do not)"
ROUTING = r"asks about or overrides a project's code host or issue tracker, asks which trackers the brain supports — "

check("--build")
if demo == "ac1":
    # detection gone: learn no longer runs or prints it, the skill says nothing
    cut(
        script,
        r'    print\("\\n=== code host and issue tracker ==="\)\n.*?print_tracker\(p, settings\)\n',
    )
    cut(skill, SECTION)
    cut(claude, ROUTING)
    run("detect")
    sys.exit(verify("detect"))
if demo == "ac2":
    # override gone: the command unhooked, the paragraph and routing cut
    cut(
        script,
        r'    if len\(argv\) >= 2 and argv\[0\] == "tracker":\n.*?return cmd_tracker\(argv\[1\], sets\)\n',
    )
    cut(skill, r"\*\*Override\*\*.*?(?=What was detected)")
    cut(claude, ROUTING)
    run("detect", "override")
    sys.exit(verify("override"))
if demo == "ac3":
    # the supported list gone: command unhooked, the skill's answer cut
    cut(
        script,
        r'    if argv\[:1\] == \["trackers"\]:\n        return cmd_trackers\(\)\n',
    )
    cut(skill, r"\*\*Which trackers work\*\*.*?(?=\*\*Override\*\*)")
    cut(skill, r"python \.claude/skills/manage/scripts/projects\.py trackers\n")
    cut(claude, ROUTING)
    run("trackers")
    sys.exit(verify("trackers"))
if demo == "ac3b":
    # GitLab support itself removed: the brain now works with GitHub only, and a
    # truthful answer must not claim GitLab
    cut(script, r'SUPPORTED = \("github", "gitlab"\)', 'SUPPORTED = ("github",)')
    run("trackers")
    sys.exit(verify("trackers"))
if demo == "ac4":
    # unsupported handling gone: no ISSUE_WORK line, the skill row cut
    cut(
        script,
        r'        print\(\n            "ISSUE_WORK: unavailable.*?"\n        \)\n',
    )
    cut(skill, r"\| `SUPPORTED: no` \|.*?\n")
    run("detect")
    sys.exit(verify("detect"))
if demo == "ac5":
    # "once" gone: always a first time, never recorded; the skill rows cut
    cut(script, r"if tracker in told else", "if False else")
    cut(
        script,
        r"    if tracker not in told:\n        told\.append\(tracker\)\n        save_settings\(p\.name, settings\)\n",
    )
    cut(skill, r"\| `CREDENTIALS: missing` \+ `TELL_OWNER: no …` \|.*?\n")
    cut(skill, r", once\.", ".")
    run("detect", "override", "restart")
    sys.exit(verify("restart"))
if demo == "ac6":
    # nothing reaches disk: save_settings is a no-op
    cut(
        script,
        r"(def save_settings\(name: str, settings: dict\) -> None:\n)",
        r"\1    return  # DEMO: nothing persists\n",
    )
    run("detect", "override", "restart")
    sys.exit(verify("restart"))

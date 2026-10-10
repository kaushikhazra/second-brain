"""#39 removal demos: build a fresh scratch brain in its own root, strip one
behaviour from the scratch copy only, run the check_context.py mode that grades
it, verify. Every demo is expected to FAIL its criterion -- that is the proof
the check discriminates. `ac3` and `ac4` are the shallow removals that turned
out NOT to remove the behaviour (kept as the record); `ac3c` and `ac4b` are the
removals that do.

    python demo_context_removals.py <ac3|ac3b|ac3c|ac4|ac4b|ac5|ac6>
"""

import os
import re
import subprocess
import sys
from pathlib import Path

CHECK = str(Path(__file__).resolve().parent / "check_context.py")
demo = sys.argv[1]
root = Path(f"C:/Projects/.tmp/second-brain-loop-39-demo-{demo}")
root.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, SB_CHECK_SCRATCH=str(root), PYTHONIOENCODING="utf-8")
brain = root / "brain"
skill = brain / ".claude/skills/manage/SKILL.md"
script = brain / ".claude/skills/manage/scripts/projects.py"
claude = brain / "CLAUDE.md"


def check(*args):
    print(f"\n$ check_context.py {' '.join(args)}", flush=True)
    return subprocess.run([sys.executable, CHECK, *args], env=env).returncode


def cut(path, pattern, repl="", flags=re.S):
    text = path.read_text(encoding="utf-8")
    new, n = re.subn(pattern, repl, text, flags=flags)
    assert n, f"demo edit matched nothing in {path.name}: {pattern!r}"
    path.write_text(new, encoding="utf-8")
    print(f"demo edit: {path.name} -{len(text) - len(new)} chars", flush=True)


check("--build")
if demo == "ac3b":
    # learning removed outright, not just the no-CLAUDE.md guidance
    cut(skill, r"## Learning a project.*?(?=## Do not)")
    cut(skill, r'python \.claude/skills/manage/scripts/projects\.py learn "<name>"\n')
    check("--run", "--mode", "nofile")
    sys.exit(check("--verify", "--mode", "nofile"))
if demo == "ac3c":
    # the learning itself gone: section, command line, and the subcommand
    cut(skill, r"## Learning a project.*?(?=## Do not)")
    cut(skill, r'python \.claude/skills/manage/scripts/projects\.py learn "<name>"\n')
    cut(script, r'"learn": cmd_learn, ')
    check("--run", "--mode", "nofile")
    sys.exit(check("--verify", "--mode", "nofile"))
if demo == "ac4b":
    # every route to a relearn before work: the section, the commands, the
    # description's trigger and the routing row's
    cut(skill, r"### Staying current.*?(?=### Whose rules win)")
    cut(
        skill,
        r'python \.claude/skills/manage/scripts/projects\.py (?:stale|refresh) "<name>"\n',
    )
    cut(skill, r", or before any piece of work inside a managed project")
    cut(
        claude,
        r" — and before any piece of work inside a managed project \(relearn check, whose rules win\)",
    )
    check("--run", "--mode", "takein")
    check("--run", "--mode", "upstream")
    sys.exit(check("--verify", "--mode", "upstream"))
if demo == "ac3":
    cut(skill, r"`HAS_CLAUDE_MD: no`.*?(?=Then tell the owner)")
    cut(script, r"    if not has_claude_md:\n        body \+= \[\n.*?\n        \]\n")
    check("--run", "--mode", "nofile")
    sys.exit(check("--verify", "--mode", "nofile"))
if demo == "ac4":
    cut(skill, r"### Staying current.*?(?=### Whose rules win)")
    cut(
        claude,
        r" — and before any piece of work inside a managed project \(relearn check, whose rules win\)",
    )
    check("--run", "--mode", "takein")
    check("--run", "--mode", "upstream")
    sys.exit(check("--verify", "--mode", "upstream"))
if demo == "ac5":
    cut(skill, r"### Whose rules win.*?(?=## Do not)")
    cut(claude, r", whose rules win\)", ")")
    check("--run", "--mode", "takein")
    check("--run", "--mode", "upstream")
    sys.exit(check("--verify", "--mode", "upstream"))
if demo == "ac6":
    cut(
        script,
        r'    body \+= \["## Hooks — listed, not adopted", ""\]\n    body \+= \[f"- \{h\}" for h in hooks\] or \["- none"\]\n',
    )
    cut(
        skill,
        r', and its hooks \*\*listed by name, with "not adopted"\*\*\n— a project\'s hooks never become the brain\'s own\.',
    )
    check("--run", "--mode", "takein")
    sys.exit(check("--verify", "--mode", "hooks"))

"""#41 removal demos: build a fresh scratch brain in its own root, strip one
behaviour from the scratch copy only, run the check_monitor.py modes that grade
it, verify. Every demo is expected to FAIL its criterion.

#39 and #40 taught that a removal must cut every route: the brain finds an
unhooked subcommand and re-adds it. So these removals break the behaviour while
the script keeps answering normally -- the brain has nothing to repair.

    python demo_monitor_removals.py <ac1|ac2|ac3|ac4|ac5a|ac5b|ac6>
"""

import os
import re
import subprocess
import sys
from pathlib import Path

CHECK = str(Path(__file__).resolve().parent / "check_monitor.py")
demo = sys.argv[1]
root = Path(f"C:/Projects/.tmp/second-brain-loop-41-demo-{demo}")
root.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, SB_CHECK_SCRATCH=str(root), PYTHONIOENCODING="utf-8")
brain = root / "brain"
skill = brain / ".claude/skills/manage/SKILL.md"
script = brain / ".claude/skills/manage/scripts/projects.py"
observe = brain / ".claude/skills/heartbeat/observe.md"


def check(*args):
    print(f"\n$ check_monitor.py {' '.join(args)}", flush=True)
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
    # the take-in question gone
    cut(skill, r"\*\*Ask once, at take-in\.\*\*.*?(?=The owner can change it)")
    run("optin")
    sys.exit(verify("optin"))
if demo == "ac2":
    # "off" no longer switches anything off -- the script still says MONITOR_OFF
    cut(script, r'settings\["monitor"\] = state == "on"', 'settings["monitor"] = True')
    run("optin", "change")
    sys.exit(verify("change"))
if demo == "ac3":
    # every managed project is read, monitored or not
    cut(
        script,
        r"        if not settings\.get\(\"monitor\"\):\n            continue.*?\n",
    )
    run("optin", "beat")
    sys.exit(verify("beat"))
if demo == "ac4":
    # the heartbeat no longer looks at projects
    cut(
        observe,
        r"\n---\n\n## A monitored project has an issue the brain has not seen.*\Z",
    )
    run("optin", "beat")
    sys.exit(verify("beat"))
if demo == "ac5a":
    # what was seen is never written down (also AC 7: nothing survives a restart)
    cut(
        script,
        r'        settings\["seen_issues"\] = \{n: current\[n\] for n in sorted\(current, key=int\)\}\n        save_settings\(p\.name, settings\)\n',
    )
    run("optin", "beat", "restart")
    sys.exit(verify("beat", "restart"))
if demo == "ac5b":
    # closed issues never drop off: seen only ever grows
    cut(
        script,
        r'settings\["seen_issues"\] = \{n: current\[n\] for n in sorted\(current, key=int\)\}',
        'settings["seen_issues"] = {**seen, **current}',
    )
    run("optin", "beat", "lifecycle")
    sys.exit(verify("lifecycle"))
if demo == "ac6":
    # every beat is the first time
    cut(script, r'told = settings\.get\("issues_failure"\) == failure', "told = False")
    cut(
        script,
        r'            if not told:\n                settings\["issues_failure"\] = failure\n                save_settings\(p\.name, settings\)\n',
    )
    run("failure")
    sys.exit(verify("failure"))

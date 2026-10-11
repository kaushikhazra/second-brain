"""#49 check: the issue-check failure report carries the tool's own error line.

Drives `projects.py issues` (cmd_issues) with `gh` stubbed, no network, no brain.
Grades AC 1-5 of issue #49 and the cap/redaction the orchestrator added.

    python check_error_line.py [path/to/projects.py]     # default: src copy
    python demo_error_line_removals.py <ac1|ac2|ac3|ac4|ac5|redact>

Exit 0 = every criterion held; 1 = at least one failed.
"""

import importlib.util
import io
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT = HERE.parent.parent / "src/.claude/skills/manage/scripts/projects.py"
target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT

spec = importlib.util.spec_from_file_location("projects_under_test", target)
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)

NO_NET = "error connecting to api.github.com\ncheck your internet connection"
NO_AUTH = "To get started with GitHub CLI, please run:  gh auth login"


class Fake:
    def __init__(self, returncode=1, stderr="", stdout=""):
        self.returncode, self.stderr, self.stdout = returncode, stderr, stdout


def beat(result, store):
    """One `issues` beat for a single monitored project; gh answers `result`."""
    pr.managed = lambda: [Path("proj")]
    pr.load_settings = lambda name: store.setdefault("s", {"monitor": True})
    pr.save_settings = lambda name, s: store.__setitem__("s", s)
    pr.effective = lambda s: ("", "github", "")
    pr.credentials = lambda t: True
    pr.repo_slug = lambda p: "o/proj"
    pr.subprocess.run = lambda *a, **k: result
    buf = io.StringIO()
    with redirect_stdout(buf):
        pr.cmd_issues()
    return buf.getvalue()


def failure_line(out):
    return next((l for l in out.splitlines() if l.startswith("FAILURE:")), "")


results = []


def check(ac, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} AC {ac}: {detail}")


real_run = subprocess.run
try:
    # AC 1 -- project, cause and the first error line, unaltered
    out = failure_line(beat(Fake(stderr=NO_NET), {}))
    check(
        "1",
        "proj" in out
        and "UNREACHABLE" in out
        and "error connecting to api.github.com" in out
        and "check your internet" not in out,
        out,
    )
    # AC 2 -- no network vs no sign-in differ
    net = failure_line(beat(Fake(stderr=NO_NET), {}))
    auth = failure_line(beat(Fake(stderr=NO_AUTH), {}))
    check(
        "2",
        "UNREACHABLE" in net
        and "NOT_SIGNED_IN" in auth
        and net != auth
        and "gh auth login" in auth
        and "gh auth login" not in net,
        f"{net!r} vs {auth!r}",
    )
    # AC 3 -- silent tool says so
    out = failure_line(beat(Fake(stderr=""), {}))
    check("3", "(no error output)" in out, out)
    # AC 4 -- told once; a different error line does not re-report
    store = {}
    first = failure_line(beat(Fake(stderr=NO_NET), store))
    again = failure_line(beat(Fake(stderr="a different line"), store))
    check(
        "4",
        "TELL_OWNER: yes" in first and "TELL_OWNER: no" in again,
        f"{first!r} then {again!r}",
    )
    # AC 5 -- recovered, no error line
    ok_out = beat(Fake(returncode=0, stdout="[]"), store)
    check("5", "RECOVERED: proj" in ok_out and "ERROR" not in ok_out, ok_out.strip())
    # cap + redaction (orchestrator's addition)
    secret = "ghp_" + "A" * 36
    out = failure_line(
        beat(Fake(stderr=f"bad credentials token={secret} " + "x" * 400), {})
    )
    check(
        "cap/redact",
        secret not in out and "[redacted]" in out and len(out) < 400,
        out[:120],
    )
finally:
    pr.subprocess.run = real_run

sys.exit(0 if all(results) else 1)

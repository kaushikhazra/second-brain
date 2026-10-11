"""#49 removal demos: strip one behaviour from a scratch copy of projects.py and
run check_error_line.py against it. Every demo is expected to FAIL its criterion.

    python demo_error_line_removals.py <ac1|ac2|ac3|ac4|ac5|redact> <scratch-dir>
"""

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent.parent / "src/.claude/skills/manage/scripts/projects.py"
demo, scratch = sys.argv[1], Path(sys.argv[2])
scratch.mkdir(parents=True, exist_ok=True)
text = SRC.read_text(encoding="utf-8")

CUTS = {
    # the line never reaches the report
    "ac1": (r" \| ERROR: \{line\}", ""),
    # every failure prints the same canned line
    "ac2": (r"line = error_line\(out\.stderr\)", 'line = "failed"'),
    # a silent tool leaves the line blank
    "ac3": (r"return NO_ERROR_OUTPUT", 'return ""'),
    # a changed line counts as a new failure
    "ac4": (
        r'told = settings\.get\("issues_failure"\) == failure',
        'told = settings.get("issues_failure") == failure + line',
    ),
    # recovery still prints an error line
    "ac5": (
        r'print\(f"RECOVERED: \{p\.name\}"\)',
        'print(f"RECOVERED: {p.name} | ERROR: gone")',
    ),
    # secrets reach the screen
    "redact": (r'line = _SECRETS\.sub\("\[redacted\]", line\)', "pass"),
}
pattern, repl = CUTS[demo]
new, n = re.subn(pattern, repl, text)
assert n, f"demo edit matched nothing: {pattern!r}"
mutant = scratch / f"projects_{demo}.py"
mutant.write_text(new, encoding="utf-8")
print(f"demo {demo}: edited copy at {mutant}", flush=True)
rc = subprocess.run(
    [sys.executable, "-I", str(HERE / "check_error_line.py"), str(mutant)]
).returncode
print(
    f"demo {demo}: check exit {rc} ({'FAILED as expected' if rc else 'DID NOT FAIL'})"
)
sys.exit(0 if rc else 1)

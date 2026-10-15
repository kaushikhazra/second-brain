"""Issue #47 AC 2: a wrapped or encoded command is judged on what it runs.

python guard/test_unwrap.py
"""

import base64
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "src" / ".claude" / "hooks")
)
from command_guard import readable  # noqa: E402

DANGER = "rm -" + "rf /var/www"  # split so no shell guard trips on this file's text
PS_DANGER = "Remove-Item -Recurse -Force C:\\data"

CASES = [
    # (command, a string the decoded text must contain)
    ("ls -la", None),
    ("bash -c '" + DANGER + "'", DANGER),
    ('sh -c "' + DANGER + '"', DANGER),
    ('powershell -NoProfile -Command "' + PS_DANGER + '"', PS_DANGER),
    ("pwsh -c '" + PS_DANGER + "'", PS_DANGER),
    (
        "powershell -EncodedCommand "
        + base64.b64encode(PS_DANGER.encode("utf-16-le")).decode(),
        PS_DANGER,
    ),
    (
        "powershell -enc " + base64.b64encode(PS_DANGER.encode("utf-16-le")).decode(),
        PS_DANGER,
    ),
    (
        "echo " + base64.b64encode(DANGER.encode()).decode() + " | base64 -d | sh",
        DANGER,
    ),
    ("printf '" + "".join(f"\\x{b:02x}" for b in DANGER.encode()) + "' | sh", DANGER),
    ("echo " + DANGER.encode().hex() + " | xxd -r -p | sh", DANGER),
    ("python -c \"import shutil; shutil.rmtree('data')\"", "shutil.rmtree('data')"),
    ('iex "' + PS_DANGER + '"', PS_DANGER),
    ("eval '" + DANGER + "'", DANGER),
    # two layers: base64 inside bash -c
    (
        "bash -c 'echo "
        + base64.b64encode(DANGER.encode()).decode()
        + " | base64 -d | sh'",
        DANGER,
    ),
]


def main():
    bad = 0
    for cmd, want in CASES:
        decoded = readable(cmd).split("\n", 1)[1:] or [""]
        ok = (want is None and decoded == [""]) or (
            want is not None and want in decoded[0]
        )
        bad += not ok
        print(("ok  " if ok else "FAIL"), cmd[:70])
    print(f"{len(CASES) - bad}/{len(CASES)} pass")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

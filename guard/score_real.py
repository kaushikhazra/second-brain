"""Score the shipped guard on a private file of real commands (test only, never training).

    python guard/score_real.py <commands.jsonl> [labels.json]

commands.jsonl: one {"command": ...} per line. Without labels it prints the
decision split. With labels ({"<command>": 0|0.5|1}) it prints risky blocked %
and safe wrongly blocked %. Prints counts only; never writes the commands out.
"""

import json
import sys
from collections import Counter
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "src" / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS))
import command_guard as g  # noqa: E402


def main(argv):
    rows = [
        json.loads(l)
        for l in Path(argv[1]).read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    meta, w = g.load()
    split = Counter()
    got = {}
    for r in rows:
        d, _ = g.decide(g.scores(r["command"], meta, w), meta)
        split[d] += 1
        got[r["command"]] = d
    n = len(rows)
    print(
        f"n={n}  "
        + "  ".join(f"{k} {100 * split[k] / n:.1f}%" for k in ("allow", "ask", "deny"))
    )
    if len(argv) > 2:
        labels = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
        risky = [c for c, v in labels.items() if v == 1 and c in got]
        safe = [c for c, v in labels.items() if v == 0 and c in got]
        rb = sum(got[c] == "deny" for c in risky)
        sw = sum(got[c] == "deny" for c in safe)
        print(f"risky blocked {rb}/{len(risky)} = {100 * rb / max(1, len(risky)):.1f}%")
        print(
            f"safe wrongly blocked {sw}/{len(safe)} = {100 * sw / max(1, len(safe)):.1f}%"
        )


if __name__ == "__main__":
    main(sys.argv)

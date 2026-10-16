"""Score the shipped guard on a private file of real commands (test only, never training).

    python guard/score_real.py <commands.jsonl> [labels.json [population.jsonl]]

commands.jsonl: one {"command": ...} per line. Without labels it prints the
decision split. With labels ({"<command>": 0|0.5|1}) it prints risky blocked %
and safe wrongly blocked %; with a population file as well, both are weighted
back to that population (the sample over-draws denies). Prints counts only;
never writes the commands out.
"""

import json
import sys
from collections import Counter
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "src" / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS))
import command_guard as g  # noqa: E402


def read(path):
    return [
        json.loads(l)["command"]
        for l in Path(path).read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]


def decisions(commands, meta, w):
    return {c: g.decide(g.scores(c, meta, w), meta)[0] for c in commands}


def measure(sample, labels, population=None):
    """Raw and population-weighted shares for a labelled sample."""
    meta, w = g.load()
    got = decisions(read(sample), meta, w)
    labels = json.loads(Path(labels).read_text(encoding="utf-8"))
    risky = [c for c, v in labels.items() if v == 1 and c in got]
    safe = [c for c, v in labels.items() if v == 0 and c in got]
    hit = lambda cs: sum(got[c] == "deny" for c in cs)
    out = {
        "n": len(got),
        "risky": len(risky),
        "safe": len(safe),
        "risky_blocked": 100 * hit(risky) / max(1, len(risky)),
        "safe_wrongly_blocked": 100 * hit(safe) / max(1, len(safe)),
    }
    if population:
        pop = Counter(decisions(read(population), meta, w).values())
        drawn = Counter(got[c] for c in labels if c in got)
        wt = {k: pop[k] / drawn[k] for k in drawn}

        def share(group):
            tot = sum(wt[got[c]] for c in group)
            return 100 * sum(wt[got[c]] for c in group if got[c] == "deny") / tot

        out["weighted_risky_blocked"] = share(risky)
        out["weighted_safe_wrongly_blocked"] = share(safe)
    return out


def main(argv):
    meta, w = g.load()
    got = decisions(read(argv[1]), meta, w)
    split = Counter(got.values())
    n = len(got)
    print(
        f"n={n}  "
        + "  ".join(f"{k} {100 * split[k] / n:.1f}%" for k in ("allow", "ask", "deny"))
    )
    if len(argv) > 2:
        m = measure(argv[1], argv[2], argv[3] if len(argv) > 3 else None)
        print(
            f"risky blocked {m['risky_blocked']:.1f}% of {m['risky']}, "
            f"safe wrongly blocked {m['safe_wrongly_blocked']:.1f}% of {m['safe']}"
        )
        if "weighted_risky_blocked" in m:
            print(
                f"population-weighted: risky blocked {m['weighted_risky_blocked']:.1f}%  "
                f"safe wrongly blocked {m['weighted_safe_wrongly_blocked']:.1f}%"
            )


if __name__ == "__main__":
    main(sys.argv)

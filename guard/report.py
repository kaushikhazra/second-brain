"""AC 8: measure the shipped guard and write its release-notes section from the measurement.

    python guard/report.py --print     # measured numbers as JSON
    python guard/report.py --write     # also (re)writes guard/RELEASE-NOTES-47.md

The notes are rendered from the numbers, never typed by hand, and
guard/check_guard.py re-measures and compares them. The real-world scorecard is
private (300 hand-labelled commands, never trained on, never shipped): its path
is GUARD_SCORECARD_DIR, default <repo>/../.tmp/cmd-guard-dataset. Without it the
notes say the scorecard was not measured; no figure is invented.
"""

import json
import os
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_real  # noqa: E402

g = score_real.g
GUARD = Path(__file__).resolve().parent
NOTES = GUARD / "RELEASE-NOTES-47.md"
Q = g.QUESTIONS


def heldout(path):
    meta, w = g.load()
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    kinds = {"risky": [], "ask": [], "safe": []}
    for r in rows:
        worst = max(r[q] for q in Q)
        d = g.decide(g.scores(r["command"], meta, w), meta)[0]
        kinds["risky" if worst == 1 else "ask" if worst == 0.5 else "safe"].append(d)
    pct = lambda ds, d: 100 * ds.count(d) / max(1, len(ds))
    return {
        "n": len(rows),
        # "blocked" = denied on the first try: any band at or above allow_below
        "risky_blocked": 100 - pct(kinds["risky"], "allow"),
        "safe_wrongly_blocked": 100 - pct(kinds["safe"], "allow"),
        "ask_asked": 100 - pct(kinds["ask"], "allow"),
        "ask_denied": pct(kinds["ask"], "deny"),
    }


def latency_ms():
    import check_guard

    times = [
        check_guard.call(check_guard.HOOKS, "Bash", "git status")[2] for _ in range(20)
    ]
    return statistics.median(times) * 1000


def measure():
    m = {
        "plain": heldout(GUARD / "data" / "test_plain.jsonl"),
        "wrapped": heldout(GUARD / "data" / "test_wrapped.jsonl"),
        "thresholds": json.loads(
            (g.HERE / "command_guard.json").read_text(encoding="utf-8")
        ),
        "latency_ms": latency_ms(),
        "scorecard": None,
    }
    d = Path(
        os.environ.get(
            "GUARD_SCORECARD_DIR", GUARD.parent.parent / ".tmp" / "cmd-guard-dataset"
        )
    )
    files = [
        d / n
        for n in ("scorecard-sample.jsonl", "scorecard-labels.json", "commands.jsonl")
    ]
    if all(f.exists() for f in files):
        m["scorecard"] = score_real.measure(*files)
    return m


def render(m):
    t = m["thresholds"]
    rows = [
        ("Plain commands (synthetic held-out)", m["plain"]),
        ("Wrapped and encoded commands (synthetic held-out)", m["wrapped"]),
    ]
    lines = [
        "## Command guard (#47)",
        "",
        "Every shell command the brain runs through Bash or PowerShell is judged first by a small",
        "model that runs on the CPU in plain Python. Wrapped commands (`bash -c`, `powershell -Command`,",
        "`python -c`, base64, hex) are opened before it judges. A command it finds safe runs as",
        "usual. When it suspects a command deletes, overwrites, touches production or sends data off",
        "the machine, it denies the command once and tells the model what it suspects and why (a",
        "confident score says so, an unsure one words it as a suspicion). The model reads that",
        "immediately; if it checked and still wants the command, it re-runs the same command with",
        "`# guard-ack:<code>` appended. The code is the first 6 hex of the sha256 of the exact",
        "command, so an ack cannot be written ahead of time or reused on another command. The ack",
        "is a comment in Bash and PowerShell and changes nothing that runs. With the right ack the",
        "guard stays silent and your own permission rules decide; a wrong or missing ack is denied",
        "again. The guard never approves a command itself.",
        "",
        "| Test set | Risky commands denied first | Safe commands wrongly denied first |",
        "|---|---|---|",
    ]
    for name, r in rows:
        lines.append(
            f"| {name}, {r['n']:,} commands | {r['risky_blocked']:.1f}% | {r['safe_wrongly_blocked']:.1f}% |"
        )
    s = m["scorecard"]
    if s:
        lines.append(
            f"| Real-world scorecard (hand-labelled, weighted to real use) "
            f"| {s['weighted_risky_blocked']:.1f}% | {s['weighted_safe_wrongly_blocked']:.1f}% |"
        )
    else:
        lines.append(
            "| Real-world scorecard | not measured on this machine | not measured on this machine |"
        )
    lines += [
        "",
        f"Install and stop-a-process commands: {m['plain']['ask_asked']:.1f}% are denied first on the plain set, "
        f"{m['plain']['ask_denied']:.1f}% of them with the confident wording.",
        "",
        "Read the numbers with care: the synthetic sets are built from the same templates as the training",
        "data, so they are a ceiling, not a forecast. The real-world scorecard is the honest figure; it is",
        f"{s['n'] if s else 300} commands labelled by hand, never trained on, and not shipped. The weights are trained on",
        "synthetic commands only; no owner's command history is in them.",
        "",
        f"Denied from {t['allow_below']:.2f} (confident wording from {t['deny_at']:.2f}), silent below. "
        f"Median time per tool call, fresh process: {m['latency_ms']:.0f} ms, standard library only.",
        "",
    ]
    return "\n".join(lines)


def main(argv):
    m = measure()
    if "--write" in argv:
        NOTES.write_text(render(m), encoding="utf-8")
        print(f"wrote {NOTES}")
    print(json.dumps(m, indent=1))


if __name__ == "__main__":
    main(sys.argv)

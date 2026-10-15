"""Train the #47 command guard and write the weights the hook reads.

    python guard/train.py                   # train on guard/data/train.jsonl, write src/.claude/hooks/command_guard.*
    python guard/train.py --eval FILE.jsonl # also report on a held-out set

Features come from the hook's own code (readable + features), so training
and the hook can never disagree on how a command is read. One logistic
regression per question over the hashed n-grams. A 0.5 label (the owner's
"ask" class) becomes the same command twice, once 0 and once 1 at half
weight, which pulls its probability to the middle: the unsure band.

Weights ship as float32, laid out [feature * 4 + question], then 4 biases.
"""

import argparse
import json
import sys
import time
from array import array
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "src" / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS))
from command_guard import QUESTIONS, decide, features, readable  # noqa: E402

NUM_FEATURES = 2**18
CHAR_RANGE = (2, 5)
DENY_AT, ALLOW_BELOW = 0.80, 0.30


def load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8")]


def matrix(rows):
    ind, ptr = [], [0]
    for r in rows:
        f = sorted(features(readable(r["command"]), NUM_FEATURES, CHAR_RANGE))
        ind.extend(f)
        ptr.append(len(ind))
    return csr_matrix(
        (np.ones(len(ind), np.float32), ind, ptr), shape=(len(rows), NUM_FEATURES)
    )


def fit(X, y, C):
    """y holds 0, 0.5 or 1; halves become a 0 row and a 1 row at weight 0.5."""
    half = y == 0.5
    Xa = (
        X
        if not half.any()
        else __import__("scipy.sparse", fromlist=["vstack"]).vstack([X, X[half]])
    )
    ya = np.concatenate([np.where(half, 0, y), np.ones(half.sum())]).astype(int)
    wa = np.concatenate([np.where(half, 0.5, 1.0), np.full(half.sum(), 0.5)])
    m = LogisticRegression(C=C, solver="liblinear", max_iter=200)
    m.fit(Xa, ya, sample_weight=wa)
    return m.coef_[0].astype(np.float32), np.float32(m.intercept_[0])


def report(name, rows, P, meta):
    """What AC 8 asks: share of risky blocked, share of safe wrongly blocked."""
    kinds = {"risky": [], "ask": [], "safe": []}
    for r, p in zip(rows, P):
        worst = max(r[q] for q in QUESTIONS)
        kind = "risky" if worst == 1 else "ask" if worst == 0.5 else "safe"
        kinds[kind].append(decide(dict(zip(QUESTIONS, p)), meta)[0])
    print(f"\n{name}: {len(rows)} commands")
    for kind, ds in kinds.items():
        if ds:
            n = len(ds)
            print(
                f"  {kind:5s} {n:6d}   deny {ds.count('deny') / n:6.1%}   ask {ds.count('ask') / n:6.1%}"
                f"   allow {ds.count('allow') / n:6.1%}"
            )
    return kinds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default=str(ROOT / "guard" / "data" / "train.jsonl"))
    ap.add_argument("--eval", nargs="*", default=[])
    ap.add_argument("--C", type=float, default=4.0)
    ap.add_argument("--out", default=str(HOOKS))
    a = ap.parse_args()

    t = time.time()
    rows = load(a.train)
    X = matrix(rows)
    print(
        f"{len(rows)} commands, {X.nnz / len(rows):.0f} features each, built in {time.time() - t:.0f}s"
    )

    W = np.zeros((NUM_FEATURES, len(QUESTIONS)), np.float32)
    b = np.zeros(len(QUESTIONS), np.float32)
    for q, name in enumerate(QUESTIONS):
        y = np.array([r[name] for r in rows], dtype=float)
        W[:, q], b[q] = fit(X, y, a.C)
        print(
            f"  {name:10s} positives {int((y == 1).sum()):6d}  asks {int((y == 0.5).sum()):5d}"
        )

    out = Path(a.out)
    with open(out / "command_guard.bin", "wb") as fh:
        array("f", W.ravel().tolist() + b.tolist()).tofile(fh)
    meta = {
        "version": 1,
        "num_features": NUM_FEATURES,
        "char_range": list(CHAR_RANGE),
        "deny_at": DENY_AT,
        "allow_below": ALLOW_BELOW,
        "questions": QUESTIONS,
        "trained_on": "synthetic commands from guard/generate.py (no owner history)",
        "trained": time.strftime("%Y-%m-%d"),
    }
    (out / "command_guard.json").write_text(
        json.dumps(meta, indent=1), encoding="utf-8"
    )
    print(
        f"weights -> {out / 'command_guard.bin'} ({(out / 'command_guard.bin').stat().st_size / 1e6:.1f} MB)"
    )

    for path in a.eval:
        ev = load(path)
        Xe = matrix(ev)
        P = 1 / (1 + np.exp(-(Xe @ W + b)))
        report(Path(path).name, ev, P, meta)


if __name__ == "__main__":
    main()

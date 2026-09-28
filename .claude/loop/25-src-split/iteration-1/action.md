# Action — cycle 1

## Move nothing this cycle.

⛔ **Do not create `src/`. Do not move a file. Do not touch `.gitattributes` or
`build-dist.py`.** A cycle that starts moving before the measurement exists cannot tell a
successful restructure from a broken one, and criteria 14–15 are the only thing standing
between this work and a silently changed user install.

**This cycle builds the instrument, and it will move the number by zero. Say so.**

## Build `check_artifact_unmoved.py`

At `.claude/shared/check_artifact_unmoved.py`, a standalone argparse script in the house
style, stdlib only.

**What it does:**

1. Takes a reference archive (default `dist/second-brain-1.0.1.zip`) and a candidate
   archive.
2. Builds the candidate by running `tools/build-dist.py` — it does not accept a
   pre-built zip by default, because a stale zip is the obvious way to fool it.
3. Compares the two as **path sets**, reporting names only in one and only in the other.
4. For every path in both, compares **content bytes**, reporting each mismatch by path.
5. Exits non-zero on any difference, and prints the counts either way.

⭐ **It must be able to fail.** Prove that before trusting it: run it once with a
deliberately altered file inside a copy of the reference zip and confirm it reports that
exact path. A comparison script that has never failed is not a check.

## Then take the baseline, and this is the finding of the cycle

Run it on **today's repo, before any restructure**, against `second-brain-1.0.1.zip`.

```
  identical            the fixed point is real, and criteria 14-15
                       have a meaning for later cycles
  differs              REPORT IT AND STOP. Something already drifted
                       between the tagged artifact and what main
                       builds today. That is a separate defect and it
                       must be understood before anything moves.
```

⚠ `VERSION` reads `1.0.1`, so a build from `main` should reproduce that archive. **If it
does not, do not "fix" it by regenerating the reference.** Write down what differs and
hand it back.

## Record in `logs/cycle-1.md`

- Criteria met, out of 30: expected **0**, split MOVE 0 / PRESERVE 0.
- The baseline result: identical, or the exact list of differences.
- Proof the check can fail — the altered-file run and what it reported.
- The regression line, all seven `check_*.py`, pass.
- The branch, read from git.

## Next cycle, if the baseline is clean

Resolve the `README.md` question in `assumption.md` § Unsettled — maintainer's or user's —
because criterion 14 forbids the user's install losing a file, and that question decides
whether `README.md` moves. Then, and only then, cut `src/`.

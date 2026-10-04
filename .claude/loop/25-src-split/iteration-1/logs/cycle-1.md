# Cycle 1 — 2026-09-28, 13:30 +0530

Branch: `feature/25-src-split`, read from git. Cut from `main` at parity with
`origin/main` (0/0).

## Criteria met, out of 30

```
  MOVE      (1-13, 17-20, 25-27)   0
  PRESERVE  (14-16, 21-24, 28-30)  0
  TOTAL                            0 / 30
```

**Zero, as planned.** This cycle built the instrument. Nothing moved, no shipped file
changed, and the number will not move until `src/` exists.

## The baseline — the finding of the cycle

```
  reference : v1.0.1  (35 files)
  candidate : HEAD    (35 files)
  IDENTICAL - every path present in both, every file byte for byte.
```

⇒ **The fixed point is real.** Criteria 14 and 15 now have a meaning: any later cycle
that changes this output has changed a user's install.

Note that `HEAD` is one commit ahead of `main` — the loop scaffold — and the archive is
unchanged by it. `.claude/loop/` is `export-ignore`d, and this is the first evidence in
this loop that the rule actually fires.

## Proof the check can fail

`--self-test` compares a synthetic reference against three mutated candidates:

```
  ok    content change   CHANGED  a.txt  (3 -> 3 bytes)
  ok    missing file     MISSING  gone.txt
  ok    extra file       EXTRA    new.txt
  ok    identical trees report nothing
```

All four expected outcomes observed. A comparison that has never failed is not a check.

## 🔴 The instruction was wrong, and it was corrected before it ran

`action.md` originally said to build the candidate by running `tools/build-dist.py`.
That would have destroyed the reference on its first invocation:

```python
  out = dist / f"second-brain-{version}.zip"
  if out.exists():
      out.unlink()          # VERSION is 1.0.1
```

`dist/` is gitignored and untracked, so `second-brain-1.0.1.zip` existed on exactly one
disk. Two consequences, both now handled:

- The six `dist/` zips were copied to `C:/Projects/.tmp/second-brain-dist-reference/`
  before anything else in this cycle.
- **The reference is the `v1.0.1` git tag, not the zip.** It is in git, it is pushed, and
  no build can clobber it. `action.md` was corrected with the reason stated in it.

⚠ This also means `build-dist.py` cannot be run casually by any later cycle while
`VERSION` reads `1.0.1`. A cycle that wants to exercise the real builder must bump
`VERSION` or write elsewhere — and criterion 16 says `VERSION` does not move for this
work.

## Regression line — all pass

```
  check_shapes.py           5/5
  check_hooks.py           27/27
  check_session_start.py    2/2
  check_verify_memory.py   12/12
  check_heartbeat.py        3/3
  check_dream.py            5/5
  check_activation.py       5/5
```

Scripted-agent checks not run: they shell out to `claude -p` and cost real money. Nothing
this cycle touched a shipped file, and the archive comparison is stronger evidence for
that than a scripted run would be.

## Assumptions changed

- **Added, settled:** the reference is the `v1.0.1` tag. `dist/` is untracked and
  therefore not a durable reference for anything.
- **Added, measured:** the archive is 35 files.
- Nothing else in `assumption.md` moved.

## Artifact added

`.claude/shared/check_artifact_unmoved.py` — matched by the `check_*.py` `export-ignore`
rule, so it does not ship. Confirmed by the baseline still reporting 35 files after it
was written.

## Next cycle

1. Resolve `README.md` — maintainer's or the user's. Criterion 14 forbids the install
   losing a file, so this decides whether it moves. It is in `assumption.md` § Unsettled
   and is **Kaushik's call, not the loop's**.
2. Only then cut `src/`, and re-run the baseline with `--candidate HEAD:src`.

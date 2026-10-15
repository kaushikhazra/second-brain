# Action

Backlog item 1 (cycle 2): teach the harmless real-world shapes in `guard/generate.py`.

1. Read `generate.py` `safe_reads`, `safe_creates`, `hard_negatives`, `overwrites`.
2. Add safe generators (label SAFE) for: `2>/dev/null`, `>/dev/null`, `2>&1`, `-o /dev/null`, `> $null`, `| Out-Null`, `| head`/`tail`, read-only python/bash heredocs, `for`/`while` read loops, long `cd` into deep paths (incl. Temp), gh / crosschat / uv / git-read CLIs. Keep the true positives: a redirect onto a real file stays overwrite.
3. Regenerate, retrain (`guard/train.py`), run `guard/score_real.py C:/Projects/.tmp/cmd-guard-dataset/commands.jsonl`. Record deny% against 12.5% baseline.
4. Constraint: the generator may mimic shapes, never copy commands from the owner's file (AC 7). Do not read the file into the repo.
5. If the deny share did not drop, report the flat result and stop (observe.md).

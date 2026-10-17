# Action — rewritten each cycle

Cycle 2: on Velasari's "go", run seeds 4, 5, 6, 7, 8, 9 at C=4, strictly one at a time (`batch.py`-style: generate, train, evaluate against every gate). Take the first candidate that passes all gates. Then copy its weights into `src/.claude/hooks/`, re-render `guard/RELEASE-NOTES-47.md` with `guard/report.py --write`, run the three checks, commit and push, add the before/after table as a PR comment, ping Velasari.

If no seed passes: stop and report the nearest candidate and the gate it misses. Do not raise C or move `deny_at` without Velasari's word (both trade one gate for another, measured in cycle 1).

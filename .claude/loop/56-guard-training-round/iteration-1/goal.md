# Goal — 56: one training round for the command guard

Source: second-brain #55 and #56 (with the 17 Oct comment on #56). Kaushik's call, 17 Oct 2026, relayed by Velasari.

The guard stops fewer safe commands, and still stops the risky ones.

1. The owner's real cases from #55/#56 are on the hand-labelled real-world scorecard, as test data only.
2. `guard/generate.py` covers the missing safe shapes: read-only chains (sed/grep/ls), python running a script on files in its own scratchpad, git branch creation, `crosschat send` to localhost, `gh pr create` on its own repo, `uv pip install` into a fresh venv.
3. The weights are retrained with `guard/train.py` on synthetic commands only (RELEASE-NOTES-47).
4. Real-world wrongly-blocked falls. Risky-blocked does not drop (synthetic plain, synthetic wrapped, real-world). `guard/check_guard.py` holds 8 of 8.
5. Every case from #55/#56 that was a false stop is a test in `guard/` (generic names, no owner history).

Done is judged by the measurement, not by the loop.

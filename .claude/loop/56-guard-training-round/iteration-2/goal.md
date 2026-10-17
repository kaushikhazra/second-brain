# Goal — 56, round 2: the ask class comes back, round 1 stays

Source: PR #57 review, Kaushik via Velasari, 17 Oct 2026. Fixed once the loop starts.

Install and stop-a-process commands are asked again, never blocked, at their old figures, while everything round 1 won is kept. Measured on `guard/data/test_plain.jsonl` and the private real-world scorecard.

1. Ask class, plain held-out set: asked >= 82% and wrongly blocked <= 6.6% (round 0: 82.1% and 6.6%; round 1: 67.6% and 10.3%).
2. The 11 new real cases from #55/#56: 0 blocked, 0 asked.
3. Real-world wrongly blocked (weighted, original 300) <= 4.0%.
4. Risky blocked does not drop from round 1: plain 99.90%, wrapped 99.80%, real-world 85.2% (55 of 58).
5. `guard/check_guard.py` 8 of 8; `guard/test_cases.py` 17 of 17; `guard/test_unwrap.py` 14 of 14.
6. Weights trained on synthetic commands only (RELEASE-NOTES-47).

Done is judged by the measurement, not by the loop.

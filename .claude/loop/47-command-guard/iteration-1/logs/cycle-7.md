# Cycle 7 — 2026-10-16 01:24 IST

`gh issue view 47`: open, 0 comments, criteria unchanged.

## Action done (backlog 5, AC 8)

- `guard/report.py`: measures the shipped guard (synthetic plain and wrapped held-out, the private scorecard when `GUARD_SCORECARD_DIR` / `<repo>/../.tmp/cmd-guard-dataset` has it, hook latency) and renders `guard/RELEASE-NOTES-47.md` from those numbers. When the scorecard is absent the notes say "not measured on this machine"; no figure is invented.
- `guard/score_real.py` refactored to expose `measure()` (one implementation of the weighting, used by both).
- `guard/check_guard.py` gained AC 8: notes must carry, per test set, both numbers within 0.1 pt of a fresh measurement. Shown to fail on (a) a notes copy with the wrapped risky-blocked figure edited (96.8% vs measured 99.8%) and (b) a copy with the safe-wrongly-blocked column dropped.

## Observe

| | cycle 6 | cycle 7 |
|---|---|---|
| criteria demonstrably met | 7 of 8 | **8 of 8** |
| checks | `check_guard.py` 6/6, `test_unwrap.py` 14/14 | `check_guard.py` 8/8 (AC 1,3-8, each also failing on a broken copy), `test_unwrap.py` 14/14 (AC 2) |
| synthetic plain risky blocked / safe wrongly blocked | 99.9 / 0.0 | 99.9 / 0.0 |
| synthetic wrapped | 99.8 / 0.0 | 99.8 / 0.0 |
| scorecard weighted risky blocked / safe wrongly blocked | 85.3 / 4.4 | 85.3 / 4.4 (no model change) |
| median hook latency | 166 ms | 164-171 ms |

## Goal check (observe.md)

Part 1, 8 of 8 hold by check: **yes**.
Part 2, "the scorecard is acceptable by Kaushik's labelling rule (nearly no deny is a false alarm on real commands)": **not established, and not mine to declare.** On the scorecard, about 15% of safe real commands in the sample (4.4% weighted to real use) are denied, and about 1 in 7 risky real commands (weighted) still passes. That is the owner's call. So the loop does **not** close this cycle: no comment on #47, cron kept.

Open and not closable from here:
- The bar: what share of risky blocked and safe wrongly blocked Kaushik accepts.
- Weights (`command_guard.bin/.json`, 4.2 MB) are uncommitted; a registered hook without them asks on every command. Release decision, his.
- `guard/data/` regenerable, deliberately uncommitted; `check_guard.py` AC 7 and `report.py` need `python guard/generate.py` to have run.

Assumptions: unchanged.

## Constraint for next cycle

All 8 hold; what remains is the quality bar. Without a stated bar, further tuning is a number chase. One provisional target keeps the loop honest until Kaushik rules: weighted safe wrongly blocked <= 3% without weighted risky blocked falling below 85%.

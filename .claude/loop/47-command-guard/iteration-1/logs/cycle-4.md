# Cycle 4 — 2026-10-16 00:24 IST

`gh issue view 47`: **failed** — api.github.com timed out (network). Criteria are the 8 read in cycles 1-3; no comment on the issue then, so unchanged as far as known. Push may fail too.

## Action done (backlog 3, first pass)

`guard/generate.py`: `prose_commands` (crosschat send, git commit -m / heredoc / -F -, gh comment / pr create --body, `>>` heredoc, echo, tag -m, with synthetic prose that uses delete/overwrite/rm/force-push vocabulary; gh comment/pr create labelled ask), `py_writes` (python that writes a file, `rm -rf X && mkdir X`). Prose is built from the generator's own frames and word lists. Retrained on regenerated 60k; scorecard files untouched and not trained on.

## Observe

| | cycle 3 | cycle 4 |
|---|---|---|
| synthetic plain: risky blocked / safe wrongly blocked | 100.0 / 0.0 | 99.8 / 0.0 |
| synthetic wrapped: risky blocked / safe wrongly blocked | 99.9 / 0.0 | 99.8 / 0.0 |
| scorecard raw: risky blocked | 94.8% (55/58) | 86.2% (50/58) |
| scorecard raw: safe wrongly blocked | 25.0% (54/216) | 10.6% (23/216) |
| scorecard population-weighted: risky blocked | 77.3% | 74.4% |
| scorecard population-weighted: safe wrongly blocked | 5.7% | **3.3%** |
| all 10,950 real commands: allow / ask / deny | 82.1 / 6.1 / 11.9 | 85.7 / 4.4 / 9.8 |

False alarms halved (54 → 23 raw). Risky blocked went down (55 → 50 of 58): five more rm/edit shapes now land on ask or allow. The trade is not acceptable as is: risky blocked is the number that must not fall.

Remaining misses (8): `sed -i` whose pattern holds backticks; `git branch -D`; `git checkout <ref> -- path`; python edit scripts (`s.replace` + write, `io.open`, `json.dump`, `save_record`); `rm -rf` + newline `mkdir`.
Remaining false alarms (23): python scripts run from deep Temp paths (`python -u C:/Users/.../Temp/...`, `cd <Temp path> && ...`), `sed -n` prints, `git show ... | sed`, one `crosschat send`, `git commit -F -`.

Criteria demonstrably met: **1 of 8** (AC 2). Not run: AC 1 registration, AC 3-5 hook sessions, AC 6 timing, AC 7 check, AC 8 release numbers.

Assumptions: unchanged. GitHub unreachable this cycle (transient, noted).

## Constraint for next cycle

Risky blocked slipped while false alarms fell; the model needs the write shapes it still misses, and the deep-Temp-path script runs it still blocks.

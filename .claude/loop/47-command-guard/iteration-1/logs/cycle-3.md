# Cycle 3 — 2026-10-16 00:00 IST

`gh issue view 47`: open, 0 comments, criteria unchanged.

## Action done (backlog 2)

Scorecard built outside the repo (`C:/Projects/.tmp/cmd-guard-dataset/`): `scorecard-sample.jsonl` (200 uniform, seed 47, + 100 drawn from the model's denies) and `scorecard-labels.json`, labelled by hand from the commands, not from the model.

Labelling choices (so the scorecard can be challenged): 1 = `>` / `cat > file <<EOF` onto a file, `sed -i`, `rm`/`rm -rf`, `branch -D`, `git checkout <ref> -- path`, python that rewrites a file. 0.5 = `gh issue comment`/`pr create`/`pr merge --delete-branch`/`repo create` (outward-facing), `branch -d`, `shutdown`, archive, local DB writes, and anything whose tail was cut off and could write. 0 = everything else incl. `>>` append, `git commit`/`push`/`add`, `crosschat send`. Counts: 58 risky, 216 safe, 26 ask. The cut-off python one-liners are the weakest labels.

`guard/score_real.py` now takes labels and a population file and reports a population-weighted figure (the sample over-draws denies).

## Observe

| scorecard, model after cycle 2 | |
|---|---|
| raw sample: risky blocked | 55/58 = 94.8% |
| raw sample: safe wrongly blocked | 54/216 = 25.0% (inflated: 100 of 300 drawn from denies) |
| population-weighted: risky blocked | 77.3% |
| population-weighted: safe wrongly blocked | 5.7% |

Weighted risky-blocked rests on 3 misses in the allow/ask strata, so it is soft (n small). Misses: two `python -c` that write a file (`json.dump`, `save_record`), one `rm -rf` chained with `mkdir` that landed on ask.

False alarms (54): dominated by long quoted prose: `crosschat send ... "<prose>"`, `git commit -m "$(cat <<EOF ...)"`, `gh ... --body "<prose>"`, plus heredoc bodies. The prose contains words like delete/overwrite and the model reads them as a command.

Criteria demonstrably met: **1 of 8** (AC 2). AC 8 has numbers now (synthetic 100/0 plain, 99.9/0 wrapped; scorecard above) but no check pins them and nothing is in release notes.

Assumption: unchanged.

## Constraint for next cycle

Prose inside quoted arguments is read as syntax. First real target the scorecard can move: safe wrongly blocked 5.7%.

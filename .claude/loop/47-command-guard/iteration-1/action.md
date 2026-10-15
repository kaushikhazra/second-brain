# Action

Backlog item 2 (cycle 3): build the real-world scorecard. Labels, not the model, decide what is right.

1. Sample with a fixed seed from `C:/Projects/.tmp/cmd-guard-dataset/commands.jsonl`: 200 uniform + 100 drawn from the current denies (so risky cases are enough to measure). Write the sample to `C:/Projects/.tmp/cmd-guard-dataset/scorecard-sample.jsonl`, outside the repo.
2. Label each by hand (read it, do not use the model): 1 = loses information (remove, overwrite, `>` onto a real file, `sed -i`, force/hard reset), 0.5 = installs, kills/stops processes, 0 = read, fresh create, history-keeping, plus production / off-machine send => 1. Save `scorecard-labels.json` ({command: label}) in the same folder. Never commit either file (AC 7).
3. Run `guard/score_real.py <sample> <labels>`. Record risky blocked %, safe wrongly blocked %, and ask-class handling.
4. If tuning is needed, change only deny_at / allow_below in `command_guard.json` or the generator (prose-in-quotes shapes: `gh ... --body "<prose>"`, `git commit -m "$(cat <<EOF`, `crosschat send "<prose>"`), then re-score. Do not train on the scorecard.
5. If the labelled run is flat after one generator change, report flat and stop.

# Action

Backlog item 3 (cycle 4): move the scorecard. Target: safe wrongly blocked (population-weighted, was 5.7%) down, risky blocked (was 77.3%) not down.

1. `guard/generate.py`: add SAFE families carrying long synthetic prose in a quoted argument or heredoc body, where the prose uses delete/overwrite/remove/rm/force-push vocabulary: `crosschat send <peer> <peer> "<prose>"`, `python -m crosschat send ...`, `git commit -m "$(cat <<'EOF' ... EOF)"`, `git commit -F - <<EOF`, `gh issue comment N --body "<prose>"`, `gh pr create --body-file - <<EOF`. Prose is built from the generator's own word lists and sentence frames, never from the owner's text (AC 7).
2. Add risky shapes the model missed: `python -c "... json.dump(..., open(p,'w'))"`, `Path(p).write_text(...)`, `open(p,'w').write(...)`, `rm -rf X && mkdir X` / `rm -rf X\nmkdir X` multi-line.
3. Regenerate train (seed 1, 60k) and held-out (seeds 2, 3), retrain, run `guard/score_real.py <sample> <labels> <commands>` with the same scorecard files in `C:/Projects/.tmp/cmd-guard-dataset/`. Do not train on them.
4. Record both held-out sets and the scorecard against cycle 3. Commit and push (separate invocations).
5. If safe-wrongly-blocked did not move, report flat and stop.

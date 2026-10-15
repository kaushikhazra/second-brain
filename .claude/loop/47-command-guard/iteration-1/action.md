# Action

Backlog item 3 (cycle 5): recover risky-blocked without giving back the false-alarm gain. Targets on the scorecard (population-weighted): risky blocked back to >= 77.3% (cycle 3), safe wrongly blocked <= 3.3%.

1. `guard/generate.py`, risky: `sed -i` with backtick / bracket / escaped patterns, `git branch -D X`, `git checkout <ref> -- <path>`, `git restore --source`, python edit scripts (`s.replace` then write, `io.open(p,'wb').write`, `json.dump(..., open(p,'w'))`, `save_*` style writers), `rm -rf X` followed by newline `mkdir`. More of them: weight `py_writes` up.
2. `guard/generate.py`, safe: `python -u <deep Temp path>/script.py`, `cd <deep Temp path> && python x.py`, `sed -n 'a,bp' <file>`, `git show <ref>:<path> | sed -n ...`, `git -C X commit -F -`, `crosschat send` with longer prose.
3. Retrain, run both held-out sets, run the scorecard (same files, never trained on). Compare to cycle 4.
4. If AC 1 time allows (GitHub reachable or not, it is local): register the hook in `src/.claude/settings.json` under PreToolUse matcher `Bash|PowerShell` -> `python .claude/hooks/command_guard.py`, matching how memory_guard.py is registered. Defer the proof check to the next cycle.
5. Commit and push. If push fails (network), commit locally and record it.
6. If risky blocked did not return to >= 74.4% after this pass, report flat and stop.

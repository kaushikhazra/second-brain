# Assumptions

Standing inputs. May change between iterations — when one does, say so in that cycle's Observe.

- Handover: `C:/Projects/second-brain/.claude/plans/47-command-guard-handover.md` (backlog 1-5 is agreed; drive it without asking per item).
- Work on `feature/47-command-guard` in C:/Projects/second-brain. Never merge to main, tag, or release.
- AC 7 is absolute: no owner command history in training. The real commands (`C:/Projects/.tmp/cmd-guard-dataset/commands.jsonl`) are test data only and are never committed. The scorecard labels stay outside the repo.
- Runtime stays stdlib-only (memory_guard.py's rule). Deviation from "numpy" in the issue is noted on the issue at close.
- Labelling rule (Kaushik, 10 Oct): stop = loses information (`echo x > file` included); ask = installs, kill/stop processes; go = read, fresh create, history-keeping changes; plus production and off-machine sends.
- Public data, if used: tldr-pages (CC-BY-4.0), attribution required.
- Commit and push together, as two separate shell invocations.
- Report to `velasari` over crosschat at start and each milestone.
- Artifact stays in place in the second-brain repo; this folder holds only the loop files and logs.

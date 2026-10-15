# 47-command-guard

## Goal

> All 8 acceptance criteria of second-brain issue #47 hold, each shown by a check that fails when the behaviour is removed: the CPU-trained command guard (`src/.claude/hooks/command_guard.py` and its weights) is registered for Bash and PowerShell, decodes wrapped commands, runs stdlib-only and fast, is trained on synthetic and public data only, and the release notes state the share of risky commands blocked and safe commands wrongly blocked on the held-out set and on the real-world scorecard.

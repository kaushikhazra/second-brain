# Assumptions — standing

- Weights are trained on synthetic commands only. The scorecard and real commands live outside the repo, are test only, and never enter `guard/generate.py` or `guard/train.py`.
- The generator uses generic names (acme/webapp), never owner names.
- The guard code lives on `feature/47-command-guard` (unmerged); this branch is cut from it.
- Nothing is merged here; the orchestrator opens the PR, Kaushik merges.

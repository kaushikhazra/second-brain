# Assumptions — standing

- Weights are trained on synthetic commands only. The scorecard and real commands stay outside the repo, are test only, and never enter `guard/generate.py` or `guard/train.py`.
- Generic names only (acme/webapp) in the generator.
- Same branch as round 1, `feature/56-guard-training-round`, so PR #57 updates. Nothing is merged here.
- Heavy runs (training, 150k sets, sweeps) go one at a time, only when Velasari types "go"; none while Kaushik is playing. Memory is 16 GB: two parallel runs were reaped once already.
- Training is deterministic per seed (verified: regenerating seed 1 reproduces the shipped training set byte for byte).
- A seed chosen using the private scorecard is a mild selection effect and is said so in the PR comment.

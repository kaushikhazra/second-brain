# 38 — clone projects

## Goal

> Every acceptance criterion in GitHub issue #38 holds against this repo, proven by a
> check that fails when the behaviour is removed: the brain owner hands the brain a git URL and it clones the project into `projects/<repo-name>/`, reports path and default branch, never re-clones, fails cleanly with a distinct message and no partial folder, lists what it manages, keeps `projects/` out of its own repo, and still finds every project after the brain folder is renamed.

# 41 — monitor projects

## Goal

> Every acceptance criterion in GitHub issue #41 holds against this repo, proven by a
> check that fails when the behaviour is removed: the brain asks whether to monitor a project it takes in, lets the owner switch and list monitoring, checks only monitored projects' open issues in their tracker each heartbeat, reports each new issue once and drops closed ones, says once when a tracker is unreachable, and never resurfaces old issues as new after a restart.

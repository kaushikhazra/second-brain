# 25 — the repo holds the machinery for building the brain, not a brain

## Goal

> Every acceptance criterion in GitHub issue #25 holds against this repo: everything that
> ships lives under `src/` and nothing outside it reaches a user's install; the root
> `CLAUDE.md` addresses someone developing the brain and never instructs its reader to
> start the brain's subsystems; `build-dist.py` produces the archive from `src/` alone,
> so deleting `.gitattributes` entirely cannot change what ships; the artifact itself does
> not move, path for path and byte for byte against `second-brain-1.0.1.zip`; no file and
> no generated artifact carries a path frozen before the move; a fresh brain unpacked from
> the new archive still boots, with `session-start`, `verify_memory.py` and the hooks
> intact; the loop records still resolve and no cycle log is edited; and a build that
> would ship anything from outside `src/` fails rather than writing it.

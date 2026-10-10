# Assumptions

Standing inputs for issue #46.

## Settled

- **No backup before a cycle.** Kaushik's ruling, 2026-10-10: "back up is an overkill for
  consolidation. Any way memory is written by the agent so it is un-attended. Just
  consolidate when nothing is going on." A cycle runs only on quiet beats. Reversibility
  comes from archiving, never deleting.
- **A cycle runs `/dream`'s Act 2 triage and Act 3 consolidation only**, not Act 4
  relational surgery (needs the owner's second read).
- **State lives in `.claude/activations.json`** through `.claude/shared/activation.py`,
  which `update_brain.py` already treats as machine-local, so it survives `/update`.
- Never touch the live store from a check. Scratch under `C:/Projects/.tmp/second-brain-loop-46/`.
- Dev runs of synaptra use `SYNAPTRA_PORT=8150` and a scratch `SYNAPTRA_DB`; the default
  port belongs to the live service.

## Open (resolve by evidence, not by guess)

- Can one cycle be capped at N memories (does `memory_consolidate` accept a limit), or must
  the cycle select ids itself? Settle in cycle 1 from synaptra's source.
- What counts as the backlog (memories waiting for consolidation)? Settle from synaptra's
  consolidation selection logic.

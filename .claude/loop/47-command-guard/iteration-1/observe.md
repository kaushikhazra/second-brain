# Observe

Open every cycle with `gh issue view 47 --repo kaushikhazra/second-brain`, before the diff and before the last log.

Record each cycle:

- Criteria demonstrably met, out of 8. Demonstrably = a script or scripted session that fails when the behaviour is removed. Name the check per criterion.
- Real-world scorecard numbers (risky blocked %, safe wrongly blocked %) against the last cycle, and what moved them.
- What is still missing, and whether it can be closed from here.
- Any assumption that changed.

Goal check:

- **Met** — 8 of 8 hold by check, and the scorecard is acceptable by Kaushik's labelling rule (nearly no deny is a false alarm on real commands). The loop ends: comment on #47 with criteria held out of N, what was accepted rather than fixed, and the branch head commit. Do not merge or release.
- **Not met** — report and write the next action from this cycle's constraint.
- **Answer did not move** — report the flat result and stop. Do not run another variant.

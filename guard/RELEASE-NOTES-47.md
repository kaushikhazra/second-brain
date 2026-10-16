## Command guard (#47)

Every shell command the brain runs through Bash or PowerShell is judged first by a small
model that runs on the CPU in plain Python. Wrapped commands (`bash -c`, `powershell -Command`,
`python -c`, base64, hex) are opened before it judges. A confidently safe command runs, a
confidently risky one is blocked with the reason it tripped (deletes, overwrites, touches
production, sends data off the machine), and anything unsure asks you.

| Test set | Risky commands blocked | Safe commands wrongly blocked |
|---|---|---|
| Plain commands (synthetic held-out), 5,000 commands | 99.9% | 0.0% |
| Wrapped and encoded commands (synthetic held-out), 5,000 commands | 99.8% | 0.0% |
| Real-world scorecard (hand-labelled, weighted to real use) | 85.3% | 4.4% |

Install and stop-a-process commands are asked, not blocked: 82.1% of them ask on the plain set and 6.6% are wrongly blocked.

Read the numbers with care: the synthetic sets are built from the same templates as the training
data, so they are a ceiling, not a forecast. The real-world scorecard is the honest figure; it is
300 commands labelled by hand, never trained on, and not shipped. The weights are trained on
synthetic commands only; no owner's command history is in them.

Blocks at 0.65 confidence, runs below 0.30, asks in between. Median time per tool call, fresh process: 164 ms, standard library only.

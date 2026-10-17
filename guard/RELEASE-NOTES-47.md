## Command guard (#47)

Every shell command the brain runs through Bash or PowerShell is judged first by a small
model that runs on the CPU in plain Python. Wrapped commands (`bash -c`, `powershell -Command`,
`python -c`, base64, hex) are opened before it judges. A command it finds safe runs as
usual. When it suspects a command deletes, overwrites, touches production or sends data off
the machine, it denies the command once and tells the model what it suspects and why (a
confident score says so, an unsure one words it as a suspicion). The model reads that
immediately; if it checked and still wants the command, it re-runs the same command with
`# guard-ack:<code>` appended. The code is the first 6 hex of the sha256 of the exact
command, so an ack cannot be written ahead of time or reused on another command. The ack
is a comment in Bash and PowerShell and changes nothing that runs. With the right ack the
guard stays silent and your own permission rules decide; a wrong or missing ack is denied
again. The guard never approves a command itself.

| Test set | Risky commands denied first | Safe commands wrongly denied first |
|---|---|---|
| Plain commands (synthetic held-out), 5,000 commands | 99.9% | 0.0% |
| Wrapped and encoded commands (synthetic held-out), 5,000 commands | 100.0% | 0.0% |
| Real-world scorecard (hand-labelled, weighted to real use) | 89.3% | 5.6% |

Install and stop-a-process commands: 77.8% are denied first on the plain set, 10.3% of them with the confident wording.

Read the numbers with care: the synthetic sets are built from the same templates as the training
data, so they are a ceiling, not a forecast. The real-world scorecard is the honest figure; it is
311 commands labelled by hand, never trained on, and not shipped. The weights are trained on
synthetic commands only; no owner's command history is in them.

Denied from 0.30 (confident wording from 0.65), silent below. Median time per tool call, fresh process: 161 ms, standard library only.

## Command guard (#47)

Every shell command the brain runs through Bash or PowerShell is judged first by a small
model that runs on the CPU in plain Python. Wrapped commands (`bash -c`, `powershell -Command`,
`python -c`, base64, hex) are opened before it judges. The guard is hint-only: it never
blocks and never asks, and every command runs under your own permission rules. When it
suspects a command deletes, overwrites, touches production or sends data off the machine,
it adds a note for the model saying what it suspects, so the model can reconsider; a
confident score words the note as certain, an unsure one as a suspicion. A command it finds
safe gets no note. Claude Code shows the note to the model next to the command's result.

| Test set | Risky commands hinted confidently | Safe commands wrongly hinted |
|---|---|---|
| Plain commands (synthetic held-out), 5,000 commands | 99.9% | 0.0% |
| Wrapped and encoded commands (synthetic held-out), 5,000 commands | 99.8% | 0.0% |
| Real-world scorecard (hand-labelled, weighted to real use) | 85.7% | 4.0% |

Install and stop-a-process commands get the unsure wording: 67.6% of them do on the plain set and 10.3% are hinted as confidently risky.

Read the numbers with care: the synthetic sets are built from the same templates as the training
data, so they are a ceiling, not a forecast. The real-world scorecard is the honest figure; it is
311 commands labelled by hand, never trained on, and not shipped. The weights are trained on
synthetic commands only; no owner's command history is in them.

Confident wording from 0.65, no note below 0.30, suspicion wording in between. Median time per tool call, fresh process: 149 ms, standard library only.

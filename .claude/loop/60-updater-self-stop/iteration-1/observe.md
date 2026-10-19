# Observe — #60

`python checks/update/check_venv_launch.py` — PASS lines for AC 1-6, run on scratch
brains with a standalone interpreter, a real venv and a PATH holding no Python. Each
criterion is shown to bite: the same scenarios run against two broken copies of the
updater (`no-handover`, `original-bug`) and the named criteria must FAIL.
The existing `checks/update/*` scripts must stay green.

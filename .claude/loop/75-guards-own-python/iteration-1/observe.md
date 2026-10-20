# Observe — #75

`python checks/guard/check_guards_own_python.py` — runs the real settings.json command
through Git bash with no python on PATH, per AC, then removes one behaviour at a time and
requires the named AC to fail. Done = 7 of 7 hold and every removal is caught.

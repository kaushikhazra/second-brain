# Observe — #83

`python checks/recall-session/check_config_dir.py` — runs the real search.py against scratch config and
home folders (USERPROFILE/HOME pointed at an empty one); then removes one behaviour at a time and requires
the named AC to fail. Done = 6 of 6 hold and every removal is caught.
Regression: `checks/recall-session/check_recall_session.py`.

# Observe — #81

`python checks/session-start/check_unattended_boot.py` — drives the real activation.py as the skill's
own import line uses it, reads the skill and brain.bat; then removes one behaviour at a time and
requires the named AC to fail. Done = 7 of 7 hold and every removal is caught.
Regression: `checks/curiosity/check_curiosity.py`, `checks/news/check_news.py`.

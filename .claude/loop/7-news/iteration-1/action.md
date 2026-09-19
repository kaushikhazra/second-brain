# Action

**Cycle 1. Baseline, register the habit, port the skill and the script.**

Record the baseline in `logs/cycle-1.md`: the branch; `activation.py`'s habit registry as
it stands; whether `.env` is in `.gitignore`; the regression line (eight scripts now).

Then, in this order:

1. **Register `news`** in `activation.py` with a `last_run` field per habit, and add
   the one line to `session-start` that runs `/news` after the report when active and
   not yet run today. Prove the three activation scenarios and `on|off|status` for
   `news` in `check_news.py`, reusing #6's check shape.

2. **Port the skill.** `.claude/skills/news/SKILL.md` from Velasari's, generalised: the
   format rule, the verify-every-link rule, no count, quiet day in one clause, the
   keyword file named as the only knob, the YouTube-needs-keys line, the keep rule.
   Create `news-keywords.txt` at the brain root with a short starter list the owner is
   told to edit.

3. **Port the script.** `scripts/youtube_subs.py` with the brain root walked up, the RSS
   path removed, `playlistItems` for uploads, and a clear message per failure: no
   `.env`, no keys, auth refused, quota exceeded, network down. Keep subscribe and
   unsubscribe.

4. **`check_news.py` structural half**: the skill states each rule; the script has no
   RSS URL; the keyword file exists and is named in the skill.

Do not run the headless proofs this cycle; they come once the pieces exist.

Commit on `feature/7-news`, push, write `logs/cycle-1.md`, write the next `action.md`,
send the one-line report to velasari, and exit.

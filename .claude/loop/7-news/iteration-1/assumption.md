# Assumptions

Standing inputs. May change between iterations — when one does, say so in that cycle's
Observe.

- **The source is Velasari's news skill, on this machine:**
  `C:/Projects/ai-persona/Velasari/.claude/skills/news/SKILL.md` (90 lines) and
  `scripts/youtube_subs.py`, `youtube_auth.py`. The skill's rules ship: headline and link
  only, no summary, verify every link, no fixed count, a quiet day said in one clause,
  keep → reading list newest first. The keyword list at the bottom of Velasari's skill is
  that owner's; here it moves to its own file the owner edits (AC 12).
- **Activation is #6's mechanism.** `.claude/shared/activation.py` holds the record;
  `session-start`'s step asks once per habit per VERSION. This story adds `news` to the
  habit registry and nothing else to that step. Read `activation.py` and #6's
  `SKILL.md` before writing the news skill's `on|off|status`, and make them the same
  shape.
- **Once a day when active** (AC 11): `session-start` runs `/news` after its report if
  the record says active and no run is recorded for today. The daily marker lives in the
  activation record (`last_run` per habit), not a separate file.
- **The keyword file** is `news-keywords.txt` at the brain root, one word or phrase per
  line, whole-word case-insensitive match, and the skill says it is the only knob.
- **Web sources.** Searched live each run with the session's WebSearch; no cache. The
  skill names the search shape ("today's AI news" plus the owner's keywords) and leaves
  source choice to the search. If the owner wants named sources later, that is a
  keyword-file line, not a skill change.
- **YouTube.** Keys in `.env` at the brain root: `YOUTUBE_CLIENT_ID`,
  `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`. The script resolves the brain root
  by walking up, never by a fixed parent count (Velasari's `parents[4]` is a frozen
  depth; replace it). Uploads come from the Data API `playlistItems` on each
  subscription's uploads playlist, at 1 quota unit per channel per run; the RSS path is
  removed. Without keys: one line, not configured, and the rest of the list appears.
  Subscribe/unsubscribe management stays in the script as Velasari has it.
- **The reading list** is `reading-list.md` at the brain root, created on first keep
  with a two-line header, blocks under `## YYYY-MM-DD`, newest date first, each block:
  bold title, source line, link. No checkbox, status or due date anywhere in the file.
- **Checks live at `.claude/skills/news/check_news.py`** and use scratch project
  directories under `C:/Projects/.tmp/second-brain-loop-7/`; a headless proof with
  network is expected for AC 8, 13, 15, 16.
- **CLAUDE.md gains one routing row** for `/news`, and `session-start`'s row names the
  daily run.
- **Branch `feature/7-news`, cut from `main` after PR #15.** One commit per cycle,
  pushed. No PR, no merge.
- **Nothing else is touched** beyond: `activation.py` (one registry entry),
  `session-start` (the daily-run line), `.gitignore` (nothing new; `.env` is already
  ignored, check), `CLAUDE.md` (rows).

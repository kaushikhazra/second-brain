# Action

**Cycle 2. The list-production half, live: format, verified links, sources, and
the two named-failure cases.**

Read the issue fresh, then `logs/cycle-1.md`. Cycle 1 built the whole activation
mechanism (5/19 — AC 1-5) and the skill/script/keyword-file scaffold, structurally
checked but not yet run live (AC 6-9, 11-14, 16-19 structural only; AC 10, 15
untouched).

1. **A scripted-agent proof of `/news` by hand, with real network access.**
   Scratch project shaped like issue #6's — `news` skill, `activation.py`, hook/
   settings for parity, no synaptra needed (this skill doesn't call it). Seed
   `news-keywords.txt` with two or three distinct, checkable words (avoid
   anything broad enough to make "verify every link" trivially pass by luck).
   No `.env` in this first run. Assert against the transcript AND structurally
   against the printed output:
   - **AC 7** — every item is exactly a bold headline line and a link line,
     nothing else (regex the output, not just eyeball it).
   - **AC 8** — every link in the output was actually fetched before being
     shown (the transcript's tool-call trace has a fetch for each URL that
     appears in the final list; a URL with no matching fetch fails this).
   - **AC 9** — no fixed count language in the reply; if the result is short,
     the reply says so in one clause.
   - **AC 10** — produced the list when invoked plainly, at any time (no
     activation gate applies).
   - **AC 13** — the reply or transcript shows a live search this run, not a
     phrase like "as I mentioned" that would imply a cached answer.
   - **AC 14 (no-`.env` half)** — the YouTube section is exactly one line
     saying not configured; the web-search half still appears in full.

2. **A second run, `.env` present with placeholder/invalid keys.** Assert the
   YouTube half names the actual failure (`AUTH_FAILED`, from the script's own
   distinguishable prefix) rather than presenting it as a quiet day, and the
   web-search half is unaffected. This is **AC 14's second half**.

3. **AC 15 — a failed web source.** This is harder to force than YouTube's
   auth failure since "the web search" isn't a single pinned endpoint the way
   YouTube's API is. Investigate the seam: can a source be forced unreachable
   in a way that's still faithful to what AC 15 actually claims (a named
   source, not a fabricated one)? If there's no clean way to force a live web
   search to include a specific dead source, say so plainly and design the
   nearest faithful proxy (e.g., a source list the skill is told to check that
   includes one dead URL) rather than skipping the criterion or forcing a
   fragile test — per the antenna principle.

4. **AC 16/AC 17 — the keep rule.** In the same or a follow-up run, have the
   transcript include the owner saying "keep that" about one item; assert
   `reading-list.md` gained one block under today's date, at the top, with
   title/source/link, and grep the whole file for `- [ ]`, `status`, `due` —
   none present.

5. **AC 18 — no network.** Reuse issue #6 cycle 3's technique directly:
   `--disallowedTools WebSearch,WebFetch,Bash,Task` (the Bash/Task lesson
   already paid for once; do not rediscover it here).

6. **AC 19 — a news failure never stops `/session-start`.** This may be more
   naturally proved as a `/session-start`-level scripted run (force `/news` to
   fail via AC 18's technique or a broken `.mcp.json`-equivalent, and confirm
   the rest of `/session-start`'s steps still completed and reported) rather
   than purely from `news`'s own scratch project. Judgement call: build
   whichever scaffold actually proves the claim, and say which was chosen and
   why in the log.

7. **AC 11's live half** — `ran_today`/`set_last_run` exercised through an
   actual `/session-start` run: first run, active and not yet run today,
   produces a list and stamps `last_run`; a second `/session-start` run the
   same day, same record, produces nothing (skip, per step 8's own text).

Update `check_news.py` (or split into `check_news_*_scripted_agent.py`
siblings, matching issue #5/#6's naming split between structural and
scripted-agent checks — prefer the split once more than two or three scripted
scenarios accumulate) with whatever of the above can be asserted as a script
rather than only a headless run's own claim.

Commit on `feature/7-news`, push, write `logs/cycle-2.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

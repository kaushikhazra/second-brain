# Observe

## Order matters

**Read the criteria from GitHub first** — `gh issue view 7 -R kaushikhazra/second-brain` —
before the diff and before the previous cycle's log. Attack each criterion; do not confirm
it. The criteria drive the cycle.

## The measurement

The number this loop moves is **criteria demonstrably met, out of 19.** Demonstrably means
a check that fails when the behaviour is removed.

The proof standard, unchanged. This is the last story; it must not regress any of the six
before it.

## Every cycle, record

- **Criteria met, out of 19**, by number, in three buckets. Only the first counts.
- How far the number moved, and what moved it.
- The full regression line: `check_shapes.py` · `check_hooks.py` · `check_session_start.py`
  · `check_verify_memory.py` · `check_heartbeat.py` · `check_dream.py` ·
  `check_recall_session.py` · `check_curiosity.py`. All pass.
- Any assumption that changed.
- The branch, read from git.

## The five that will be got wrong

- **AC 1 to AC 6 — activation.** Do not build a second mechanism. Register `news` in
  `activation.py`'s habit list and prove the same three scenarios #6 proved (fresh asks,
  answered stays quiet, VERSION change re-asks) for this habit, plus `on|off|status`.
- **AC 8 — every link checked to resolve to what its headline says.** A headless run
  with network: assert every link in the output was fetched before printing (the skill
  states the check; the transcript shows the fetches; the printed list contains no URL
  that was not fetched).
- **AC 14 — YouTube only with keys.** Two runs: `.env` absent → the YouTube half is one
  line saying not configured and the rest of the list still appears; `.env` present
  with placeholder keys → the script reports the auth failure by name, not a quiet day.
  ⚠ YouTube's public RSS upload feed returned 404 on 2026-09-19 on this machine; the
  port must not depend on it. The Data API `playlistItems` route with the owner's keys
  is the one to keep; the RSS path is removed, not left as a silent fallback.
- **AC 15 — a failed source is named.** Seed a source list with one unreachable host;
  assert the output names it and still shows the rest.
- **AC 16 and AC 17 — keep appends to `reading-list.md`, newest first, no checkbox, no
  status, no due date.** Headless run: owner says "keep that" about item 2; assert the
  file gained one block under today's date at the top with title, source, link; grep
  the whole file for `- [ ]`, `status`, `due` and assert none.

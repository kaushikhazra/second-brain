# Cycle 1 — 2026-09-20 ~01:05–01:20 +0530

**Branch:** `feature/7-news` (read from `git branch --show-current`, cut from
`main` after PR #15, confirmed clean before starting).

## Baseline

- **`activation.py`'s habit registry, as it stood:** no fixed list — the module
  is generic over any `habit` string; only `curiosity` had ever been passed to
  it. `set_answer`, `is_active`, `needs_ask`, `answered_at_version` all took a
  `habit` parameter already, so registering `news` needed no structural change
  to those functions.
- **Was `.env` already git-ignored?** `assumption.md` said "already ignored,
  check" — checked, and it was **not**. `.gitignore` had no `.env` entry at
  all, and no `.env` file was tracked in git either (so nothing had actually
  leaked — this was a preventive gap, not an active one). Fixed in this cycle,
  see below.
- Regression before touching anything: not run standalone — no prior state for
  this story; run at the end of this cycle instead (below), now eight scripts.

## What moved

1. **Registered `news` in `activation.py`.** Added `last_run`, `ran_today`,
   `set_last_run` — `last_run(record, habit)`, `ran_today(record, habit,
   today=None)` (injectable for tests), `set_last_run(record, habit,
   today=None)` (raises if the habit has no activation entry yet — nothing to
   stamp a run against). `set_answer` now documents that it resets `last_run`
   on a fresh answer, on purpose: a habit just re-asked after a `VERSION`
   change should be free to run again that same day.
2. **`session-start`'s Activation step (step 2)** now carries a small table —
   habit, question text, hint — with `curiosity` and `news` as its two rows,
   replacing the single hardcoded question/hint pair from issue #6. A third
   habit is one more row, not a second block of prose, matching
   `assumption.md`'s instruction exactly.
3. **A new step 8, "Daily habits"**, after the Report step (deliberately last,
   so a `/news` failure has nothing left of the boot to take down with it —
   AC 19). Gates on `is_active` then `ran_today`; runs `/news` and stamps
   `last_run` regardless of whether the run succeeded (a broken source retried
   every few minutes for the rest of the day would be its own failure mode).
4. **`.claude/skills/news/SKILL.md`**, generalised from Velasari's 90-line
   source: activation handling at the top (mirroring `/curiosity`'s shape
   exactly, per `assumption.md`), then the list-production rules (format,
   verify-every-link, no-fixed-length/quiet-day, the keyword file as the only
   knob, YouTube's not-configured line), the keep rule, and failure handling.
   Reworded two spots after the first check run to match the criteria's own
   literal language more closely (see below).
5. **`news-keywords.txt`** created at the brain root — comment-line support
   (`#`-prefixed lines ignored) added on top of Velasari's format, with a
   starter list carried over from her YouTube keywords (the AI/ML terms;
   generalised, no persona-specific content).
6. **`scripts/youtube_subs.py`**, ported with the changes `assumption.md` and
   `observe.md` both called for:
   - `brain_root()` walks up (never a fixed `parents[4]` depth).
   - **The RSS path is removed entirely** — no `feeds/videos.xml` URL, no
     `ATOM`/`MEDIA` XML namespaces anywhere in the file. `recent_uploads()`
     replaces the old RSS-based `uploads()`, using `playlistItems` on each
     channel's uploads playlist (`UU` + channel id), same 1-quota-unit-per-
     channel cost the old per-channel `latest_upload()` already had — just
     returning several recent items instead of only the single latest one.
   - Distinguishable failure prefixes — `NOT_CONFIGURED` (no `.env`, or a
     specific key missing), `AUTH_FAILED` (token refresh rejected),
     `NETWORK_ERROR` (a `urllib.error.URLError` that isn't an `HTTPError`),
     `QUOTA_EXCEEDED` (existing quota-wall handling, kept) — so the skill (and
     a later check) can tell "not set up" from "set up and broken" without
     parsing free text.
   - Subscribe/unsubscribe kept unchanged in behaviour.
7. **`scripts/youtube_auth.py`** also ported (not explicitly in `action.md`'s
   port list, but both the skill and `youtube_subs.py`'s own error messages
   point at it, and leaving a `parents[4]`-hardcoded copy of it in place would
   have been the same class of bug this story exists to fix elsewhere) — same
   `brain_root()` walk-up, otherwise unchanged.
8. **`.gitignore`** gained `.env`, since the assumption that it already was
   ignored turned out to be wrong.
9. **`CLAUDE.md`** gained one Session Lifecycle row for `/news` and one
   Structure row.
10. **`check_news.py`**, mirroring `check_curiosity.py`'s shape for the
    activation half exactly (issue #7's AC 1-6 are, criterion for criterion,
    the same shape as issue #6's AC 1-6) — mechanism-tier proof against a
    scratch brain root, plus a real two-process restart for AC 5. Then a
    structural half checking what `SKILL.md` and `youtube_subs.py` actually
    say: the format/verify-link/no-fixed-length/keyword-file/YouTube-keys/
    keep/no-checkbox/no-network/searched-live/never-stops-session-start rules
    are all present as text, the script has no RSS reference, the keyword
    file exists.

Two regressions were found and fixed while running the full suite, both
self-inflicted by this cycle's own edits, not by the check scripts:

- `check_news.py`'s first pass found two of its own regex checks didn't match
  the skill's actual wording (`"nothing about news is printed, fetched or
  scheduled"` split across a markdown line-wrap, same class of bug
  `check_dream.py` hit in issue #5; and `"not configured"` wasn't the literal
  phrase the skill first used for YouTube's unconfigured state). Fixed by
  loosening the check's regex to tolerate the line-wrap, and by rewording the
  skill to use the criterion's own literal phrase ("not configured") rather
  than a paraphrase.
- Rewriting `session-start`'s Activation step into a shared two-habit table
  **regressed `check_curiosity.py`'s AC 3 check to 6/7** — it looked for the
  literal phrase `"hint for switching it on later"`, which the table rewrite
  replaced with `"that habit's one-line hint from the table above"` (still
  correct, differently worded). Fixed the check to look for the concrete
  hint command (`/curiosity on`) instead of a generic phrase — a check on a
  shared file used by two stories should anchor on the part that cannot
  legitimately reword itself out from under a future story's own edit.
  Re-verified 7/7.

## Criteria met, out of 19

**First bucket (demonstrably met, check fails when the behaviour is
removed):** AC 1–5 — **5/19**, all via `check_news.py` driving `activation.py`
directly (mechanism tier), plus the real two-process restart and `.gitignore`
check for AC 5.

**Second bucket (plausible, not yet proven — structural half only, per this
cycle's own explicit scope):** AC 6, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 19 —
twelve criteria whose text is checked against `SKILL.md`/`youtube_subs.py`/
`session-start` `SKILL.md`, but none of which has a live run behind it yet.
`action.md` was explicit that this cycle does not attempt those: "Do not run
the headless proofs this cycle; they come once the pieces exist."

**Third bucket (not attempted at all):** AC 10 (`/news` by hand produces the
list), AC 15 (a failed source is named rather than a quiet day) — no check of
any kind exists for these two yet.

Only the first bucket counts, per `observe.md` — **5/19**.

## Regression — full line, after the above

```
check_shapes.py           5/5
check_hooks.py             27/27
check_session_start.py     2/2
check_verify_memory.py     12/12
check_heartbeat.py         3/3
check_dream.py             5/5
check_recall_session.py    12/12
check_curiosity.py         7/7
check_news.py              18/18
```

All pass (after the two fixes above).

## Assumptions

One changed: `.env` was **not** already in `.gitignore`, contrary to
`assumption.md`'s stated check — fixed this cycle, noted here rather than
silently "corrected" without a record.

## Next

Cycle 2 builds the live scripted-agent proofs for the list-production half:
AC 7-9 (format, verified links, no-fixed-length/quiet-day) with a real web
search; AC 13 (searched live); AC 14 (both the no-`.env` "not configured"
one-liner and, with placeholder keys, the `AUTH_FAILED` case named rather
than a quiet day); AC 15 (one unreachable source named, the rest of the list
still shown); AC 10 (by-hand invocation). AC 16/17 (the keep rule) and AC 11
(the daily-run gate, `ran_today`/`set_last_run` exercised through a real
`/session-start`-triggered run) are natural companions once a scratch project
with a real news list to act on exists — fold them in if the same scaffold
covers them cheaply. AC 18 (no network) and AC 19 (a news failure never
stops `/session-start`) reuse issue #6 cycle 3's `--disallowedTools`
technique (with the Bash/Task lesson already learned) rather than
rediscovering it.

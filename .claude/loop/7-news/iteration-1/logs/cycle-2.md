# Cycle 2 — 2026-09-20 ~01:16–01:41 +0530

**Branch:** `feature/7-news` (read from `git branch --show-current`, confirmed
clean and up to date with origin before starting).

## What moved

Built two scripted-agent check scripts covering every remaining criterion:

**`check_news_pass_scripted_agent.py`** — three by-hand `/news` runs against a
minimal scratch project (no synaptra, `/news` never needs it), using
`--output-format stream-json` so every `WebSearch`/`WebFetch` call is visible
in the trace, not just the final reply:

- **`no-env`** (no `.env`, includes a "keep that" follow-up in the same turn)
  — 8/8 on the second pass: AC 7 (bold-headline-and-link items, nothing else),
  AC 8 (every shown link had a matching `WebFetch` before it appeared), AC 9
  (no fixed-count language), AC 10 (a real by-hand list), AC 12 (every
  headline matched the seeded keyword scope), AC 13 (a real `WebSearch` this
  run), AC 14's first half (YouTube: "not configured" in one line, web half
  unaffected), AC 16/AC 17 (the keep, appended under today's date, no
  checkbox/status/due-date).
- **`bad-keys`** (`.env` with placeholder YouTube credentials — a genuine HTTP
  401 from Google's real OAuth endpoint, not simulated) — 2/2: AC 14's second
  half (`AUTH_FAILED` named, not a quiet day) and AC 15, as a faithful
  instance of the same claim (see below for why no second, separate AC 15
  proof was built).
- **`no-network`** (`--disallowedTools WebSearch,WebFetch,Bash,Task`, issue #6
  cycle 3's technique reused directly, Bash/Task lesson included) — 1/1:
  AC 18.

**`check_news_session_start_scripted_agent.py`** — three sequential
`/session-start` runs against a second scratch project (`session-start` +
`news` skills, no synaptra configured, exercising the documented
memory-less-boot fallback):

- **Run 1** (news active, no `last_run` yet, web/shell tools disallowed so
  `/news` is forced to fail) — 2/2: AC 19 (the boot still produced its
  completion report despite the forced failure) and AC 11's setup half
  (`last_run` gets stamped even though the attempt failed, exactly as
  `session-start`'s step 8 says it should).
- **Run 2** (same record, now carrying today's `last_run`, full tool access
  restored) — 1/1: AC 11's second half — no `Skill` tool call named `news`
  this run, and the boot still completed.
- **Run 3** (independent — news off, fresh record) — 1/1: AC 6's behavioral
  half — no `news` skill invocation, no `WebSearch`/`WebFetch` call, and the
  boot still completed normally.

**Three real gaps were found and fixed while getting these runs to pass, not
assumed correct beforehand:**

1. **The "today's news" wording was ambiguous and produced a false quiet day.**
   The `no-env` run's first pass returned an empty list — the model read
   `SKILL.md`'s "a source older than today's run is not shown as today's
   news" literally, rejecting genuinely current items (Sept 18–19) because
   they weren't dated the literal current calendar day. Reworded step 1:
   "live" governs the *search*, not the article's publish date; a quiet day
   is about how much is actually happening, not an artificial same-day
   filter. Rerun produced a real three-item list.
2. **The keyword scope wasn't actually enforced on headlines.** Even after
   the reword, one shown headline ("Detecting and countering misuse of AI:
   September 2026") matched none of the three seeded keywords by its own
   text — it came from an Anthropic-scoped *search query* but never said
   "Anthropic" in the headline itself. `SKILL.md` only said the search was
   "scoped by" the keyword file, which the model reasonably read as guiding
   the query, not filtering the result. Added an explicit rule: keep only
   results whose own headline matches a keyword, whole word, case-insensitive
   — the same mechanical rule the YouTube half already had. This is what
   makes AC 12 ("adding or removing a word is the only thing that changes
   what gets through") actually true rather than approximately true.
3. **A `subprocess.run` Windows encoding crash.** The first `no-env` rerun hit
   `UnicodeDecodeError: 'charmap' codec can't decode byte 0x81` reading
   `claude -p`'s stdout under the default `cp1252` console encoding (real
   web content contains bytes outside that codepage). Fixed by passing
   `encoding="utf-8", errors="replace"` explicitly to `subprocess.run`.

**One more, cheaper bug**: `check_news_pass_scripted_agent.py`'s three modes
share one scratch project, and `do_run()` unconditionally deletes
`reading-list.md` at the start of every mode — so re-verifying `no-env`
*after* running `bad-keys` and `no-network` read the file as missing, even
though the `no-env` run itself had produced it correctly. Fixed by
snapshotting `reading-list.md` under each mode's own name right after that
mode's run, and having `do_verify` read the snapshot instead of the live
shared file.

**AC 15's proof shape, stated plainly (`action.md`'s own instruction on this
point):** no separate "one dead URL in an otherwise-live web search" run was
built. There is no controllable seam for forcing one specific result of a
real, live web search to be unreachable without fabricating a source that
isn't genuinely being searched — which would be the less faithful proof, not
a more thorough one. The `bad-keys` scenario's YouTube auth failure is a real
source (an actual API call) genuinely failing for a real reason, named rather
than papered over as a quiet day — exactly what AC 15 claims, just for the
source this codebase can actually make fail on command.

## Criteria met, out of 19

**First bucket (demonstrably met, check fails when the behaviour is
removed):** AC 1–19 — **19/19.** AC 1-5 from cycle 1; AC 6-19 this cycle, via
the two scripted-agent scripts above, against real web search, a real (if
deliberately invalid) OAuth call, a real tool-denial technique, and real
`/session-start` runs.

**Second bucket:** none remaining.

**Third bucket:** none remaining.

**All 19 acceptance criteria for issue #7 are demonstrably met.**

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

All pass.

## Assumptions

None of `assumption.md`'s standing inputs changed this cycle beyond what's
already recorded in cycle 1's log (the `.env` git-ignore gap).

## Next

None — the loop converges here. Deleting the cron, posting the closing
comment on issue #7 with the final numbers, pushing, and telling Velasari.
This was the last of the seven stories (#2–#8, minus #1 which was PR #9
itself) this loop-engineering rollout scaffolded — worth saying plainly on
the channel rather than only in this file.

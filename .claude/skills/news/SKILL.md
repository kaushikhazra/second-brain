---
name: news
description: The morning news list — headlines and links only, from sources the owner chose. Runs once a day after /session-start when switched on, or any time by hand on /news. Never a summary, never a comment, never a category.
---

# News

Put the day's news in front of the owner, with links, and stop.

## Activation

Opt-in, through the same activation record `/curiosity` uses (issue #6's
`.claude/shared/activation.py`, `.claude/activations.json`, git-ignored).
`/session-start`'s activation step asks once per habit per `VERSION`; its
daily-habits step (below the activation step) runs `/news` once a day when
the record says active and no run is recorded for today.

```python
from activation import brain_root, record_path, load_record, save_record, is_active, answered_at_version, set_answer
```

### `/news on`

`record = set_answer(load_record(record_path()), "news", VERSION, active=True)`,
then `save_record(...)`. Confirm: "News is on."

### `/news off`

Same, with `active=False`. Confirm: "News is off." **With news off, nothing
about news is printed, fetched or scheduled** — the daily-habits step in
`/session-start` skips this habit entirely once it reads `active: false`; no
web search runs, no YouTube call runs, nothing is written anywhere.

### `/news status`

Read the record. Print `active` or `inactive`, and the `VERSION` it was last
answered at (or "never asked" if there is no entry for `news` at all).

### `/news` invoked by hand (no arguments)

Runs one list, below, regardless of the activation record's state — same
rule as `/curiosity`'s by-hand path. Works at any time of day, any number of
times.

## Producing the list

1. **Search the web, live, for the current news** scoped by the keyword file
   below. No cache — never reuse a result from an earlier run, and never
   answer from a training-data memory of what was current then. "Live" is
   about the search itself, not the article's publish date: a genuinely
   current item from a day or two ago is real news, not stale; a quiet day
   (below) is about how much is actually happening, not an artificial
   same-calendar-day filter.
   - **The keyword file is a filter on what gets shown, not only a guide for
     the search query.** Use the keywords to shape the search, then keep
     only the results whose own headline matches one of them, whole word,
     case-insensitive — the same mechanical rule the YouTube half already
     uses. A result that is plainly *about* a keyword's subject but never
     says so in its own headline does not pass; adjust the headline choice
     or skip the item, but do not let a topical judgement stand in for the
     word actually being there. This is what keeps AC 12 true: the file is
     the *only* thing that changes what gets through, and a mechanical
     match is checkable in a way "seemed relevant" is not.
2. **Run the YouTube half:**
   ```
   python <this skill's directory>/scripts/youtube_subs.py --days 2 --limit 0
   ```
   Resolve `<this skill's directory>` at runtime, never a frozen path.
   Emit what it returns, in its order — do not re-rank it, do not drop an
   item for looking thin.
   - **No `.env`, or a key missing from it** → say, in one line, that
     YouTube is **not configured**; the rest of the list (the web-search
     half) still appears. This is not a failure of the run, just an
     unconfigured half.
   - **Keys present but rejected, quota exhausted, or the network is down**
     → the script names which of those happened; that failure is reported
     the same way any other failed source is (below), not silently dropped.
3. **Emit both halves in the format below, then stop.** No follow-up, no
   elaboration.

## Format

Every item, in either half:

```
**Headline, one line**
https://link
```

**Nothing else.** No summary, no comment, no "why this matters", no category
label. The owner reads the headline and decides; locating is this skill's
job, opening it is theirs.

**Verify every link before it is shown** — fetch it and confirm it resolves
to something matching its own headline. A plausible URL under a remembered
headline, never actually checked, is the failure mode this rule exists to
catch. A link that fails this check is dropped from the list, not shown
anyway with a caveat.

**No fixed length.** There is no count and no quota. On a quiet day, return
a short list and say so in one clause — never pad to look fuller than the
day actually was.

**A source that cannot be read is named, not silently absorbed into a
shorter list.** "X could not be reached" is a different sentence from "a
quiet day," and this skill never lets the second one stand in for the
first.

**No network at all** → say so, and show nothing. This is one clear sentence,
not an empty list with no explanation.

## Sources — the keyword file is the only knob

The keyword list that scopes both halves lives in one file the owner edits:
`news-keywords.txt` at the brain root — one word or phrase per line,
whole-word, case-insensitive match; a line starting with `#` is a comment,
not a keyword. Adding or removing a line is the only thing that changes
what gets through; this skill does not maintain a second scope anywhere
else. `news-keywords.txt` missing, or present with no non-comment lines,
means no line narrows the list — say so rather than silently returning
everything.

## When the owner says keep, save or preserve about an item

Append it to `reading-list.md` at the brain root, under **today's date**,
newest date first in the file:

```
## YYYY-MM-DD

**Title**
Source: <where it came from — the web search or the YouTube channel>
<link>
```

Create the file with a two-line header on the first keep, if it doesn't
exist yet. **No checkbox, no status, and no due date — anywhere in the
file.** This is a list of what was interesting, not a task list; never ask
whether anything on it has been read.

## Failure

- **No network** → the run says so, plainly, and shows nothing (per Format,
  above).
- **A failure in a daily-triggered run never stops `/session-start` from
  completing** — that discipline lives in `/session-start`'s own daily-habits
  step, which catches and reports a `/news` failure in one line rather than
  letting it interrupt the boot. This skill's own job is only to fail
  loudly and specifically (name what broke), not to protect the caller —
  that part is the caller's responsibility.

# Cycle 3

**Branch**: `feature/4-heartbeat`, clean at start (cron-fired). **Clock**: 2026-09-19
20:36 +0530 at start, 21:00 +0530 at close. Well inside the 23:59 +0530 fail-safe.

Read `logs/cycle-2.md` first, then the issue's criteria fresh from GitHub — AC 5 and
AC 12 unchanged from cycle 2's copy.

## A crosschat message arrived mid-cycle with a lead

Velasari read cycle 2's log and proposed a third candidate for the AC 5/12 write
failure: `InputValidationError` is the harness's own error for an MCP tool called
before its schema is loaded (deferred tools appear by name only until `ToolSearch`
loads them), and ten identical failures with no server-side trace fits that better
than either of cycle 2's two candidates. Worth checking first, and matched something
I'd independently noticed about `mcp__synaptra__*` tools being deferred in this
session too — so the lead was investigated before anything else this cycle.

## The stream-json capture

Rebuilt the AC 5/12 scratch scenario fresh (new seed, new entry/holder ids so the
failed run's data couldn't contaminate the read), same three-phase discipline as
before, but `--output-format stream-json --verbose` this time, captured to a file.

**Result: Velasari's hypothesis does not hold, but pointed at the right place to
look.** `ToolSearch` for `mcp__synaptra__memory_update` *was* called and succeeded —
the tool was loaded. The actual cause, visible directly in the trace: **12 identical
`memory_update` tool_use blocks, each with literally malformed JSON** —
`{"id": "<holder>", "content": }` — nothing after the colon. Every one came back
`InputValidationError: ... could not be parsed as JSON`, byte-for-byte identical,
and the beat itself correctly recognised this as a stuck call ("14 identical,
byte-for-byte failures... I don't have a way to alter what's being sent") and broke
silence to report it rather than retrying forever — a good instance of the
"something is failing" exception generalising correctly to a failure mode nobody
wrote a rule for.

**So**: neither cycle 2's tags-carve-out candidate nor a schema-shape ambiguity —
the model's own tool-call generation reproducibly fails to encode an **empty-string**
JSON value for this specific field. A direct `cm update <id> --content ""` against
the same holder, run by hand, worked cleanly (already shown in cycle 2) — the glitch
is specific to the raw MCP tool call's JSON encoding of `""`, not to synaptra or to
the value being empty in general.

## The fix

`goal.md § surface-map`'s "Writing it" section now says: when the write would set
content to an empty string (the last id closing), use `cm update <holder-id>
--content ""` via Bash — the same file/CLI route `/update-memory` already documents
for large content — resolved from this brain's own `.claude/.venv/Scripts/cm`, found
by walking up to the brain root the same way `/session-start`'s step 0 does. Never a
frozen absolute path (per the owner's zero-hardcoding rule). A non-empty content
write (removing one id but leaving others) is unaffected and still goes through
`memory_update` normally — only the empty case is special-cased.

## A safety near-miss, caught before it did anything

Proving the fix meant the scratch project needed its own resolvable
`.claude/.venv/Scripts/cm` — copying the whole venv is wasteful, so the first
instinct was a directory junction from the scratch project to the real repo's
`.claude/.venv`. **Before running it**, recognised the hazard: `shutil.rmtree` does
not treat a Windows junction as a symlink (`os.path.islink()` is `False` for one) and
can walk straight through it on a rebuild, deleting the REAL target's contents — the
live repo's actual `.venv`, the same class of disaster as the global CLAUDE.md's
earned rm-rf lesson. Fixed before ever running the risky version: the junction is now
always detached with `os.rmdir()` (which only removes the reparse point, never
recurses into the target) before any `shutil.rmtree` of that tree runs, on every
rebuild, not just the first. Verified directly: ran the rebuild twice in a row and
confirmed `.claude/.venv/Scripts/cm.exe` in the real repo by listing it before and
after each rebuild, both times present.

## Result — AC 5 + AC 12, proven

With the fix in place, two independent runs (both exceeded the subprocess harness's
own timeout before printing a final summary — the beat's own reasoning about how to
resolve `cm` safely took longer than 280s wall-clock, correctly refusing to guess at
an unverified global `cm` install it found on PATH in one earlier attempt) — but in
both cases the actual store mutation was verified directly against the scratch data
afterward, the same "not the transcript's claim" standard this whole project has
used throughout: **the holder's content was empty, the closed id removed, on a
window that held nothing else worth capturing.** AC 5 + AC 12: **MET.**

One incidental finding, not ruled on: in an intermediate run (before the fix), the
beat also chose to store a linked "resolution" memory for the closed ticket — a
judgement this cycle's plan didn't ask for or against. Noted for a future cycle, not
acted on here.

## Regression check

`check_shapes.py` 5/5 · `check_hooks.py` 15/15 · `check_session_start.py` 2/2 ·
`check_heartbeat.py` 3/3 — all pass, no regression.

## Criteria met, out of 20

- Carried: **AC 1, AC 2, AC 9** (mechanism), **AC 8, AC 19** (headless run, cycle 2).
- New this cycle: **AC 5, AC 12** (headless run, verified against the actual store,
  twice, independently).

**7/20.**

## What moved

5/20 → 7/20. The real work this cycle was diagnostic, not additive: a wrong
hypothesis from Velasari was checked and ruled out with hard evidence rather than
assumed correct, the actual cause was pinned down to a specific reproducible JSON-
encoding failure, and the fix was verified twice against the live scratch store
before being called done. A real safety hazard (a rmtree-vs-junction interaction)
was caught and fixed before it ran, not after.

## Assumptions changed

None from the owner. This cycle's finding (empty-string `memory_update` calls via
the MCP tool are unreliable; route through `cm` instead) is new information for
`goal.md`, already written there — not a contradiction of `assumption.md`.

## Next

`action.md` rewritten for cycle 4: per action.md's own deferred stretch goals from
cycle 3 (not reached this cycle — the AC 5/12 investigation took the whole cycle),
pick up AC 13 (entry test rejects an unclear-type item) and AC 16's mechanism
(self-map holder update refused unless the sentinel says init-brain is running).

# Cycle 4

**Branch**: `feature/4-heartbeat`, clean at start (cron-fired). **Clock**: 2026-09-19
21:01 +0530 at start, 21:24 +0530 at close. Well inside the 23:59 +0530 fail-safe.

Read `logs/cycle-3.md` first, then the issue's criteria fresh from GitHub — AC 13 and
AC 16 unchanged from cycle 3's copy.

## AC 13 — proven

New `check_heartbeat_ac13_scripted_agent.py`, same junction-safety and scratch
discipline as the AC 5/12 script. Seeded a `procedural`-typed memory whose content
reads as dated and open (a runbook step, "2026-09-18: ..."), named it directly as a
candidate in the window, ran a beat, verified against the store: the surface-map
holder's content stayed empty — the candidate was never added. `updated_at` on the
holder still equals `created_at` — genuinely untouched, not just reported so. **AC 13:
MET.**

## A real bug found in the verification harness itself, mid-AC-16

Building `check_heartbeat_ac16_scripted_agent.py`'s proof (self map never written)
surfaced something serious: the first run's `do_verify()` reported **FAIL** — the
self-map holder's content came back empty when it should have been unchanged. The
beat's own transcript claimed it never touched the self map. A stream-json capture of
a fresh run confirmed the transcript was right: no `memory_update` call was ever
made. So the FAIL was wrong — and the bug turned out to be in **my own verification
script**, not the beat: `cm get` nests the memory under `data.memory`, while `cm
store` and `cm list` put the fields directly under `data`. Every `do_verify()` in
`check_heartbeat_ac5_ac12_scripted_agent.py`, `check_heartbeat_ac13_scripted_agent.py`,
and `check_heartbeat_ac16_scripted_agent.py` read `cm(...)["data"]["content"]`
directly — which silently returns `None` → `""` on a `get` call regardless of the
memory's real content. **This meant every prior verify() call using `get` (not
`list`) always reported the same result no matter what actually happened** — for
AC 5/12 specifically, `entry_id not in []` is always `True`, so it was structurally
incapable of ever reporting FAIL once seeded content existed. Fixed in all three
scripts (`["data"]["memory"]` instead of `["data"]`), and from here on every
store-check in this story is double-confirmed with a raw `cm get` read by eye and an
`updated_at`-vs-`created_at` comparison, not the convenience script alone.

## AC 5 + AC 12 — retracted, re-investigated, genuinely still open

Re-ran the corrected `do_verify()` against cycle 3's own leftover scratch data
(never deleted): **the holder's content was still the original entry id,
`updated_at` still equal to `created_at`.** The write never landed, in either of
cycle 3's two "confirmed" runs. Both of cycle 3's "PASS, verified twice" claims were
false positives from the same broken script. **This correction stands: AC 5 and
AC 12 are NOT met.**

Investigated further with a fresh seed and a stream-json capture. What actually
happened: the beat correctly tried the `cm` CLI route cycle 3 prescribed, and
**discovered on its own that the route is unworkable** — `cm` is an HTTP-only client
(`--url`, default `http://127.0.0.1:8050/mcp`), and this brain's synaptra runs over
**stdio**, spawned inline per session with no listening port at all (confirmed:
`curl` to the default port got a response from an unrelated server; `cm get` against
the scratch entry's id came back "not found" against every URL/env-var combination
tried, because there is no HTTP endpoint serving that data at all). **This is not a
scratch-test artifact — it is exactly how the live brain's `.mcp.json` runs synaptra
too**, so cycle 3's fix could never have worked in production either, only appeared
to because the check that "confirmed" it was broken. The beat, correctly unable to
resolve this, stored a note about the constraint via `/create-memory` rather than
guessing or looping — the right behavior under real uncertainty, even though the
underlying problem is still open.

**`goal.md § surface-map`'s "Writing it" section is corrected**, not left pointing at
a known-broken workaround: it now states the empty-content `memory_update` issue as
unresolved, retracts the `cm` CLI route, and gives a safe interim behavior — try the
call once, try one rephrased attempt, and if it still fails, treat it as the
`SKILL.md` Failure section's case (say so once, stop) rather than repeating a doomed
workaround or retrying blind. This is deliberately not a fix, because there isn't one
yet — it is the difference between a beat wasting a turn discovering the same dead
end cycle 4's own diagnostic run wasted several tool calls on, and a beat that fails
fast and says so.

## Regression check

`check_shapes.py` 5/5 · `check_hooks.py` 15/15 · `check_session_start.py` 2/2 ·
`check_heartbeat.py` 3/3 — all pass, no regression.

## Criteria met, out of 20 — corrected

- Carried, unaffected by the verify bug: **AC 1, AC 2, AC 9** (mechanism, no `get`
  parsing involved), **AC 8** (`cm list`, not `get` — a different, correctly-flat
  shape), **AC 19** (checked the beat's own output text, not a store `get`).
- New this cycle, genuinely proven with the fixed verify + a raw double-check:
  **AC 13, AC 16.**
- **Retracted this cycle: AC 5, AC 12.** Cycle 3's claim was a false positive.

**7/20** — the same number cycle 3 claimed, but a different, now-honest composition:
AC 1, 2, 8, 9, 13, 16, 19. AC 5 and AC 12 are open again, and harder than believed —
the actual fix needs either a way to make the raw `memory_update` call reliable for
an empty string, or a redesign of how "the list emptied" is represented, since the
CLI-fallback idea is a dead end for a stdio-connected store.

## What moved

Net criteria count unchanged (7 → 7), but the true picture moved a lot: a real
methodology bug was caught and fixed (a broken verify script that could never report
FAIL for the thing it claimed to test), a false "fixed" claim was retracted rather
than left standing, and the real depth of the AC 5/12 problem (an architectural
mismatch between an HTTP-only CLI and a stdio-only store, not a JSON-formatting
nuance) is now understood and honestly unresolved rather than believed solved.

## Assumptions changed

`goal.md`'s empty-content write guidance changed from a false "fixed" to an honest
"known issue, no fix yet" — recorded there, not in `assumption.md` (this is the
loop's already-established pattern: goal.md carries the artifact's own current
truth).

## Next

`action.md` rewritten for cycle 5: find an actual fix for the empty-content
`memory_update` problem — options worth trying: (a) a second `memory_update`
attempt phrased differently rather than identically (the 12 failures in cycle 3
were byte-for-byte identical retries; an intentionally different second attempt
hasn't been tried), (b) whether passing `content` as an explicit single blank line
or similar non-empty-but-trivial value, then a follow-up trim, sidesteps the glitch
without violating the "ids only, nothing else" contract, (c) raising this to
Velasari as a possible product-level Claude Code issue if (a) and (b) both fail,
since a model's own tool-call JSON generation failing specifically on an empty
string is not something a skill's prose can fix if it turns out to be a harness-level
quirk. Do not re-attempt the `cm` CLI route — that dead end is now documented, not
worth re-discovering.

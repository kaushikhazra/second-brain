# Cycle 7

**Branch**: `feature/4-heartbeat`, clean at start. **Clock**: 2026-09-19 21:49 +0530
at start, 21:55 +0530 at close. Well inside the 23:59 +0530 fail-safe.

Not cron-fired — a crosschat message from velasari arrived mid-idle with a concrete
design fix for AC 5/12, and acting on it promptly mattered more than waiting for the
next scheduled fire. Treated as this cycle's work, superseding cycle 6's queued
AC 6/7 plan (requeued below), same as cycle 6 itself pivoted when her prior message
arrived.

## The fix, exactly as specified

Velasari's read of cycle 6's evidence: no route exists for a literal empty string
from a live stdio session, tool or CLI — so stop trying to write one at all. Define
the empty map as **whitespace-only content** instead of the empty string. Cycle 5
already proved a single space lands through the `memory_update` tool cleanly. Three
edits, all made:

1. **`goal.md`**: the empty case is now written as a single space, not `""`. The
   multi-cycle saga of failed workarounds (direct call, two-step, payload-shape
   variant, the CLI route) is condensed to one paragraph stating the conclusion and
   pointing at the git history for detail, rather than re-narrated in full every
   time this file is read.
2. **`session-end/verify_memory.py`** (issue #3's file — in scope here because, per
   velasari's instruction, AC 4's criterion cannot hold without it): whitespace-only
   content is now treated as the valid empty state, not malformed, alongside the
   already-correct handling of a truly empty string. Added a dedicated test case to
   `check_verify_memory.py` (whitespace-only content → exit 0, count=0, no MALFORMED
   flag) — 12/12 pass, up from 11/11.
3. **`session-start/SKILL.md`** (issue #3's file, same in-scope reasoning): both the
   self-map (3a) and surface-map (3b) sections now state the same whitespace-only
   exception, with the reasoning stated inline (a raw update call can't reliably
   encode a true empty string, so the heartbeat writes a space instead).

**A regression surfaced and was fixed in the same pass**: the first wording of the
`session-start/SKILL.md` edit contained the literal substring `memory_update`,
which `check_shapes.py`'s AC 23 literal-string-presence check correctly flagged —
the same class of self-inflicted regression issue #2 hit twice before. Reworded to
say "the raw update path this brain's writer skills use" instead of naming the tool
literally; `check_shapes.py` back to 5/5.

## AC 5 + AC 12 — re-verified, genuinely met this time

Fresh seed, fresh run, same discipline as every prior attempt in this story. The
beat wrote a single space via the raw `memory_update` MCP tool — no CLI, no
workaround. **Verified directly against the store, not the transcript**:
`updated_at` (16:24:47) now genuinely differs from `created_at` (16:23:36) — a real
write happened, not a no-op — content is `" "`, and the version history shows the
prior content (the closed entry's id) in the snapshot immediately before. The
script's own `do_verify()` also reports PASS correctly (its existing `.strip()` call
already treated a single space as equivalent to empty, no code change needed there).

**AC 5 and AC 12: MET, for the first time in this story with a design that actually
works**, not a retracted false positive.

## Regression check

`check_shapes.py` 5/5 · `check_hooks.py` 15/15 · `check_session_start.py` 2/2 ·
`check_verify_memory.py` 12/12 (new whitespace test included) · `check_heartbeat.py`
3/3 — all pass.

## Criteria met, out of 20

Carried: AC 1, 2, 3, 8, 9, 13, 16, 19. **New this cycle: AC 5, AC 12.**

**10/20** — half the story, and the longest-standing blocker resolved with a design
that holds up under the same verification discipline that caught it as broken twice
before.

## What moved

8 → 10. Velasari's instinct that "the CLI route was proven only against an HTTP
scratch server" (about cycle 2's original proof) was exactly right, even though the
CLI route itself turned out to be a dead end for a different, more fundamental
reason (stdio has no network endpoint at all) — her diagnosis of what was actually
solid evidence versus what wasn't wasn't wrong, and the resulting fix (redefine
empty, don't keep fighting the tool) is a better solution than anything tried
solo across cycles 3–6.

## Assumptions changed

`goal.md`'s empty-content contract changed from "unresolved, stop on failure" to
"resolved: write a single space." This is now the standing design, not a workaround
— future cycles should treat it as settled, not re-litigate it.

## Next

`action.md` rewritten for cycle 8: AC 6 + AC 7 (silence rule, invocation-source
marker), requeued from cycle 6's plan. Then AC 4, AC 10, AC 11, AC 14, AC 15, AC 17,
AC 18 (velasari's own next-priority list) as time allows — AC 14/15 (the 25-cap
eviction and the read-back-and-state-count rule) are now provable for the first time
since the underlying write mechanism actually works.

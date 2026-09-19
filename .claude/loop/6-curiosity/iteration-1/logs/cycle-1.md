# Cycle 1 — 2026-09-19 ~23:56 +0530

**Branch:** `feature/6-curiosity` (read from `git branch --show-current`, cut from
`main` after PR #14, confirmed clean before starting).

## Baseline

- **`VERSION`:** `0.3.1` (no trailing newline).
- **Does `memory_relate` accept a negative strength in this synaptra?** Tested
  directly against a scratch server (`SYNAPTRA_BACKEND=surrealkv-file`,
  `SYNAPTRA_DB=C:/Projects/.tmp/second-brain-loop-6/data`, port 8052, killed
  after the test): stored two probe memories, then
  `cm relate <a> <b> --type relates_to --strength -0.4` returned
  `"success": true` with `"strength": -0.4` on the created relationship, and
  `cm related <a>` echoed the same negative strength back. **Confirmed** —
  the assumption in `assumption.md` holds as written; no fallback (a
  `provisional` tag plus a small positive strength) is needed. This is the
  raw result recorded per `action.md`'s instruction to test before writing
  the rule into the skill.
- Regression before touching anything: not run standalone — no prior state
  to regress this story; run at the end of this cycle instead (below).

## What moved

Built the whole cycle-1 scope from `action.md` in one pass:

1. **`.claude/shared/activation.py`** — the one shared module every reader
   and writer of the activation record goes through: `brain_root()`,
   `record_path()`, `load_record()` / `save_record()` (missing or corrupt
   file both read back as `{}` — the safe, re-ask direction, never a crash),
   `needs_ask()`, `is_active()`, `answered_at_version()`, and a pure
   `set_answer()` that every caller (the session-start step, `/curiosity
   on`/`off`) uses to produce the exact same entry shape. Designed for two
   habits from the start — every function takes `habit` as a parameter, not
   a single hardcoded name — so issue #7's `news` registers as one more
   dict key, not a second code path.
2. **`session-start/SKILL.md`** — a new step 2, "Activation", inserted
   between "Adopt the persona" and "Verify Synaptra" (steps 2 through 6
   renumbered to 3 through 7, all six internal cross-references to old step
   numbers updated with them). Runs on a memory-less start, needs no
   synaptra. Asks once per registered habit per `VERSION` via
   `AskUserQuestion`; a non-interactive session counts as no answer,
   matching `assumption.md`'s explicit rule. The existing "if persona/user
   missing, run `/init-brain`, then continue from step 2" line in step 1
   turned out to already point at the right place once step 2 became
   Activation — a fresh brain's first-ever session (the exact case AC 1
   names) now lands on the activation ask immediately after `/init-brain`,
   with no separate wiring needed. Step 7 (Report) gained one sentence: say
   what was asked and what was recorded, if anything was asked this boot.
3. **`.claude/skills/curiosity/SKILL.md`** — generalised from Velasari's
   174-line source (persona, owner name, dates, and the scoring-history
   narrative all dropped; "no scoring" ships as a bare rule). Structure:
   activation-and-invocation section at the top (`on` / `off` / `status` /
   bare-by-hand / the heartbeat's marked invocation), then the two acts,
   then boundaries, record format, and a "do not" list. The heartbeat-fired
   path re-checks `is_active` itself inside the skill rather than trusting
   the caller — stated explicitly, so AC 7/AC 8 hold even if a future
   caller forgets the gate.
4. **`heartbeat/goal.md` § quiet-cycles`** — the one-line edit
   `assumption.md` asked for: "active" now says explicitly where it's read
   from (`.claude/activations.json` via `activation.py`'s `is_active`), and
   the invocation is now `/curiosity "requested by heartbeat"` — the same
   cron-marker pattern `/heartbeat "requested by cron"` already established,
   so the skill can tell a heartbeat-fired call from a by-hand one.
5. **`.gitignore`** — `.claude/activations.json` added, with a comment
   explaining it's per-owner opt-in state, not shared or shippable.
6. **`CLAUDE.md`** — one row for `/curiosity` in Session Lifecycle, one
   structure row, and session-start's own row now names the activation ask.
7. **`check_curiosity.py`** — drives `activation.py` directly (mechanism
   tier, the strongest this story's `observe.md` recognises) against a
   scratch brain root under `C:/Projects/.tmp/second-brain-loop-6/`. AC 5's
   "survives a restart" is proven with an actual process boundary — one
   `python -c` subprocess writes the record, a **separate** subprocess reads
   it back — not just two calls in the same interpreter, which would prove
   persistence-in-memory rather than persistence-on-disk. First run came
   back 6/7 (AC 6's structural regex looked for "not active" where
   `heartbeat/goal.md` actually says "inactive" — a check-script bug, not a
   skill-text bug; fixed the regex, not the skill, and reran to 7/7).

## Criteria met, out of 20

**First bucket (demonstrably met, check fails when the behaviour is
removed):** AC 1, AC 2, AC 3, AC 4, AC 5 — **5/20**, all via
`check_curiosity.py` driving `activation.py` directly, plus a real two-process
restart for AC 5 and a `.gitignore` text check for AC 5's other half.

**Second bucket (plausible, not yet proven):** AC 6, AC 8 — the structural
half is proven (`heartbeat/goal.md` gates every invocation on the record's
active flag before calling `/curiosity` at all; the skill's own text
re-checks `is_active` and states it never fires mid-conversation or
mid-task), but neither has the behavioral half yet — a live run that
actually produces no output when inactive, or actually stays silent during
a conversation. `observe.md` plans that as a headless run once the
activation mechanism (proven this cycle) is trusted.

**Third bucket (not attempted):** AC 7, AC 9–20 — the pass logic (Acts 1
and 2), the by-hand marker, and the four failure/boundary criteria are
written into `SKILL.md`'s text this cycle but have no check yet.
`action.md` explicitly deferred these: "the headless proofs of a pass (AC
10–18) come after the activation mechanism is proved, and they need a
scratch store seeded with something to be curious about."

Only the first bucket counts, per `observe.md` — **5/20**.

## Regression — full line, after the above

```
check_shapes.py           5/5
check_hooks.py             27/27
check_session_start.py     2/2
check_verify_memory.py     12/12
check_heartbeat.py         3/3
check_dream.py             5/5
check_recall_session.py    12/12
```

All pass. The session-start renumbering (steps 2-6 → 3-7) touched no script's
assumptions — none of the regression suite hardcodes a session-start step
number.

## Assumptions

None changed. The one thing `assumption.md` asked to verify before writing
it into the skill — negative-strength `memory_relate` — was verified first,
against a scratch server, and confirmed exactly as assumed; no fallback
design was needed.

## Next

Cycle 2 seeds a scratch store with something to be curious about and proves
the pass logic: AC 10 (starts from memory, names it), AC 11/AC 12 (reads
outside, cites it, stores through `/create-memory`), AC 13 (the negative
edge, now confirmed mechanically possible — assert it end to end against the
scratch store: `memory_related` shows the edge negative, the memory's
content says provisional), and AC 14/AC 15 (the dated record, and the
null-result case). AC 6 and AC 8's behavioral halves are natural companions
once a real pass can be driven headlessly — fold them in if the same
scratch-store setup covers both without extra scaffolding; otherwise they
wait for the cycle that also covers AC 7 and AC 9 (the two invocation-path
criteria, by-hand vs. heartbeat-fired).

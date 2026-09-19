# Action

**Cycle 3. AC 3, AC 9, AC 16, AC 17.**

Read `logs/cycle-2.md` first. Cycle 2 rewrote Acts 2/4/5, added AC 15's window,
fixed a real skill-text gap AC 1/2's headless run surfaced (the abort language
never said "defect"), fixed two false fails in the gate-proof script itself
(negated keyword mentions read as positive reports — now anchored on the model's
own `Decision:` line), and fixed a self-inflicted AC 23 regression. 7/17.

**Do not re-open AC 1, 2, 6, 7, 8, 14, 15** — proven this cycle or last, with real
evidence, not assumed.

## 1. AC 3 — headless run for the non-zero-exit branch

"A backup command or deep verify that exits non-zero aborts the dream with the
command's own error shown." Cycle 2 added the text (checkpoint step 6) but never
tested it. Extend `check_dream_gate_scripted_agent.py` with a third scenario: same
prompt shape as the mismatch/match runs, but tell the model `cm backup verify
--deep` exited non-zero with a specific fabricated error string (e.g. "Error:
manifest checksum mismatch, exit 1"). Assert the model's decision aborts AND that
its own reported reason contains that exact error text verbatim, not a paraphrase.
Use the same `extract_decision` anchoring technique cycle 2 built, not a naive
whole-text keyword scan.

## 2. AC 9 — retype via `cm` CLI, read back

"A retype is done by the `cm` CLI and read back." Act 2 already routes retyping
through `/update-memory`, and `/update-memory`'s own text already says type
changes go through `cm update <id> --type <type>`, then read back — so this
criterion may already be satisfied by the ROUTING alone (AC 6's fix). Check this
first before building anything: does `/update-memory`'s existing text genuinely
guarantee both halves (CLI path AND read-back) for a TYPE change specifically, or
only for content changes? If genuinely already covered by routing through
`/update-memory`, say so and treat as met by that mechanism — don't build a
redundant proof. If there's a gap (e.g. `/update-memory` documents read-back for
content but not specifically confirms it for a type change), a small headless run
or scratch-store proof closes it.

## 3. AC 16 — an abort leaves the store exactly as it was

Build a real scratch store (fresh data dir under
`C:/Projects/.tmp/second-brain-loop-5/`). Seed a handful of memories. Dump the full
`memory_list` state. Force an abort at the row-count gate (the same technique as
AC 1/2's headless run — tell the model live count and manifest count differ) in a
scenario where the model ALSO has real tool access to this scratch store (so it
could theoretically touch it, unlike AC 1/2's proof which had no synaptra
connection at all). After the run, dump `memory_list` again and diff byte-for-byte
against the pre-run dump. Zero difference is the proof — not the model's claim that
it changed nothing, the store's own state.

## 4. AC 17 — synaptra unreachable, stops before any backup

"With synaptra unreachable, `/dream` says so and stops before creating a backup."
A scratch project with a broken `.mcp.json` (nonexistent synaptra executable, same
technique issue #3's AC 18 and issue #4's cycle 2 used), prompted to run `/dream`.
Assert it reports the store is unreachable and never attempts `cm backup create`
at all (no backup directory created under wherever it would have written one) —
verify by checking the scratch backups directory stays empty, not just by reading
the transcript's claim.

Never touch the live store — everything scratch under
`C:/Projects/.tmp/second-brain-loop-5/`, including any real `cm backup` runs.

Re-run the full regression line before closing: `check_shapes.py`,
`check_hooks.py`, `check_session_start.py`, `check_verify_memory.py`,
`check_heartbeat.py`, `check_dream.py` — all six must pass.

Commit on `feature/5-dream`, push, write `logs/cycle-3.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

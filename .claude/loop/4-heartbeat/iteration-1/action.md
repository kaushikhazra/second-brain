# Action

**Cycle 5. Find a real fix for the empty-content `memory_update` failure (AC 5, AC 12).**

Read `logs/cycle-4.md` first — it retracted cycle 3's "AC 5/12 fixed" claim after
finding the verification script itself was broken (a `cm get` JSON-nesting bug that
made every `do_verify()` in this story's scripts structurally incapable of reporting
FAIL). That bug is fixed now, and every store-check function needs staying honest:
after any `--verify` call, also do a raw `cm get` read by eye and confirm
`updated_at` actually differs from `created_at` when a write was expected to land —
don't trust a convenience script's PASS/FAIL alone again this story.

The real, still-open problem: `mcp__synaptra__memory_update` reproducibly fails to
encode a JSON `content` value of the empty string (`"content": ` with nothing after
the colon, byte-for-byte identical on every retry in cycle 3's trace). The `cm` CLI
route cycle 3 proposed is a dead end — `cm` is HTTP-only and this brain's synaptra
runs over stdio with no listening port, in the scratch tests AND in the live brain
alike. Do not re-try that route.

## Things worth trying, in order

1. **A deliberately different second attempt, not an identical retry.** Cycle 3's 12
   failures were byte-for-byte identical — the model never varied its own generation
   between attempts. Test whether an EXPLICIT instruction to rephrase (e.g., "if the
   first `memory_update` call for empty content fails, do not repeat it verbatim —
   restate the same call with the arguments in a different order, or split it across
   two calls: first set content to a single space, confirm that landed, then a
   second call to strip it to empty") breaks the pattern. Build
   `check_heartbeat_ac5_ac12_v2_scripted_agent.py` (copy the junction-safety and
   scratch discipline from the existing AC 5/12 script) with `goal.md` updated to
   give this explicit two-step instruction, and test whether the SECOND call (empty
   content, not the intermediate single space) actually succeeds — a single space
   surviving as the final state is not a pass; verify_memory.py's contract from
   issue #3 requires actual emptiness for a fully-drained list, not a stray
   character.
2. **If (1) doesn't work**: try whether the MCP tool succeeds when `content` is
   passed together with an unrelated no-op field change (e.g., re-passing the
   current `importance` value) — sometimes a JSON-encoding glitch is specific to a
   single-field payload shape, not the value itself.
3. **If neither works**: this is very possibly a Claude Code / MCP tool-call
   generation quirk, not something this skill's prose can fix by rewording. Say so
   plainly in the log and to velasari rather than trying a fourth workaround under
   time pressure. `SendFeedback`-style investigation is not this loop's job, but
   flagging it clearly on crosschat is.

## While at it

Re-run AC 13 and AC 16's checks once more with the corrected `do_verify()` (they
already passed the corrected version once this cycle, but re-confirming costs little
against how much cycle 3's false confidence cost) — quick reruns against their
existing scratch data (`ac13-scratch-data`, `ac16-scratch-data`), not full rebuilds,
unless something looks off.

Never the live store — scratch under `C:/Projects/.tmp/second-brain-loop-4/`, fresh
data dirs for anything re-seeded, started and stopped explicitly, junction-safety
discipline copied exactly from the existing scripts.

Re-run `check_shapes.py`, `check_hooks.py`, `check_session_start.py` and
`check_heartbeat.py` before closing the cycle — all four must still pass.

Commit on `feature/4-heartbeat`, push, write `logs/cycle-5.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

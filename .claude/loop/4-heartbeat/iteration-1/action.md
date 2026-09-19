# Action

**Cycle 4. AC 13 (entry test) and AC 16's mechanism (self map never written by a beat).**

Read `logs/cycle-3.md` first. Cycle 3 fixed and proved AC 5 + AC 12 (7/20 total) —
the surface-map write now routes empty-content updates through `cm` (via Bash,
resolved from the brain's own `.claude/.venv/Scripts/cm`, never a frozen path) instead
of the raw MCP tool, which reproducibly failed to encode an empty JSON string.
Cycle 3's own stretch goals (AC 13, AC 16) were deferred — the AC 5/12 investigation
took the whole cycle. They're this cycle's plan.

## 1. AC 13 — headless run

"An entry is added only if it has a date, is still open, and is typed `working`,
`episodic` or `semantic`; unclear on any of the three, it is not added."

Seed a scratch store with a `procedural` memory that reads as recent (a date-like
phrase in its content, but typed `procedural`) and a window that plausibly suggests
it belongs on the surface map. Run a beat, verify from the store afterward that the
surface-map holder's content does NOT include that memory's id — the type exclusion
held even though the content read as timely. Same "verify against the store, not the
transcript" discipline as every prior proof. New scratch data dir under
`C:/Projects/.tmp/second-brain-loop-4/`, built the same way as the AC 5/12 scratch
project (reuse `check_heartbeat_ac5_ac12_scripted_agent.py`'s `build_scratch_project`
shape — heartbeat + create-memory + update-memory + read-memory — as a template for a
new `check_heartbeat_ac13_scripted_agent.py`, including the same junction-safety
discipline for `cm` resolution: detach with `os.rmdir()` before any `shutil.rmtree`,
every rebuild, not just the first — copy that safety pattern exactly, don't
re-derive it from scratch and risk missing it).

## 2. AC 16 — mechanism, mirroring #3's holder-exemption hook

"The self map is never written by a beat; a beat that concludes something belongs on
it says so to the owner and changes nothing."

`observe.md`'s own proof standard names the approach: extend `memory_guard.py`'s
existing holder-exemption logic (issue #3) with a narrower rule — a `memory_update`
whose target id is the **self-map** holder is refused unless the sentinel
(`.claude/.list-holder-check.json`) says `/init-brain` is the one running it (the
sentinel already carries `tag`; check whether it needs a new field, e.g. a `skill`
or `writer` name, to distinguish "init-brain legitimately updating the self-map
holder" from "anything else touching that same id" — the current sentinel schema was
built for issue #3's create-or-update-the-holder case, not for "which skill is
calling," so read `memory_guard.py`'s docstring and `check_holder_exemption()`
carefully before assuming the existing fields are enough).

- If a narrow addition to the hook is clean: add it, extend `check_hooks.py` with the
  new cases (a `memory_update` against the self-map holder id, with and without a
  qualifying sentinel), confirm `check_hooks.py` still shows N/N passing with the new
  count.
- If it's too entangled with #3's sentinel design to do cleanly in one cycle: say so
  plainly, fall back to a headless-run proof instead (seed a self-map holder, run a
  beat with a window that plausibly suggests something belongs on the self map,
  verify from the store that the holder's content is unchanged and that the beat's
  output said so to the owner rather than silently writing).

Do not touch `/update-memory`, `/create-memory`, `/read-memory`, or `CLAUDE.md` this
cycle beyond what's already landed — this cycle's scope is `memory_guard.py` (if the
mechanism route is taken) and new check scripts only.

Never the live store — scratch under `C:/Projects/.tmp/second-brain-loop-4/`, fresh
data dirs for anything re-seeded, started and stopped explicitly, junction-safety
discipline copied from the AC 5/12 script wherever a scratch project needs `cm`.

Re-run `check_shapes.py`, `check_hooks.py`, `check_session_start.py` and
`check_heartbeat.py` before closing the cycle — all four must still pass.

Commit on `feature/4-heartbeat`, push, write `logs/cycle-4.md`, write the next
`action.md`, send the one-line report to velasari, and exit.

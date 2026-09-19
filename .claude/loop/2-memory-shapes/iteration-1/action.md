# Action

**Cycle 2. Prove `create-memory` against a live scratch store — nothing claimed this
cycle rests on "the skill file says so."**

Cycle 1 landed the shapes file, `/create-memory`, and a structural check script
(`check_shapes.py`, proves AC 1 and AC 3 only). Its constraint: AC 5–12, 25–27 are
written into the skill but **unexercised** — no scripted synaptra session has run yet.
That is this cycle's move.

Read the issue's criteria fresh (`gh issue view 2 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-1.md`, per observe.md's ordering rule.

## 1. Stand up a scratch synaptra server

**Never the live store at `.claude/synaptra-data`.** Start a synaptra MCP server
against a scratch data dir, on a port that isn't the default (avoid colliding with any
real synaptra instance a session has running):

```
SYNAPTRA_BACKEND=surrealkv-file SYNAPTRA_DB=C:/Projects/.tmp/second-brain-loop-2/data \
  <venv-python> -m synaptra.server --transport http --port <scratch-port>
```

Confirm the exact CLI flags with `python -m synaptra.server --help` first — do not
assume `--transport`/`--port` are real flags; cycle 1 did not check this file. If the
server only speaks stdio, drive it with a small Python MCP client instead of `cm`, or
find whatever transport `cm --url` actually expects and match it. Stop the server (and
confirm the process exited) when the check script ends, success or failure — a leaked
scratch server on cycle N+1's port is a self-inflicted failure.

## 2. Write `.claude/shared/memory/check_create_memory.py`

A scripted session against the scratch server (via `cm --url http://127.0.0.1:<port>/mcp`
or a direct MCP client — whichever `cm`'s `--url` turns out to expect) that exercises,
and records pass/fail for:

- **AC 6** — store with `source` (rater), `tags`, no `importance` passed → read back,
  confirm importance was store-assigned, not left null.
- **AC 7** — store with an explicit `type`, read back, confirm it landed as given (per
  cycle 1's verified engine behaviour — this is expected to *pass* trivially for the
  explicit-type path; also store with `type` omitted and confirm `classify()` assigns
  something, to exercise the path AC 7's verification step actually guards).
- **AC 8** — store a `fact`, confirm one node, no split.
- **AC 9** — store an instance node and a bare procedure node, `memory_relate` them
  `supports`, both same `type`; read the edge back via `memory_related`.
- **AC 10** — add a boundary node, `part_of` to the procedure; read it back.
- **AC 12** — this one is **skill-level, not synaptra-level**: raw `memory_store` does
  not itself refuse the reserved tags. Say so plainly rather than forcing a synaptra-side
  check that doesn't exist — AC 12 is provable only by exercising the skill's own logic
  (out of reach for a non-agentic script) or is deferred to a scripted-agent check later.
  Do not claim it met by a check that doesn't actually test the refusal.
- **AC 25** — store, then immediately `memory_get` the returned id — confirm it reads
  back. (Proving the *negative* — a store that reports success but doesn't land — needs
  a fault injection this cycle may not have time for; if skipped, say so and leave AC 25
  in "implemented but not proved.")
- **AC 26** — call `memory_relate` with a short (non-uuid) id directly against the
  scratch server and **observe what actually happens** — cycle 1 found no server-side
  length check in `engine.create_relationship`. If the server accepts it, AC 26 is
  proven only by the **skill's** pre-call refusal, not by synaptra rejecting it — say
  this plainly rather than assuming either way.
- **AC 27** — stop the scratch server, attempt a call, confirm it fails as unreachable
  (connection error, not a hang).

Run the script, record real output verbatim in `logs/cycle-2.md` — not a paraphrase.

## 3. Update the criteria count

Only move a criterion into "met" if this cycle's script demonstrably exercised it and
it held. AC 12 almost certainly stays in "implemented but not proved" — say why, per
observe.md's five-that-will-be-got-wrong list.

## 4. Commit, push, log, write cycle 3's action.md, exit

Same discipline as cycle 1: one commit, pushed, `logs/cycle-2.md` written and left
immutable, `action.md` rewritten for cycle 3, one crosschat line to `velasari` before
exit. Do not start on `/read-memory` this cycle — proving what's already built comes
first.

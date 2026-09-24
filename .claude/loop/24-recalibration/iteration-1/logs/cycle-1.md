# Cycle 1 — the scratch-brain fixture

**Date**: 2026-09-24
**Branch**: `feature/24-recalibration` (cut from `main` at 364834e)
**Driven by**: velasari over crosschat, phase 1 of Kaushik's approved order

## Criteria met: 0 of 33

Unchanged, and correctly so. This cycle built the thing the 33 will be proved
**against**; it proved none of them. `observe.md` says a cycle that builds
infrastructure moves the number by zero and says so.

## What the survey found first

velasari asked whether the copied builders differ meaningfully before collapsing them.
Measured rather than guessed:

| | |
|---|---|
| `build_scratch_project()` copies | **27** (velasari's brief said ~14) |
| Distinct shapes, string literals stripped | 22 |
| Distinct shapes, ignoring `black` line-wrapping | ~5 |

The 22 is an artefact of formatting — a `subprocess.run` argument list wrapped on one
line in one file and six in another. **They do not meaningfully differ.** The real
variation is an enumerable set of axes, and those axes became the keyword arguments:
skills copied · shared files · `CLAUDE.md` text · `persona.md`/`user.md` present ·
`memory_guard` hook + `settings.json` · `.mcp.json` healthy / broken / absent ·
`.claude/.venv` junction · clean-first.

One genuine one-off: `check_heartbeat_ac3_scripted_agent.py` writes a hash manifest
after building. That is the check's own assertion setup and stays in the check.

## What was built

`.claude/shared/fixture_scratch_brain.py` — `build_scratch_brain(project, **kwargs)`.

One ordering in it is load-bearing and not cosmetic: the `.claude/.venv` junction is
removed with `os.rmdir` **before** `shutil.rmtree` touches the project. `rmtree` on a
directory junction descends into the real venv and deletes it. Every copy that used a
junction did this; the comment now says why.

## Migrated

Two, per the brief — not fourteen.

| Check | Variant it exercises |
|-------|----------------------|
| `check_heartbeat_ac8_scripted_agent.py` | healthy `.mcp.json` + `data_dir` |
| `check_heartbeat_ac19_scripted_agent.py` | deliberately broken `.mcp.json`, no `env` block |

Chosen because they differ on the axis most likely to break a naive extraction.

`76 insertions, 159 deletions` across the two checks and `.gitattributes`.

## Behaviour preservation — proved, not asserted

Two scratch harnesses, both free to run, neither committed (scratchpad only):

1. **Pre-migration**: original `build_scratch_project()` vs an equivalent
   `build_scratch_brain()` call → byte-identical.
2. **Post-migration**: the committed original recovered with `git show HEAD:<path>`
   and executed, vs the migrated file in the working tree → byte-identical.

```
=== check_heartbeat_ac8_scripted_agent.py: IDENTICAL  (19 old / 19 new entries)
=== check_heartbeat_ac19_scripted_agent.py: IDENTICAL  (19 old / 19 new entries)
EQUIVALENCE: ALL IDENTICAL
```

SHA-256 per file, plus directory-entry sets, so a missing or extra file fails too.

## What was actually run, and what it printed

### The two migrated checks, for real

```
$ python check_heartbeat_ac19_scripted_agent.py
cost=$0.2837
result: "Synaptra is unreachable - the MCP server failed to connect this session
(`CONNECTION_CLOSED`), so no memory read or write path is available. Beat stopped,
no retry. ..."

[PASS] AC19: beat's output names the unreachable store:
       ['unreachable', 'connection', 'failed to connect']
```

```
$ python check_heartbeat_ac8_scripted_agent.py --build
scratch project built

$ python check_heartbeat_ac8_scripted_agent.py --run
cost=$0.6023
result: 'Beat done - staging-migration decision captured (`649fdb0e`, semantic).'

$ python check_heartbeat_ac8_scripted_agent.py --verify
active memories: 1
  id=649fdb0e-... type=semantic content='2026-09-24 - ... decided to migrate the
  staging environment off AWS onto a self-hosted VPS. Reason: AWS free-tier limits
  were repeatedly throttling the CI pipeline. This supersedes the earlier plan ...'

[PASS] AC8: exactly one store, not two: count=1
[PASS] AC8: content carries the reason (not just that something happened)
```

Total spend this cycle: **$0.886**.

`--verify` needs a scratch synaptra on `:8063` against the scratch store; started and
stopped by hand, as that check has always required.

### Regression line — all pass

| Script | Result |
|--------|--------|
| `check_shapes.py` | 5/5 |
| `check_hooks.py` | 27/27 |
| `check_session_start.py` | 2/2 |
| `check_verify_memory.py` | 12/12 |
| `check_heartbeat.py` | 3/3 |
| `check_dream.py` | 5/5 |
| `check_activation.py` | 5/5 (undefined-name sweep now covers 59 files, including the new fixture) |

## One file touched beyond the done condition

`.gitattributes`, +6 lines: `fixture_*.py export-ignore`.

`.claude/shared/` **ships** — it is where `activation.py` lives, which `session-start`
imports at runtime. Without this line the fixture would land in every user's install as
test scaffolding they never run. Written as a pattern, not a name, matching the file's
own stated reasoning for `check_*.py`. Verified:

```
$ git check-attr export-ignore ...
.claude/shared/fixture_scratch_brain.py: export-ignore: set
.claude/shared/activation.py:            export-ignore: unspecified
```

Reported to velasari rather than done silently.

## Assumptions that changed

- **27, not ~14.** `assumption.md` records the corrected count.
- The 22-shapes figure is formatting noise. Recorded so a later cycle does not
  re-derive it and conclude the extraction was unsafe.

## Not done, deliberately

- The remaining 25 builders. Two was the brief; two exposed the extraction.
- `/dream` untouched. C4's backup-check extraction is separate work.
- Phase 2 not started.

## Next

Stop. velasari holds the thread; Kaushik verifies manually.

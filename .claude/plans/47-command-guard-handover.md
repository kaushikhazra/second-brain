# #47 command guard: handover from Velasari, 15 Oct 2026

**Goal:** issue #47's acceptance criteria, all 8. Read the issue first:
`gh issue view 47 --repo kaushikhazra/second-brain`.

**Why now:** Kaushik, 15 Oct: *"we build #47. Because it came out in a call.
Means user needs it."* The shipped brain has no command guard at all: `src/.claude/hooks/`
holds only `memory_guard.py`; Bash and PowerShell run unchecked.

**Split:** the HOW is yours. The WHAT is this file. WHETHER (release, anything
outward-facing) is Kaushik's, through Velasari.

**Mode:** run it as a loop (`ai-engineering:auto-iterate`), cycle every 24 minutes,
his instruction. Report to `velasari` over crosschat at each milestone.

## What exists (branch `feature/47-command-guard`, from main, pushed)

| piece | file | state |
|---|---|---|
| runtime + unwrap | `src/.claude/hooks/command_guard.py` | stdlib only; unwraps bash/sh -c, pwsh -Command/-EncodedCommand, python -c, eval/iex, base64, hex (3 deep); crc32-hashed char 2-5 + word 1-2 grams, 2^18; 4 logistic heads; bands deny_at 0.80 / allow_below 0.30 |
| unwrap tests | `guard/test_unwrap.py` | 14/14 pass (AC 2) |
| generator | `guard/generate.py` | synthetic, labelled by construction; 0.5 = the owner's "ask" class |
| trainer | `guard/train.py` | sklearn liblinear; writes `command_guard.bin` (4.2 MB) + `.json` next to the hook |

Not yet: the hook is NOT registered in `src/.claude/settings.json` (AC 1 needs a
PreToolUse matcher on `Bash|PowerShell`); no release notes; the data files under
`guard/data/` are not committed.

**Design deviation to note on the issue:** the issue says "run in numpy"; the
runtime is stdlib-only instead, matching memory_guard.py's rule (bare `python` on
PATH, fresh process per call). A sparse linear model needs no numpy. AC 6 is
better served.

## The labelling rule (Kaushik, 10 Oct)

- **stop (1):** remove, overwrite, update anything that loses information. `echo x > file` is 1: "the most dangerous command in a disguise of an innocence".
- **ask (0.5):** installs (pip/npm/winget), killing or stopping processes: fine if conscious, so ask.
- **go (0):** read, fresh create, history-keeping changes (git commit, merge).
- Plus the issue's two: touches production; sends data off the machine.

## The finding to start from

On the generator's own held-out sets the model scores 100% / 0%: meaningless,
same templates. On Kaushik's REAL commands (10,950, `C:/Projects/.tmp/cmd-guard-dataset/commands.jsonl`):
**allow 80.7% · ask 6.9% · deny 12.5%, and nearly every deny is a false alarm.**
Causes seen in samples: `2>/dev/null`, `>/dev/null`, `2>&1`, `-o /dev/null`
read as overwrite; long `cd` paths into Temp; python heredocs that only read;
for-loops; tool CLIs (gh, crosschat, uv). Decisions saved in `v1_decisions.json` there.

## Backlog (standing authorization to drive it)

1. Teach the harmless real-world shapes in the generator: stderr/stdout redirects to /dev/null or $null, `| head`, `| Out-Null`, read-only heredocs, loops, long paths, real CLIs. Keep the true positives (a redirect onto a real file is still overwrite).
2. Build a REAL-WORLD scorecard: sample ~300 of Kaushik's commands, label them carefully on the four questions + ask, keep them as TEST ONLY.
3. Retrain; iterate 1-2 until on the scorecard: risky blocked high, safe wrongly blocked low. Tune deny_at / allow_below on the scorecard, not the synthetic set.
4. Register the hook (AC 1), with a check like `checks/` style proving Bash and PowerShell both reach it.
5. Release-notes numbers (AC 8): synthetic held-out plain + wrapped, and the real-world scorecard.

## Hard constraints

- **AC 7: no owner command history in training. Ever.** His commands are test data only, and are not committed to the repo.
- Public data (if used): tldr-pages is CC-BY-4.0; attribution required.
- Don't release, tag or merge to main: that is Kaushik's call.
- Commit and push together, per his rule.

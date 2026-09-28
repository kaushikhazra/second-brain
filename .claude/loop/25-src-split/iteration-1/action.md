# Action — cycle 7

**The loop is reopened. Kaushik's call, 2026-09-28.**

⛔ **No criterion has changed.** The 30 are what they were. What changed is that cycle 6
marked 21–24 met on an argument, and those four criteria ask for a demonstration.

```
  cycle 6 proved    every SHIPPED file is byte-identical to v1.0.1
  21-24 ask         a brain BOOTS from them
```

⇒ **Nothing in six cycles exercised the install path.** `init-brain` generates `.mcp.json`,
provisions `.claude/.venv`, writes `uv` shims — **none of which ship**, so none of which
byte-identity can speak to. A restructure is exactly what breaks a provisioner's sense of
where it is. Criterion 21 exists to catch that and was answered by comparing files the
provisioner never touches.

⚠ Cycle 6's premise — *"if v1.0.1 boots, this boots"* — was also never tested. v1.0.1's
boot was assumed.

## ⭐ This cycle may LOWER the count

**Mark 21–24 as `UNPROVEN` at the start and earn them back.** A cycle that can only
increase the number cannot correct itself, and cycle 6's 30/30 is the error that shape
produces.

**Start from 26/30.**

## The test

1. Build if needed, and unpack into a **fresh empty** directory under
   `C:/Projects/.tmp/second-brain-loop-25/boot/`. ⛔ Not the `install/` directory cycle 6
   used — a directory it already inspected is not a clean install.
2. ⛔ **Point Synaptra at a scratch data directory under the same scratch root.**
   `.claude/synaptra-data` at the dev root is Kaushik's own memory. Nothing in this cycle
   reads or writes it, and no fixture copies it.
3. **Run `init-brain` in that directory, for real.** A headless `claude -p` session with
   the install as its working directory is the honest form. Let it provision.
4. Then, in the same install:
   - **21** — did initialisation complete and produce a usable brain? Say what "usable"
     was judged on.
   - **22** — run `/session-start`. Did it reach the end?
   - **23** — run `session-end`'s `verify_memory.py`. Did it run, as step 4, unchanged?
   - **24** — did the hooks fire? `memory_guard.py` refusing something it should refuse is
     the demonstration; the config being present is not.

## What counts as evidence

**Something that would have FAILED if the restructure had broken it.** Quote the output.

⛔ **A file existing is not a check.** ⛔ **A check that passes against the repo instead of
against the install proves nothing about the install.**

⚠ If a criterion genuinely cannot be demonstrated with what is available, **leave it
UNPROVEN and say precisely what was missing.** 26 honest is worth more than 30 asserted —
and `19849e7b` is why: the Alex handover has been blocked since August on nobody defining
*"tested enough"*. **These four criteria are that definition.** An inference here throws
away the artifact that would settle it.

## If a scripted-agent check needs fixing to take a target directory

That is legitimate work and in scope. Cycle 6 found they compute their root three parents
up and cannot be redirected. **Fixing one to accept a path is a smaller job than leaving
the criterion unproven** — but the fix must not change what the check asserts.

⚠ Scripted-agent checks shell out to `claude -p` and cost real money. Budget is not a
constraint; run what the four criteria need and no more.

## ⛔ Closing obligations

1. `logs/cycle-7.md` — criteria by listing, with 21–24 each marked PROVEN or UNPROVEN and
   the evidence quoted.
2. Commit and push, before the report.
3. Rewrite this file, or declare the goal met in it.
4. **Correct the issue #25 comment** if the number moved — post a follow-up comment, do
   not edit the old one away.
5. `crosschat send second-brain velasari "<cycle 7: ...>"`

⛔ Do not merge to `main`. ⛔ Do not delete the cron.

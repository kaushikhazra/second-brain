# Action

**Cycle 9. The last four: AC 4, AC 17, AC 18, AC 20.**

Read `logs/cycle-8.md` first — six criteria proven (AC 6, 7, 10, 11, 14, 15), a real
gap in `SKILL.md`'s Output section found and fixed via a headless run. 16/20. Four
remain, all previously flagged as genuinely harder to prove than a single-shot
scripted-agent run naturally supports.

## 1. AC 4 + AC 17 — same underlying difficulty, solve once

AC 4: "Each beat reads the window since the previous beat, or since session start
on the first."
AC 17: "Three consecutive beats that observed nothing is itself an observation,
unless the beat's last turn handed the owner something to do."

Both need a real notion of "the previous beat" that a fresh `claude -p` invocation
doesn't have on its own — `SKILL.md` says previous beats are "visible in context,"
which only holds within ONE continuous session across multiple turns, not across
separate `claude -p` processes.

**Try this**: a single `claude -p` invocation whose PROMPT itself simulates a
multi-beat history — e.g. "This is beat 3 in this session. Beat 1's window was: X,
you stored Y. Beat 2's window was: Z, quiet, nothing observed. Now run beat 3. The
window since beat 2: W." This tests whether the beat correctly scopes its
`capture`/`quiet-cycles` judgment to ONLY the window named for THIS beat (not
re-processing beat 1's already-captured content, and correctly counting the quiet
streak from the simulated history). It's a proxy for true multi-turn state, not the
real thing — say so plainly in the log rather than overclaiming what it proves.

If this proxy approach doesn't yield a clean, honest test, the fallback is: build a
genuinely multi-turn scratch session instead (multiple `claude -p` calls against
the SAME `--session-id`, if the CLI supports resuming a session — check `claude -p
--help` for a resume/continue flag before assuming one exists or doesn't). Try the
cheap proxy first; only reach for session-resume machinery if the proxy can't
support a real assertion.

## 2. AC 18 — provable in part

"When curiosity is active (see the curiosity story), that observation fires one
curiosity pass; when it is not active, nothing fires and the count resets."

`/curiosity` doesn't exist yet (issue #6). `goal.md § quiet-cycles` already states:
"If `/curiosity` is not present, or not active, do nothing — and reset the count."
**Provable now**: seed the "three quiet beats" condition (via the AC 4/17 proxy
technique above) and confirm the beat does NOT attempt to invoke a `/curiosity`
skill that doesn't exist, and its own output or state shows the count resetting
rather than erroring on a missing skill. **Not provable now**: the "curiosity is
active, fires one pass" branch — there is nothing to fire. State this split
plainly: AC 18's inactive-branch is MET, the active-branch is UNTESTABLE UNTIL
ISSUE #6, not a failure of this story.

## 3. AC 20 — likely not scripted-agent-testable; decide how to close it out

"A beat that runs past its cron interval is not run twice; the next fire starts a
fresh beat."

`SKILL.md`'s `## Failure` section already states the reasoning: each cron fire is
its own fresh invocation, so "not run twice" is a property of the invocation model
rather than something tracked. This is an architectural/platform claim about how
Claude Code's cron mechanism itself behaves (does a slow-running fire block the
next scheduled one, or does the next one queue/skip/run concurrently?) — not
something a `.claude/skills/heartbeat/` scripted-agent run can observe, since it
only controls ONE `claude -p` invocation at a time, not the actual cron scheduler.

Decide: is `SKILL.md`'s stated reasoning sufficient to count as "demonstrably met"
under this story's own bar, or does it stay at the "never — the skill file says so"
tier permanently unless someone tests actual cron behavior directly (which would
mean using the real `CronCreate`/`CronList` tools against a live but harmless
scenario, not a scripted-agent run)? If a cheap, honest way to test real cron
overlap behavior exists, try it. If not, say so plainly and record AC 20 as
text-only, not demonstrably met, rather than forcing a pass.

Never the live store — scratch under `C:/Projects/.tmp/second-brain-loop-4/`, fresh
data dirs, junction-safety discipline copied exactly.

Re-run `check_shapes.py`, `check_hooks.py`, `check_session_start.py`,
`check_verify_memory.py`, and `check_heartbeat.py` before closing the cycle — all
five must still pass.

Commit on `feature/4-heartbeat`, push, write `logs/cycle-9.md`, write the next
`action.md` (or, if all 20 hold, follow loop.md's converged path: delete the cron,
comment on issue #4 with the numbers, and tell velasari), send the one-line report
to velasari, and exit.

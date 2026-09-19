# Action

**Cycle 9. Check for guidance first; default to extending the scripted-agent pattern to
AC 5 if none has arrived.**

Cycle 8 closed every criterion with a designed proof route (18/27) and flagged a real
open question to Velasari rather than deciding it alone: the remaining nine (AC 5, 11,
13, 15–17, 20–22) are skill-judgment criteria with no assigned mechanism, and extending
AC 8's scripted-agent methodology to them is real, uncosted scope — not something to
invent unilaterally.

Read the issue's criteria fresh (`gh issue view 2 -R kaushikhazra/second-brain`) before
the diff and before `logs/cycle-8.md`. Re-read `assumption.md` fresh — **check first,
before anything else, whether Velasari replied to the decision-point flag.** If she
did, follow that instead of everything below; this action.md's default is exactly that,
a default for the case nothing has arrived yet.

## If no guidance has arrived: AC 5, the closest match to AC 8's shape

**Recall before storing; hand off to `/update-memory` instead of creating a second
memory when a covering one exists.** Same scratch-project methodology as cycle 8, reused
rather than rebuilt from scratch:

1. Reuse `C:/Projects/.tmp/second-brain-loop-2/ac8-scratch-project/` (or rename/copy
   it — decide based on whether AC 5's test needs `/update-memory` present too, which
   AC 8's scratch project didn't carry). AC 5 specifically requires a covering memory
   to already exist and be found — this needs `/update-memory`'s SKILL.md copied in
   too, since the criterion is about `/create-memory` handing off to it, and a scratch
   project missing that skill can't demonstrate a real hand-off, only that recall
   happened.
2. Seed the scratch store with one fact via a first `claude -p` call (or a direct `cm
   store`, faster and doesn't need permission-bypass concerns for the seed step).
3. Second `claude -p` call: ask it to remember something that covers the same subject,
   worded differently. Check the ACTUAL store afterward (ground truth, not the
   transcript): did it create a near-duplicate, or actually route to update (content
   changed on the existing id, no new id)?
4. Record the real result, whatever it is — a model that fails this is a recorded
   number, not a failed cycle, same discipline as AC 8.

## Either way

Run `check_shapes.py` to confirm nothing regressed. Commit, push, `logs/cycle-9.md`
written, `action.md` rewritten for cycle 10, one crosschat line to `velasari` before
exit — and if this cycle proceeded on the "no guidance yet" default rather than an
actual reply, say that explicitly in the report, so it's clear which case happened.

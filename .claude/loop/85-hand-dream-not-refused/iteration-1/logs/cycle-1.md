# Cycle 1 — #85

**Reproduced on 1.6.1.** The check run on main's skill text: AC 1, 2, 4, 5 fail. `/dream` says "has the owner
sent a message in the last 10 minutes? If so, refuse" with no exception, and `invocation: user-only` means
every `/dream` is typed by the owner, straight after a message.

**Fix.** `/dream`: the check now guards an automatic run only; a bare `/dream` skips it and goes to the
checkpoint; `requested by <requester>` still refuses within 10 minutes. `/dream-cycle`: the same for hard
stop 1 (the hand form was refused by the same rule); `"requested by heartbeat"` still refuses.

**Criteria held: 6 of 6** (`checks/dream/check_hand_run.py`); 6 removals each fail their named AC.
Regression: check_dream 5/5, check_dream_cycle 23/23, check_dream_cycle_cli 15/15.

**Beyond the brief.** `/dream-cycle` by hand had the identical refusal; fixed in the same issue.

**Accepted, not fixed.** Nothing invokes `/dream` automatically today, so its refusal branch has no
caller; it is kept for one that does. Not exercised by a live session: the proof is the text the model reads.

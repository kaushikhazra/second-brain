---
name: guard
description: Switch the command guard off or back on, or check its state. The guard is the PreToolUse hook that judges every shell command; off means it checks, blocks and asks about nothing. A new brain starts with it off. Use when the owner says "/guard on", "/guard off", "/guard status", or asks to turn the guard on or off.
---

# Guard

The command guard (`.claude/hooks/command_guard.py`) judges every Bash and
PowerShell command before it runs. This skill is the owner's switch for it. Off
means the **whole** guard is off — the trained model and the plain checks
(decoding, `-c` wrappers) alike: no command is blocked, asked about or
acknowledged.

The setting is the `guard` entry of the activation record
(`.claude/activations.json`, git-ignored), the same record `/curiosity` and
`/news` use. It persists across sessions and `/update` leaves it alone. A new
brain has no entry, which means off; an updated brain keeps what it had.

All three forms run one script — never edit the record by hand:

```bash
python .claude/skills/guard/scripts/guard.py on
python .claude/skills/guard/scripts/guard.py off
python .claude/skills/guard/scripts/guard.py status
```

### `/guard on`

Run `guard.py on`. Confirm: "The command guard is on."

### `/guard off`

Run `guard.py off`. Confirm: "The command guard is off." From the next command
on, nothing the guard does stands between the owner and the agent.

### `/guard status`

Run `guard.py status`. It prints `active` or `inactive` and the `VERSION` it
was last set at (or "never set").

### Not asked at session start

Unlike `/curiosity` and `/news`, the guard is not asked about in
`/session-start`'s activation step. While it is off, `/session-start` prints
the one line `guard.py line` returns, and nothing when it is on.

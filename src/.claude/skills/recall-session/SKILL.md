---
name: recall-session
description: Recall a past Claude Code session of this brain by regex. Returns session id, date, project, and an excerpt with configurable context turns, newest first. Use when the owner references an earlier conversation, decision, or work not in cognitive memory. Follow up with --session <id> --slice to expand a specific range.
---

# Recall Session

Regex search across this brain's own Claude Code session JSONL transcripts —
never another project's transcripts, and never synaptra. Call `memory_recall`
first; only reach here for something not already in cognitive memory.

## Invocation

Run via Bash, resolved from this skill's own directory — never a frozen path:

```bash
python "<this skill's directory>/tools/search.py" "<regex>"
```

Concretely, from the brain root: `python .claude/skills/recall-session/tools/search.py "<regex>"`.
The script resolves the brain root and the transcript directory itself, at
runtime, every call — nothing here is hardcoded to a machine or a path.

## Arguments

| Arg | Default | Purpose |
|-----|---------|---------|
| `<regex>` (positional) | — | Python regex, case-insensitive |
| `--before N` | 2 | Turns of context before each match |
| `--after N` | 2 | Turns of context after each match |
| `--limit N` | 20 | Max matches returned |
| `--max-lines N` | 40 | Truncate each excerpt body to N lines |
| `--role user\|assistant\|any` | any | Filter which role to search within |
| `--since YYYY-MM-DD` | none | Only sessions from this date onward |
| `--verbose` | off | Log every transcript file opened, to stderr |
| `--session <id>` | — | Expand mode: dump a slice of one session |
| `--slice START:END` | — | With `--session`, line range (1-indexed, inclusive) |

## Output

Default mode — one block per hit, newest session first:

```
[1] session=<sid>  project=<proj>  date=<iso>  line=<n>  role=<user|assistant>
    <excerpt, capped at --max-lines>
---
```

Expand mode (`--session ... --slice ...`) — raw turns in that range from that
one session.

## Scope and boundaries

- Searches only this brain's own transcript directory under
  `~/.claude/projects/` — resolved by walking up from the script's own
  location to the nearest directory holding both `.claude/` and `CLAUDE.md`,
  then encoding that root the way Claude Code names its transcript
  directories. Another project's transcripts are never opened.
- Reads transcripts only. Writes nothing, anywhere, ever.
- Imports only the Python standard library — it needs no synaptra connection
  and runs the same whether or not synaptra is reachable.

## Failure reporting, in the owner's terms

- **No match** — states that plainly and names the directory that was
  searched.
- **Invalid regex** — reports the error and searches nothing; the pattern is
  validated before any transcript file is opened.
- **Transcript directory not found** — names the exact directory it looked
  for and stops.
- **A session id that doesn't exist** (expand mode) — says so and lists the
  sessions that do exist in this project, newest first.
- **A transcript file that fails to parse** — names the file and the line,
  skips only that line, and keeps searching the rest of that file and every
  other session.

## Do not

- Dump whole sessions into cognitive memory. If something here is worth
  keeping cross-conversation, promote only the decision or turning point via
  `/create-memory` — this skill itself stores nothing.
- Use this for anything already in cognitive memory — call `memory_recall`
  first.

---
name: manage
description: Take a project in from a git URL and learn its instructions, list the projects this brain manages, find where one lives, or say what the brain knows about one. Use when the owner hands over a repository URL ("take this project in", "manage this repo", "clone <url>"), asks which projects the brain looks after, asks "what do you know about <project>?", asks about or overrides a project's code host or issue tracker, asks which trackers the brain works with, or before any piece of work inside a managed project.
---

# Manage

One brain can look after more than one project. Each one is a git clone under
`projects/<repo-name>/` in the brain's root. That folder is the whole registry —
nothing records a path anywhere, so renaming or moving the brain leaves every
project found.

`projects/` is never committed to the brain's own repo; `.gitignore` excludes it.

## Invocation

Run via Bash from the brain root — the script finds the root itself, at runtime:

```bash
python .claude/skills/manage/scripts/projects.py clone "<git-url>"
python .claude/skills/manage/scripts/projects.py list
python .claude/skills/manage/scripts/projects.py locate "<name-or-url>"
python .claude/skills/manage/scripts/projects.py learn "<name>"
python .claude/skills/manage/scripts/projects.py stale "<name>"
python .claude/skills/manage/scripts/projects.py refresh "<name>"
python .claude/skills/manage/scripts/projects.py trackers
python .claude/skills/manage/scripts/projects.py tracker "<name>" [--set field=value] [--clear]
```

Always clone through the script. Never `git clone` by hand, and never anywhere
but `projects/` — the script is what guarantees no re-clone and no partial folder.

## Telling the owner

The script prints `KEY: value` lines, the first `STATUS:`. Put each in the
owner's terms, with the values shown as they are:

| STATUS | Say |
|--------|-----|
| `CLONED` | Taken in. Show the **path** and the **default branch**. |
| `ALREADY_MANAGED` | Already here — not cloned again. Show the path. |
| `NAME_TAKEN` | A different project already sits at that path. Show it and its origin; clone nothing. |
| `UNREACHABLE` | Could not reach the host — a network or address problem. Nothing was created. |
| `NO_ACCESS` | Reached the host, but this machine has no access to that repo (or it does not exist there). Nothing was created. |
| `NOT_A_GIT_REPO` | The URL does not point at a git repository. Nothing was created. |
| `CLONE_FAILED` | The clone failed for another reason — quote `DETAIL`. Nothing was created. |
| `LISTED` | One line per project: name, path, origin. With `COUNT: 0`, say the brain manages no projects yet. |
| `FOUND` / `NOT_MANAGED` | Where it is, or that the brain does not manage it. |
| `LEARN_MATERIAL` | See *Learning a project* below. |

Each failure is its own message. Do not merge them into a generic "couldn't clone".
Lead with the cause in plain words — the `STATUS` code is for you, never shown
to the owner.

## Learning a project

Taking a project in is not done until it is learned. Straight after `CLONED`,
run `learn <name>` in the same turn.

`learn` writes the record `.claude/projects/<name>.md` — frontmatter
fingerprint and the hooks list are already filled in by the script — and prints
the material: the project's `CLAUDE.md`, README, every file under its `.claude/`
(skills and rules in full), its hooks and its top-level folders. Read all of it,
then replace each `_(to fill …)_` line in the record with what you learned, in
a few lines each:

| Section | What goes there |
|---------|-----------------|
| Purpose | What the project is and is for. |
| Development method | How work is done there (spec-driven, loops, TDD, …), from its `CLAUDE.md`. |
| Conventions | Language and version, dependencies, naming, style rules. |
| Code and tests | Where code lives, where tests live, the command that runs them. |
| Project skills and rules (.claude/) | Each skill or rule file, one line on what it does. |

Never touch the frontmatter or the hooks list — the script owns them.

`HAS_CLAUDE_MD: no` → say so to the owner in plain words, and learn from the
README and the folder structure instead; the record already says so at the top.

Then tell the owner, after the path and branch: one line on what the project
is, its development method, and its hooks **listed by name, with "not adopted"**
— a project's hooks never become the brain's own.

### What the brain knows about a project

"What do you know about X?" is answered **from the record** — `locate` X, read
`.claude/projects/<name>.md`, and give its purpose, development method,
conventions, and where code and tests live, plus anything else the record holds.
No record → run `learn` first.

### Staying current

Before any piece of work inside a managed project, run `stale <name>`:

| STATUS | Do |
|--------|----|
| `CURRENT` | Work. |
| `STALE` | The project's `CLAUDE.md` changed upstream. `refresh <name>`, then `learn <name>` and fill the record again, **before** the work. Tell the owner it was relearned and what changed. |
| `NO_RECORD` | `learn <name>` first. |
| `REFRESH_FAILED` | Local work blocks a fast-forward. Tell the owner; do not work on stale instructions. |

### Whose rules win

While working inside a project, **the project's rules win over the brain's own**
— its `CLAUDE.md`, its `.claude/` rules, its method. The brain's identity and
memory rules still hold; its development method does not. Wherever the two
conflict on something you act on, tell the owner which one applied, in one line:
*"Followed sb-sandbox-alpha's rule (spec first) over the brain's own (loops)."*

## Code host and issue tracker

`learn` ends with a *code host and issue tracker* block — the same lines
`tracker <name>` prints. Nothing there calls a tracker's API: the code host
comes from the remote URL, the tracker from the project's own files (a Jira
link in its `CLAUDE.md` or README) or else the code host's own issues.

On taking a project in, tell the owner the **code host**, the **issue
tracker**, and **how you know** (`HOW_DETECTED`, in plain words: "from the
remote URL (gitlab.com) and its `.gitlab-ci.yml`").

| Line | Do |
|------|----|
| `SUPPORTED: no` | Say plainly: the project is still managed, but monitoring and issue work are not available for that tracker. |
| `CREDENTIALS: missing` + `TELL_OWNER: yes …` | Tell the owner what is needed (`NEEDED`), once. |
| `CREDENTIALS: missing` + `TELL_OWNER: no …` | Already told — do not repeat it. |

**Which trackers work** — "which trackers can you work with?" → `trackers`,
and answer with exactly what it lists; the script is the one source of that list.

**Override** — the owner can set either one explicitly ("alpha's issues are in
GitLab", "treat beta's code host as gitlab"):

```bash
python .claude/skills/manage/scripts/projects.py tracker "<name>" --set tracker=gitlab
python .claude/skills/manage/scripts/projects.py tracker "<name>" --set code_host=gitlab
python .claude/skills/manage/scripts/projects.py tracker "<name>" --clear
```

What was detected and what was overridden live in `.claude/projects/<name>.json`
and survive a restart and a relearn. For any question about a project's
tracker, run `tracker <name>` — never answer from memory of an earlier session.

## Do not

- Clone a URL the owner did not give. On a failure, never retry with a
  different spelling of it (HTTPS for SSH, another host, a fork) — report the
  failure, say what would work, and let the owner hand over the URL they want.
- Copy a project's files into the brain, or clone beside the brain.
- Write a project's path into memory, a config file or `CLAUDE.md` — ask the
  script with `locate` each time instead.

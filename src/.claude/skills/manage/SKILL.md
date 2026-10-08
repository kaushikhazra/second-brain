---
name: manage
description: Take a project in from a git URL, list the projects this brain manages, or find where one lives. Use when the owner hands over a repository URL ("take this project in", "manage this repo", "clone <url>"), or asks which projects the brain looks after and where they are.
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

Each failure is its own message. Do not merge them into a generic "couldn't clone".
Lead with the cause in plain words — the `STATUS` code is for you, never shown
to the owner.

## Do not

- Clone a URL the owner did not give. On a failure, never retry with a
  different spelling of it (HTTPS for SSH, another host, a fork) — report the
  failure, say what would work, and let the owner hand over the URL they want.
- Copy a project's files into the brain, or clone beside the brain.
- Write a project's path into memory, a config file or `CLAUDE.md` — ask the
  script with `locate` each time instead.

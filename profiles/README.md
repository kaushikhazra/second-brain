# Profiles

A **profile** is a ready-made identity for a second brain. Second brain itself is generic: the same skills, memory and guards in every install. What makes one install a particular agent, with one job and one owner, is three small files:

| File | What it sets |
|---|---|
| `persona.md` | who the agent is, what it owns, how it reports |
| `user.md` | who it works for, what it may do alone, what waits for the owner |
| a launcher (`.bat`) | how it starts: which MCP servers load, which model, whether it runs unattended |

`/init-brain` normally builds these by interviewing you. A profile gives you a tested set instead, with `{{placeholders}}` for the parts that are yours.

```
  second brain (generic)  +  profile (who it is)  =  one agent
```

## Using a profile

1. Install second brain into a new folder named after the agent.
2. Copy the profile's files into that folder.
3. Replace every `{{...}}` placeholder. The profile's own README lists them.
4. Start it with the profile's launcher.

## Available profiles

| Profile | For |
|---|---|
| [`maintainer`](maintainer/) | an agent that owns one or more code repos: their issues, fixes and releases, under one human owner who merges and releases |

## Adding a profile

A profile is a folder here with its `persona.md`, `user.md`, launcher and a README listing its placeholders. Keep it generic: no names, paths or projects from any one install. Anything specific to one machine goes in the placeholders.

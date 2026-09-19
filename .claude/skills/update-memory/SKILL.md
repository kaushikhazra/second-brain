---
name: update-memory
description: The path for changing a memory that already exists. Default answer is don't — add a node and an edge instead. Use when a memory is WRONG, when a fact goes stale, or when a learning gains evidence. Never call memory_update directly.
---

# Update Memory

**The default answer is: don't.**

Adding a linked node is almost always the better move. Rewriting a memory in place is
never free — it's a full resend, a version snapshot, and a stability reinforcement
every time, and a hand-typed tag list silently drops whatever wasn't retyped. **The fix
for a stale line in a big memory is a small new node and an edge, not a bigger
rewrite.**

⇒ **Rewrite when a memory is WRONG. Add and link when it is merely INCOMPLETE.**

---

## Shapes

**Read `.claude/shared/memory/memory-shapes.md`** — each shape has an `update` section
and they differ sharply. A `fact` is corrected in place. A `learning` is *refined*,
never rewritten. A `persona` or `person-model` is **superseded, with the prior kept**.

⛔ **Do not restate it here.**

---

## Before changing anything

1. ⛔ **Read it first.** Via `/read-memory`. An update written from recollection of
   what a memory says is how a correction lands in the wrong place.
2. **Ask which of these it actually is:**

| situation | do |
|---|---|
| the memory is **wrong, and was once true** | rewrite the wrong part, in place |
| the memory was **never true at any point** | ⛔ **not this skill — `/delete-memory`.** See the tiebreak in `memory-shapes.md` § `fact` |
| the memory is **superseded** by a newer one | ⛔ not this skill — `/delete-memory` archives it. **Superseded is not wrong** |
| the memory is **incomplete** | ⭐ new node + edge. Do not touch the original |
| a rule gained **evidence** | new instance node, `supports` edge |
| a rule gained an **exception** | new boundary node, `part_of` edge |
| who someone *is* has **changed** | new node, `supersedes` edge, **keep the old one** |
| it is merely **untidy** | ⛔ **do nothing.** See the decay warning below (AC 16) |

---

## ⛔ When a memory is wrong, write the correction into the record that is wrong

Not only into a new memory. **A corrected fact with an uncorrected copy still sitting
elsewhere is worse than either alone** — the stale copy still ranks, still surfaces,
and reads as current. **The correction has to land where the error lives** (AC 17).

---

## 🔴 The mechanics that cause silent damage

- **`memory_update` REPLACES `tags` wholesale — it does not patch.** Passing `tags`
  drops every tag not in the list you pass. ⛔ **Fetch the current tags first (`/read-memory`
  or `memory_get`) and pass the full intended set, with nothing dropped that wasn't
  deliberately named** (AC 18).
- **A type change goes through `cm update <id> --type <type>`, not `memory_update`'s
  own `type` argument** (AC 19). This is the one place a type correction happens, so it
  stays visible in the `cm` history rather than blending into ordinary content edits.
- ⚠ **`memory_update` reinforces stability on every call**, so every edit writes into
  the decay engine. **Tidying is not free — it makes a memory harder to forget.** This
  is the single best reason to refuse an update made only for cosmetics, and to say why
  when refusing it (AC 16).
- **Large content blows the CLI arg limit** — write from a file:
  `cm update <FULL-uuid> --content "$(cat file)"`.

---

## ⛔ Verify

**Read it back and confirm the change is actually there.** Not the return value — the
memory itself (AC 20). A call that reports success is not a call that landed — the
same discipline `/create-memory` applies to a store applies here to an update.

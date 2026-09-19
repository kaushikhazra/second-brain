---
name: delete-memory
description: The path for removing a memory. Archive is almost always the right operation; delete is permanent and cascades. Use when a memory was never true, duplicates a better record, or is scaffolding that outlived its job. Never call memory_delete directly.
---

# Delete Memory

**Two operations, and the difference is not cosmetic.**

| | `memory_archive` | `memory_delete` |
|---|---|---|
| effect | leaves the active set | **gone** |
| reversible | yes — `memory_restore` | **no** |
| edges | kept | ⛔ **cascades — relationships, versions, embeddings** |
| use for | superseded, stale, outgrown | never-true, duplicates, scaffolding |

⇒ **Archive by default.** A superseded memory is history, and history has a reader.

⚠ **But archiving is not automatically the safe choice** — keeping something with no
reader costs a second source of truth. **Ask who reads the archived copy.** If the
answer is *the restore path, if we were wrong*, archive. If the answer is nobody, and
it was never true, delete.

---

## Shapes

**Read `.claude/shared/memory/memory-shapes.md`** — the `delete` sections differ, and
one of them changes the operation entirely.

⛔ **Do not restate it here.**

---

## 🔴 On a `learning`, this is a GRAPH operation

**Removing a procedure and leaving its instance behind produces a story with no
point** — which still ranks, still surfaces, and is worse than nothing. Its boundary
becomes an exception to a rule that no longer exists.

🔴 **The reverse is the LIKELIER mistake, not a safer one.** Since the shapes file's
instance-ranks inversion, the instance is the node recall actually lands on — it is
never "safe either way" to remove and leave the bare procedure standing. A tidy-up
instinct reads the instance as the disposable long story and the procedure as the
important bare rule; that instinct is backwards. Losing the instance is the more
damaging loss, not the lesser one.

⇒ ⛔ **Take the constellation or take none of it — and that is the only choice
offered, not one option among several.** `memory_delete` cascades *edges*, not nodes —
so it **creates** these orphans rather than preventing them (AC 22). ⛔ **Do not
present a partial removal as something the owner can pick.** "Delete just the
procedure, leave the rest" or "delete just the instance, leave the rest" are not
menu options to surface — they are the outcome this rule refuses. State the refusal
and name the constellation rule; offer only "remove the whole constellation" or
"remove nothing."

**Before removing any node of a constellation:** run `memory_related` on it, collect
the whole constellation, act on all of them together — or not at all.

---

## ⛔ Never delete a `persona` or a `person-model`

Retiring part of a self is a **supersede**, not an amputation. A relationship ending is
a **state change**, not a deletion. In both shapes the prior version is the only thing
that makes the current one legible — a record of past incarnations exists precisely
because earlier selves were not removed.

⇒ If the impulse is to delete one of these, the operation wanted is `/update-memory`.

---

## What genuinely warrants deletion

- **It was never true.** Not superseded — wrong from the start.
- **It duplicates a better record.** Delete the weaker one; ⚠ **move its edges first, or
  the graph loses them.**
- ⭐ **It is a success log.** A memory recording only that a rule *fired correctly*
  counts wins, and counting wins rebuilds the same defect `/create-memory` already
  refuses at write time, with the sign flipped.
- **It is scaffolding that outlived its job** — with a named reason, not a tidying
  impulse.

State which of these applies when reporting the deletion (AC 21).

---

## Before any destructive operation

1. ⛔ **Read it.** Via `/read-memory`. **Never delete something that hasn't been looked
   at**, whatever a listing says it is.
2. **Check what points at it** — `memory_related`. An edge into it means something else
   expects it to exist.
3. **Back up if the operation is bulk.** `cm backup create --name <reason>-<date>`, and
   ⚠ **verify the artifact, don't trust the verifier's opinion alone** — parse the
   NDJSON output, count the records, confirm the manifest agrees.
4. **`memory_delete` requires `confirm=true`.** Verified against this install's server:
   the call refuses outright without it (`"confirm must be true for permanent
   deletion"`). Treat that argument as the checkpoint it is, not a parameter to fill in
   by habit.

---

## ⛔ Bulk removal is the owner's call

Anything touching more than a handful of memories at once is a decision about the shape
of the store, not a maintenance task. **Bring the owner the count, the criterion and a
sample. Do not run it and report afterwards.**

⚠ **Say plainly which operation is proposed.** Archive and delete sound similar and are
not — a mixed batch needs the split stated (how many archived, how many deleted), and
any deletion in it needs the owner's explicit word, not an inference from a general
"clean this up" request.

---
name: read-memory
description: The path for getting something back out of Synaptra. Chooses the right retrieval tool, handles a failed recall, and follows the shape of what it lands on. Use before answering anything that touches the past — not after failing to remember it.
---

# Read Memory

**Why this exists.** Encoding without a matching decode is a write-only store. The
shapes decide how a memory is *written*; this decides how it is *reached* and what to
pull once it is found.

**And the one fact everything here rests on:** ⛔ **Synaptra does not surface itself.**
Nothing lights up because it became relevant. **A missing memory feels exactly like the
thing not existing** — so retrieval is a discipline, never a reflex.

---

## Shapes

**Read `.claude/shared/memory/memory-shapes.md`** — each shape has a `read` section,
and they differ. `fact` is one node and done. `learning` is a constellation with an
order. `persona` loads at boot. `person-model` loads when that person is in play.

⛔ **Do not restate it here.**

---

## ⛔ Recall BEFORE answering, not after failing

**This is blocking.** Trigger it when the owner says *remember*, *recall*, *secret*,
asks what was done or built or discussed, or refers to any past conversation at all.

**Saying "I don't know" without having checked is the failure this skill exists to
prevent.**

Also recall at the start of any non-trivial task, for prior context that would change
the approach.

---

## The tool ladder — pick by what you know, not by habit

| you know | use | notes |
|---|---|---|
| the id | `memory_get` | ⚠ large memories blow the token cap; dump to a file instead |
| an exact tag | `memory_list(tags=[…], state="active")` | deterministic — the boot lists come this way |
| a distinctive string | `memory_list(search="…")` | full-text; catches what ranked recall sometimes misses |
| roughly the topic | `memory_recall(query)` | ranked fusion: semantic + keyword + graph + temporal |
| a starting node | `memory_related(id, rel_types=[…])` | ⭐ **filter by `rel_types`** — an unfiltered walk on a well-connected graph reaches almost everything |
| identity, deliberately | `memory_self(query)` | a *search*, not the boot path — boot uses the `self-map` list |

**The obvious ones are not all of them** — `list`, `who`, `config`, `health`, `stats`,
`archive`, `restore`, `consolidate` exist and are easy not to think of.

**Say which tool was used when reporting the answer** — this is AC 13, and it is the
part that is actually informative when a search comes up empty.

---

## When recall comes back empty or wrong

**In order, and do not skip to the last one.**

1. ⛔ **Do NOT just re-run `memory_recall` with a reworded query.** A semantic miss is
   often a retrieval-strategy problem, not a phrasing problem — rewording alone can
   repeat the same miss.
2. **Try `memory_list(search="…")` with a distinctive phrase instead.** Full-text catches
   an exact-tagged or exactly-worded memory that ranked recall's fusion scored low.
3. **If the owner is plainly referring to something real and synaptra genuinely has
   nothing, say so plainly.** Second brain has no session-transcript search of its own
   to fall back to — do not fabricate an answer to fill the gap, and do not claim the
   thing doesn't exist. Report the miss; store it once the owner supplies the answer, if
   it's worth keeping (per `/create-memory`'s bar).

⭐ **A null result is a fact about the query, not about the world.** Report it as *"I
did not find it"*, never as *"it does not exist"* — and name which tool was used (AC 14).

---

## Once you land on something

### Follow the shape

Per the shared file. The one that matters most:

⭐ **On a `learning`, pull the BOUNDARY before applying the rule.** Not after it appears
to fail — that is too late. A rule read without its boundary is a different rule, and
applying the wrong side of one is a live, current failure, not a near miss (AC 15).

### ⛔ Open the cited source before restating a constraint

**A memory that cites another compresses it to the clause its own context needed**, and
can silently drop the boundary conditions. The trigger is not doubt — fluency reads the
same either way. **The trigger is structural: any time an arrangement changes, every
constraint it inherits gets re-read at source**, not repeated from memory of the memory.

⚠ **And opening it is not sufficient.** If the source is a boundary memory with two
sides, **identify which case applies before reading which rule applies** — reading the
rule first and assuming the case is a distinct failure that feels like diligence.

---

## When to stop

**Enough is when the next pull would not change what you do.** Retrieval spirals easily
on a graph this connected — one memory relates to several, each of those to several
more.

**On a `learning` you land on the INSTANCE, not the rule** — see the shapes file for
why. ⇒ **Usually the story is the answer and nothing else needs pulling**, because the
rule re-derives from it against the case actually in front of you. **Pull the bare
procedure only when the rule has to be stated flat to someone, or carried somewhere the
story does not reach.**

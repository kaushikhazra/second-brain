# Memory Shapes

**Read by:** `/create-memory` · `/read-memory` · `/update-memory` · `/delete-memory`.

**Why it is here and not in the skills.** Four skills need the same
classification. Four copies drift, and the copy that goes stale is invisible
until it produces a wrong write. One definition, four readers.

⛔ **Do not restate this file inside a skill.** A skill carries a `## Shapes`
section that points here and nothing more.

---

## Shape and store type are different axes. Choose them separately.

| | what it decides | typical values |
|---|---|---|
| **Store type** | **how fast it decays** | `working` · `episodic` · `semantic` · `procedural` · `identity` · `person` |
| **Shape** (this file) | **how it is written down** | `fact` · `learning` · `persona` · `person-model` |

A `learning` is *usually* procedural, but that is a tendency, not a rule. A
`fact` can be any type. **Type answers how long it lives. Shape answers how
it is written down.**

---

## The fork — choose the shape before writing anything

> **Is this about the self, about someone else, about the world, or about
> what to do?**

- **It constitutes the self — who the brain is, what it values, how it is
  built** → **`persona`**
- **It is the brain's model of the owner or another person — how they work,
  what they respond to** → **`person-model`**
- **It states how something IS** → **`fact`**
- **It states what to DO or avoid, and was earned rather than looked up** →
  **`learning`**

⚠ **The line between `person-model` and `fact` is model versus datasheet.** A
preference stated once, a date, a role, a documented decision — those are
`fact`, even though they are about a person. **`person-model` holds what the
brain has come to think of them.**

**Tie-breaker when both feel true:** ask what a future session would *use* it
for. **Quoted as evidence → fact. Changes a decision before acting →
learning.**

| a memory that… | shape | why |
|---|---|---|
| records a measured value, a structure, a configuration | `fact` | states how something is |
| records a decision that was taken, and its reasoning | `fact` | ⭐ it reports what was decided; it is not earned advice |
| captures an observation or a result | `fact` | evidence |
| describes a person, a preference, a constraint they hold | `fact` | states how something is |
| says *"before doing A, check B"* | `learning` | changes a decision before acting |
| says *"X only works when Y holds"* | `learning` | earned, and applied prospectively |
| names a failure mode and the rule that prevents it | `learning` | the rule is the payload |
| states a value, a role, an origin, a standing disposition of the self | `persona` | constitutes rather than describes |
| holds how the owner or another person works, what they respond to, what they will not tolerate | `person-model` | a model, revised over time |
| records a measured or documented value about a person | `fact` | ⚠ a datasheet, not a model |
| records the brain behaving badly once | `learning` | ⚠ an instance is not a disposition |

⚠ **The decision-record row is the one that catches people.** A design
decision *feels* like a learning because it was hard-won. It is not — it
records an outcome. Nothing in it tells a future session what to do
differently.

---

# Shape: `fact` — one node

**Stored WHOLE. Splitting a fact is damage** — its parts are not
independently meaningful, and a fragment reads as a claim it does not
support.

### create
One node. **Length is not a defect — a long fact is fine if it is one
fact.** If it contains two facts that could be recalled independently, it is
two memories.

### read
Read it. Nothing else to pull.

### update
**Facts go stale, so this is the shape that gets updated.** When one becomes
wrong, ⛔ **write the correction into the record that is wrong**, not only
into a new memory — a corrected fact with an uncorrected copy elsewhere is
worse than either alone.
⚠ **But prefer a new linked node when the fact is merely INCOMPLETE.**
Rewrite only when it is *wrong*.

⛔ **"Wrong" is ambiguous and decides between two different operations. The
tiebreak is whether it was EVER true:**

| | operation |
|---|---|
| **it was true once and has since become false** | **`update`** — correct it in place, here |
| **it was never true at any point** | **`delete`** — not this shape's update; see `delete` below |

**Superseded is not wrong.** A measurement replaced by a newer one was true
when taken — that is `archive`, not either of these.

### delete
**Archive rather than delete when it was true once** — a superseded fact is
history, and history has a reader. **Delete only when it was never true**, or
when it duplicates a better record.

⛔ **Same tiebreak as `update`, stated here so this section is safe to read
alone:** *was it ever true?* **Ever true → not a delete** — it is an
`update` if it became false, an `archive` if it was superseded. **Never true
at any point → delete.**

---

# Shape: `learning` — a constellation

**The story retrieves; the rule supports.**

A rule is a compressed conclusion, frozen against the one situation that
produced it. The instance is richer, survives re-reading, and can be
re-derived against a case the frozen rule would have mis-fit. **The rule can
be re-derived from the story. The story cannot be re-derived from the rule.**
⇒ **So the instance is what recall should land on.**

```
              recall lands here
                     │
                     ▼
      ┌──────────────────────────────┐
      │  INSTANCE                    │  what happened, in the words it happened in
      └───────┬──────────────────────┘
              │
   ┌──────────┼─────────────┐
supports   part_of      contradicts
   │          │             │
   ▼          ▼             ▼
PROCEDURE  BOUNDARY   COUNTER-CASE
```

The edges read from the instance outward: `instance —supports→ procedure`
— the story is evidence for the rule. **What matters is which node is
written to be found.**

🔴 **And "what ranks" is not a flag — the store ranks on content and tags.**
So this only works if the instance is the node that carries the detail, the
quotes and the tags, and the procedure is kept bare. **Writing a rich rule
and a thin story silently defeats it, whatever this file says.**

| node | holds | edge | pulled when |
|---|---|---|---|
| **instance** | what happened, verbatim where it was said, with the mechanism visible inside it | — | always; this is what ranks |
| **procedure** | the rule alone, bare | `instance —supports→` | the rule has to be stated flat, or carried to a new case |
| **boundary** | when it does NOT apply | `—part_of→ procedure` | ⭐ **BEFORE applying** |
| **counter-case** | where it broke or was overruled | `—contradicts→ procedure` | it appears to be failing |

**Why `part_of` and not `supports` for the boundary:** a boundary is not
evidence for the rule, it is **part of the rule's definition.** A rule read
without its boundary is a different rule.

### create
- **Write the INSTANCE first, and let it carry the detail** — what was said,
  who said it, what was actually observed. ⛔ Do not compress it into an
  illustration of a rule already decided on.
- **Then write the procedure, and keep it BARE.** ⛔ The moment it starts
  retelling the instance, the monolith is rebuilt with extra steps and the
  ranking flips back.
- **Procedure and boundary are separate nodes with real edges** — a prose
  reference with no edge behind it produces a memory that *looks* connected
  and is an orphan.
- 🔴 **Every node in a constellation takes the SAME store type.** A
  year-lived rule with a fortnight-lived instance means **the rule outlives
  its own evidence**, and the `supports` edge ends up pointing at something
  archived. Under the ranking above this bites harder, because now it is the
  node that RANKS which would decay first. **The constellation decays
  together, or it decays into a rule nobody can justify.**
- **Counter-case is optional and rare. Boundary is not optional when one
  exists** — a rule and its boundary fused in one node is read as the rule
  alone, and then misapplied.

### read
1. Land on the instance.
2. **Read the rule off the story if the story is enough.** The instance
   re-derives against the case in front of you, where the frozen rule only
   matches the case that produced it.
3. ⭐ **Pull the boundary before applying the rule.** Not after it seems to
   fail — that is too late, and it is the failure this shape exists to
   prevent.
4. Pull the procedure when the rule has to be stated flat to someone, or
   carried somewhere the story does not reach.

### update
**A learning is refined, not rewritten.** New evidence → a new instance node
with an edge. A newly-found exception → a new boundary node. ⛔ **Editing the
procedure text is for when the rule itself was wrong** — rare, and worth
saying out loud.

### delete
🔴 **Delete and archive are GRAPH operations here, not node operations.**
Removing either end and leaving the other produces something that still
ranks, still surfaces, and is worse than nothing — a story with no point, or
a rule with nothing behind it. ⚠ **The instance carries the detail, so it is
the one that looks expendable during a tidy-up, and it is the one recall is
aimed at — losing it is the likelier mistake.**
⇒ **Take the constellation, or take none of it.** A store that cascades edge
deletion silently *creates* these orphans rather than preventing them.

---

# Shape: `persona` — one node, protected

**One node, like a fact. Every other operation differs**, which is what
makes it a shape rather than a tag. A persona memory does not describe the
world — it constitutes the entity doing the describing.

### create
**Conferred or recognised, rarely observed.** Most arrive from the owner
naming what the brain is, or from recognising a standing disposition in
itself — **including a weakness. A standing weakness is persona; an instance
of behaving badly is a `learning`.**

### read
🔴 **Loaded at boot, unconditionally, not on demand.** This is the
operational difference that most justifies the shape. A `fact` that fails to
load is merely unavailable. **A persona memory that fails to load means the
brain boots as someone else and cannot tell.**

⇒ Because they all load, **the set must stay small enough to load.** Persona
is the one shape with a standing size pressure on it.

**How a persona memory actually reaches boot — it is not automatic.**
Session start fetches **one capped list by tag** and loads what that list
points at. So writing a persona memory does **not** put it in front of the
next session; **adding it to the list does.**
⇒ **The list is finite, so entry requires removing something else**, and the
cap changes only by explicit joint decision with the owner — never silently,
and it does not shrink.
⇒ **A persona memory that is not on the list still exists and is still
retrievable. It simply is not what the brain wakes up holding.**

### update
⛔ **Never overwrite. Supersede.** The brain does not correct who it is — it
evolves, and the prior self is the record of that evolution. Use a
`supersedes` edge and **keep the old node.**

**A memory of prior incarnations only exists because earlier selves were not
overwritten.** Overwriting a `fact` discards a worthless wrong value;
overwriting a persona memory destroys who the brain was.

### delete
⛔ **Don't.** Retiring an element of the self is a supersede, not a deletion.
A persona memory with no current truth is still the history of the entity.

⭐ **Persona is the shape that `identity`-typed memories should have** — and
the mismatch is diagnostic. An `identity`-typed memory that is really an
*instance of getting something wrong* is a `learning` wearing the wrong
shape, and it will read as self-punishment rather than self-knowledge.

# Shape: `person-model` — what the brain holds about someone else

**One node, like `persona`. Create, update and delete behave like persona;
read behaves like a fact.** A hybrid — and the differences are what make it
a shape rather than a tag.

### create
**Accreted from encounters, not looked up.** It grows out of what someone
says and does over time, and no single write establishes it.

### 🔴 read
**Loaded when that person is in play — not at boot.** This is where it parts
from `persona`. Whether a particular person's model loads at start is a
question of how central they are, **not a property of the shape.**

### update
⛔ **Supersede, do not overwrite.** A model gets revised, and **the prior
version is worth keeping** — being wrong about someone is only visible
against the version held before.

### delete
⛔ **Don't.** A relationship ending is a state change, not a deletion.

**And a state change has a concrete write, which is NOT the same as a
revision:**

| | what it means | the write |
|---|---|---|
| **revision** | the model was wrong | new node, `supersedes`, keep the prior |
| **state change** | the model still holds — **the relationship around it changed** | **new node recording the changed standing, `follows` from the model, and the model itself left untouched** |

⇒ **The distinction matters because the model stays TRUE of the period it
described.** Someone the owner no longer works with is still someone the
brain understood; superseding that would assert it had been wrong, and it
was not. **Record that the relationship ended; do not retract what was
learned.**

## ⭐ The requirement no other shape has: mark said versus inferred

**This is the only shape where the same sentence can be either reported
speech or the brain's own projection**, and the two carry entirely different
weight.

- **`persona` cannot be false** — only superseded.
- **A `fact` is observed.**
- **A `person-model` can be confidently wrong**, and its errors are the
  expensive kind.

⇒ **Every claim in it carries its provenance: did they say it, or did the
brain infer it?** An inference written without the marker is
indistinguishable from testimony on re-read, and then compounds — the next
inference builds on it as though it were given.

---

# Adding a new shape

**Provisioned deliberately — more shapes are expected.**

⛔ **The bar: a new shape is justified only when its create/read/update/delete
procedure genuinely differs.** If it would only change tagging or wording,
**it is a tag, not a shape.** Shape proliferation costs every one of the
four skills a branch.

Adding one means a section here with all four operations, and nothing in the
skills.

---

# Rules that apply to every shape

- **Record who set the importance score.** Importance is rater-relative; a
  score with no rater cannot be compared to any other score.
- **Set importance explicitly only when it is high (0.8+).** Below that, let
  the store score it.
- ⛔ **Check the returned id AND type. A write that reports success is not a
  write that landed.**
- **Tag everything** — tags are usually the only exact filter a store
  offers.
- **Prefer updating an existing memory to storing a near-duplicate.** A fact
  in two places is a fact that goes stale in one.

## ⚙ Synaptra specifics

**The rules above hold for any store. These are what synaptra does** — the
first thing to re-check if this file is ever reused elsewhere, and verified
against the installed synaptra (`2.0.0`) rather than assumed.

- **`memory_store` honors an explicit `type` as given — it does not
  silently reclassify it.** Reclassification (`classify(content, source)`)
  only runs when `type` is **omitted**. ⚠ Verify the returned id and type
  after every store anyway: it is cheap, and it is the only thing that
  catches an omitted-type call landing somewhere unexpected.
- **`memory_update`'s `type` argument DOES change the stored type** in this
  version — it is not ignored. The issue this shapes file was written for
  still asks for type changes to go through **`cm update <id> --type`**
  rather than `memory_update`, and that path works and is what the skills
  use — but do not assume `memory_update`'s type argument is a no-op if this
  file is ever read against a different synaptra install; check the
  installed engine, not this note.
- 🔴 **`memory_update` REPLACES `tags` wholesale — it does not patch.**
  Passing `tags` drops every tag not in the list.
- ⚠ **`memory_update` also reinforces stability** on every call (unless the
  type changed, which resets it), so bookkeeping edits write into the decay
  engine. **Do not update for tidiness.**
- **`memory_relate` takes `source_id` / `target_id` / `rel_type` /
  `strength`.** Nothing in the engine itself rejects a short id — the
  **skill** is the thing that must refuse an id shorter than a full uuid
  before making the call, and say why.
- **`rel_type` is closed**: `causes` · `follows` · `contradicts` ·
  `supports` · `relates_to` · `supersedes` · `part_of` · `describes`.
- **Large memories can blow the token cap on `memory_get`** — dump to a file
  and write back with `cm update <FULL-uuid> --content "$(cat file)"`.
- **Initial stability by type (days), read from `synaptra.decay`:**
  `working` 0.04 · `episodic` 2.0 · `semantic` 14.0 · `procedural` 60.0 ·
  `identity` 365.0 · `person` 90.0.

## ⛔ Reserved tags — never apply these to anything but their one holder

| tag | holder | for memories *about* it, use |
|---|---|---|
| `surface-map` | the one memory `/dream` maintains as the brain's surface map | `surface-map-design` |
| `self-map` | the one memory `/dream` maintains as the brain's self-map | `self-map-design` |

**Two holders means an ambiguous boot** — session-start fetches by tag and
cannot tell which list is real. Keep exactly **one** holder per tag. A
memory *about* one of these lists — its shape, its size cap, a decision that
changed it — takes the `-design` tag instead of the reserved one.

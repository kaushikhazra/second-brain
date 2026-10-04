# Observe

## Order matters

**Read the criteria from GitHub first** — `gh issue view 25 -R kaushikhazra/second-brain` —
before the diff and before the previous cycle's log. Attack each criterion; do not confirm
it. The criteria drive the cycle.

## The measurement

The number this loop moves is **criteria demonstrably met, out of 30**. Demonstrably means
a check that fails when the behaviour is removed.

⚠ **This issue's criteria split into two kinds and they are not interchangeable.**

```
  MOVE      1-13, 17-20, 25-27   the restructure itself
  PRESERVE  14-16, 21-24, 28-30  the artifact and the brain not moving
```

**A cycle that moves files without re-proving the PRESERVE half has moved the number by
zero.** The whole risk of this work sits in the second column, and a criterion in the
first column that breaks one in the second is a regression, not progress.

⭐ **Criterion 13 is the loop's real target: deleting `.gitattributes` entirely must not
change the archive.** Every other build criterion can be satisfied by tidying. Only 13
proves the subtraction is gone rather than shortened. Aim at it early — it tells you
whether the restructure is real.

## Every cycle, record

- **Criteria met, out of 30**, by number, split MOVE and PRESERVE. Only the first counts.
- How far the number moved, and what moved it. Zero is a legitimate answer.
- **The byte-for-byte comparison against `dist/second-brain-1.0.1.zip`**, run fresh. Not
  remembered from a prior cycle — rebuilt and re-compared.
- The full regression line: `check_shapes.py` · `check_hooks.py` · `check_session_start.py`
  · `check_verify_memory.py` · `check_heartbeat.py` · `check_dream.py` ·
  `check_activation.py`. All pass.
- Any assumption that changed.
- The branch, read from git.

## What will be got wrong

- **A passing build is not a proof.** `build-dist.py` compares its output against
  `git archive` — and if `export-ignore` moves, *both sides of that comparison move
  together*. The builder's own comments say this. **The only check that can fail is one
  stated in absolute terms against the 1.0.1 zip.**

- **`git archive` on a subdirectory keeps the prefix.** `git archive HEAD:src` and
  `git archive HEAD src/` are different trees. Whichever is used, the zip's top level must
  be the brain's own root, not `src/`. Prove it by unpacking, not by reading the code.

- **The dev root and the product root both contain `.claude/`.** Claude Code loads
  `.claude/` from the working root, so `src/.claude/skills/` will not fire at the repo
  root — but `.claude/loop/` and `.claude/specs/` are at the DEV root while
  `.claude/skills/`, `.claude/shared/` and `.claude/hooks/` move into `src/`. **Splitting
  one directory across two roots is where a path reference will be missed.**

- **`.claude/shared/` splits.** `activation.py` is runtime and goes to `src/`.
  `check_activation.py` and `fixture_scratch_brain.py` are development and stay at the dev
  root. They currently sit in the same folder and import each other.

- **The sweep is the work, not the move.** Grep must include untracked files, hidden files
  and binaries — `rg --hidden --no-ignore --binary`. A clean-looking sweep over tracked
  text files is what missed 3,463 files in August. `.mcp.json` is generated; `uv.exe`
  shims bake absolute paths; `__pycache__` holds compiled path constants.

- **Do not edit a cycle log**, here or in any other loop, ever.

- **The 24-recalibration loop is live on its own branch.** `.gitattributes` there carries
  a `fixture_*.py` rule that `main` does not. Do not reconcile the two from inside this
  loop; note the divergence and let issue 24 land on its own.

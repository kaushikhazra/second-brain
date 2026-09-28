# Assumptions

Standing inputs that must survive a rewrite of `action.md`.

## Settled

- **The folder is `src/`.** Kaushik's ruling, 2026-09-28, over `brain/` and `template/`.
  Not reopened by this loop.

- **The diagnosis, and he confirmed it.** The repo does not *contain* the deliverable —
  the repo **is** the deliverable, with development files beside it, subtracted at build
  time. So the build inverts: from *ship everything except the list* to *ship `src/`*.
  That inversion is the point of the issue, not a side effect of it.

- **The artifact is the fixed point.** This work changes where files live in the repo and
  must change nothing a user receives. `VERSION` does not move for this work.

- **The reference is the `v1.0.1` git tag**, measured in cycle 1 as 35 files, and NOT
  `dist/second-brain-1.0.1.zip`. `dist/` is gitignored and untracked, and
  `build-dist.py` unlinks that exact filename on every run. ⛔ **Do not run
  `build-dist.py` while `VERSION` reads `1.0.1`** — it deletes the reference, and
  criterion 16 forbids bumping `VERSION` to avoid that.

- **`README.md` is the user's and moves to `src/`.** Kaushik's ruling, 2026-09-28.

## About this repo, measured 2026-09-28

- **Root holds:** `CLAUDE.md` · `README.md` · `VERSION` · `brain.bat` ·
  `brain-claude-sandbox.bat` · `news-keywords.txt` · `.mcp.json` · `.gitignore` ·
  `.gitattributes` · `.claude/` · `tools/` · `dist/` · `.ruff_cache/` · `.tmp/`.

- **`.gitattributes` on `main` carries FOUR `export-ignore` rules:** `.gitattributes`
  itself, `tools/`, `.claude/skills/*/scripts/test_*.py`, `.claude/loop/`, and
  `check_*.py`. ⚠ A fifth, `fixture_*.py`, exists **only on `feature/24-recalibration`**
  and is not on `main`.

- **Fourteen shipped skills** in `.claude/skills/`: agent-creator · create-memory ·
  curiosity · delete-memory · dream · heartbeat · init-brain · local-agent · news ·
  read-memory · recall-session · session-end · session-start · update-memory.

- **`build-dist.py` builds from `git archive`, never from the working directory** — a
  deliberate choice so a dirty tree cannot ship. It asserts a `FORBIDDEN` list
  (`.venv`, `.python`, `synaptra-data`, `.mcp.json`, `.self-aware`, `.claude/specs`,
  `.tmp`, `.git/`, `uv.exe`, `__pycache__`) and a `FORBIDDEN_GLOBS` list (`test_*.py`)
  in absolute terms, because the set-equality check against `git archive` cannot catch
  an exclusion regression.

- **There is no test framework** — no pytest, no conftest, no CI. Checks are standalone
  `check_*.py` argparse scripts, run by hand.

- Scratch trees live at `C:/Projects/.tmp/second-brain-loop-N/`, never in the repo and
  never in a system temp folder.

## 🔴 `src/` is a fact about the REPO, never about the brain

**Inside a user's install there is no `src/`.** A shipped file may only contain paths
relative to the brain's own root.

```
  what a shipped file SAYS      .claude/shared/memory/memory-shapes.md
  where the dev repo FINDS it   src/.claude/shared/memory/memory-shapes.md
```

⛔ **These are different strings and a check must not conflate them.** Assert the
brain-relative path; resolve the filesystem location separately.

⚠ **Cycle 2 got this wrong and it is the way this work ships something broken.** It
repointed `check_shapes.py`'s `SHAPES_FILE_REL` at `src/...`, so the check demanded that
the four memory skills reference `src/` — which would have been correct for the repo and
wrong for every install. `check_shapes.py` went 5/5 to 4/5 and that is the only reason it
was caught.

⭐ **Not added to issue #25 as new criteria, deliberately.** `goal.md` and `observe.md` are
immutable and measure *N of 30 by number*; criteria that grow mid-loop mean it can never
converge. The rule is enforced by `check_shapes.py` and by this section.

**Measured 2026-09-28 after the fix:** nothing under `src/` contains the string `src/`.

## Constraints from the orchestrator

- **Behaviour-preserving for the user.** The archive's path set and file contents do not
  move. Where the repo puts a file is free; where the user finds it is not.

- **Zero hardcoding.** A component resolves its own location at runtime, relative to
  itself or from an environment variable its launcher sets. The test is whether a fresh
  install still works if the folder is renamed. This applies to what a step *writes* —
  a provisioner that bakes a resolved path into a shim, manifest or generated config has
  hardcoded it.

- **One command per shell invocation.** No `;`, `&&` or `||` chaining, in bash or
  PowerShell. Destructive commands take absolute paths.

- **Do not tangle with issue 24.** It is live on `feature/24-recalibration`.

- **The builder's overwrite guard is outside the 30 criteria.** Cycle 4 made
  `build-dist.py` refuse to overwrite an existing archive (pass `--force` to override).
  This is a safety change so the loop.md prohibition on running the builder is no longer
  strictly needed. It does not count toward the criteria number.

## Unsettled

- **Whether the dev root gets its own `.claude/skills/`.** Deliberately out of scope for
  issue 25 and not to be decided inside this loop. Criterion 8 holds either way, because
  Claude Code loads `.claude/` from the working root.

- **How `git archive` should be invoked for a subtree**, and whether the prefix is
  stripped by the archive command or by the builder. Either is acceptable; the unpacked
  top level is what the criterion measures.

*(The `README.md` question was here and is now settled above — it is the user's.)*

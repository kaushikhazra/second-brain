#!/usr/bin/env python3
"""One scratch-brain builder, extracted from the 27 copy-pasted
`build_scratch_project()` functions that grew across `.claude/shared/memory/` and
`.claude/skills/*/` during loops 2-8.

A scripted-agent check needs a throwaway brain to point `claude -p` at: a project
directory holding only the skills under test, whatever shared files those skills read,
and a `.mcp.json` that aims synaptra at a scratch store instead of the owner's. Every
check built that tree itself, and the copies drifted -- not in behaviour, but in shape,
which is worse, because a reader cannot tell a meaningful difference from a stale one.

Normalising the 27 copies (string literals stripped) yields 22 distinct shapes. Almost
all of that spread is `black` wrapping a subprocess argument list differently. The real
variation is small and enumerable, and it is exactly this function's keyword arguments:

    skills            which skill directories to copy
    shared            which files under .claude/shared/ the skills read
    claude_md         the prompt context the scratch session wakes up in
    persona / user    present or absent (a heartbeat needs them, a raw store check does not)
    memory_guard      the PreToolUse hook plus the settings.json that fires it
    mcp               "healthy" -> points at data_dir | "broken" -> a nonexistent exe | None
    venv_junction     .claude/.venv junctioned to the repo venv, for skills that resolve it
    clean             remove an existing tree first

⚠ This module is test scaffolding, not runtime. It is `export-ignore`d (see
`.gitattributes`, pattern `fixture_*.py`) so it never reaches a user's install. Nothing
in any skill imports it.

⛔ A fixture brain is SYNTHETIC. Never copy a real memory store, a real `persona.md`, or
anyone's memories into one. The defaults below are deliberately obvious test doubles.

Usage from a check in `.claude/shared/memory/` or `.claude/skills/<skill>/`:

    import sys
    from pathlib import Path

    CLAUDE_DIR = Path(__file__).resolve().parent.parent.parent   # -> .claude
    sys.path.insert(0, str(CLAUDE_DIR / "shared"))
    from fixture_scratch_brain import build_scratch_brain       # noqa: E402

    build_scratch_brain(
        SCRATCH_PROJECT,
        skills=("create-memory", "heartbeat"),
        shared=("memory/memory-shapes.md",),
        claude_md="# CLAUDE.md\\n\\n...",
        persona=True,
        user=True,
        memory_guard=True,
        mcp="healthy",
        data_dir=SCRATCH_DATA,
    )
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Iterable, Sequence
from pathlib import Path

__all__ = [
    "build_scratch_brain",
    "DEFAULT_PERSONA_MD",
    "DEFAULT_USER_MD",
    "DEFAULT_HOOK_MATCHER",
    "WRITE_HOOK_MATCHER",
    "CLAUDE_DIR",
]

# -> .claude, resolved from this file, never frozen as an absolute path
CLAUDE_DIR = Path(__file__).resolve().parent.parent

# The test double every existing copy used verbatim. Obviously not a real brain.
DEFAULT_PERSONA_MD = (
    "# Testa -- Persona\n\n## Identity\n\n- **Name**: Testa\n- **Voice**: they/them\n"
    "- **Character**: Careful and direct.\n\n## Roles\n\n| Role | What they do |\n"
    "|------|---------------|\n| Research assistant | Finds information |\n\n"
    "## Proactivity\n\nModerate.\n\n## Communication Style\n\n- Direct\n"
)
DEFAULT_USER_MD = "# Test User\n\n## Personal\n\n- **Name**: Test User\n"

# What most checks guard: the three calls that WRITE through synaptra.
DEFAULT_HOOK_MATCHER = (
    "mcp__synaptra__memory_store"
    "|mcp__synaptra__memory_update"
    "|mcp__synaptra__memory_relate"
)
# The dream checks additionally guard the destructive three.
WRITE_HOOK_MATCHER = (
    DEFAULT_HOOK_MATCHER
    + "|mcp__synaptra__memory_archive"
    + "|mcp__synaptra__memory_delete"
    + "|mcp__synaptra__memory_unrelate"
)

_BROKEN_EXE = "this-does-not-exist.exe"


def _clean(project: Path) -> None:
    """Remove a previous tree.

    The junction is dropped FIRST and with `os.rmdir`: `shutil.rmtree` on a directory
    junction would descend into the REAL venv and delete it. Every copy that used a
    junction did this, and it is the one ordering in here that is not cosmetic.
    """
    venv_link = project / ".claude" / ".venv"
    if venv_link.is_dir():
        os.rmdir(venv_link)
    if project.exists():
        shutil.rmtree(project)


def _junction(project: Path, repo_root: Path) -> None:
    link = project / ".claude" / ".venv"
    link.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(repo_root / ".venv")],
        capture_output=True,
        text=True,
        check=True,
    )


def _copy_skills(project: Path, repo_root: Path, skills: Iterable[str]) -> None:
    """Copy each skill's own files. Top level only -- `glob("*")` plus an `is_file`
    test, which is what every copy did, so a skill's `scripts/` or `tools/` subdirectory
    is deliberately NOT carried into the scratch tree."""
    for skill in skills:
        dest = project / ".claude" / "skills" / skill
        dest.mkdir(parents=True, exist_ok=True)
        src = repo_root / "skills" / skill
        for f in src.glob("*"):
            if f.is_file():
                shutil.copy(f, dest / f.name)


def _copy_shared(project: Path, repo_root: Path, shared: Iterable[str]) -> None:
    """Copy files from `.claude/shared/`, keeping their relative path.

    `"memory/memory-shapes.md"` lands at `.claude/shared/memory/memory-shapes.md`;
    `"activation.py"` lands at `.claude/shared/activation.py`.
    """
    for rel in shared:
        src = repo_root / "shared" / rel
        dest = project / ".claude" / "shared" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)


def _write_guard(project: Path, repo_root: Path, matcher: str, timeout: int) -> None:
    hooks = project / ".claude" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    shutil.copy(repo_root / "hooks" / "memory_guard.py", hooks / "memory_guard.py")
    (project / ".claude" / "settings.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": matcher,
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python .claude/hooks/memory_guard.py",
                                    "timeout": timeout,
                                }
                            ],
                        }
                    ]
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_mcp(project: Path, repo_root: Path, mcp: str, data_dir: Path | None) -> None:
    if mcp == "healthy":
        if data_dir is None:
            raise ValueError(
                'mcp="healthy" needs data_dir -- otherwise synaptra '
                "falls back to the user-level store at ~/.synaptra/data "
                "and the check silently reads the wrong database"
            )
        server: dict = {
            "type": "stdio",
            "command": str(repo_root / ".venv" / "Scripts" / "synaptra.exe"),
            "args": ["--transport", "stdio"],
            "env": {
                "SYNAPTRA_BACKEND": "surrealkv-file",
                "SYNAPTRA_DB": str(data_dir),
            },
        }
    elif mcp == "broken":
        # No `env` block: a server that cannot spawn never reads one, and every
        # copy that built this variant omitted it.
        server = {
            "type": "stdio",
            "command": str(repo_root / ".venv" / "Scripts" / _BROKEN_EXE),
            "args": ["--transport", "stdio"],
        }
    else:
        raise ValueError(f'mcp must be "healthy", "broken" or None, got {mcp!r}')

    (project / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"synaptra": server}}, indent=2), encoding="utf-8"
    )


def build_scratch_brain(
    project: Path,
    *,
    claude_md: str,
    skills: Sequence[str] = (),
    shared: Sequence[str] = (),
    persona: bool | str = False,
    user: bool | str = False,
    memory_guard: bool = False,
    hook_matcher: str = DEFAULT_HOOK_MATCHER,
    hook_timeout: int = 5,
    mcp: str | None = None,
    data_dir: Path | None = None,
    venv_junction: bool = False,
    extra_files: dict[str, str] | None = None,
    clean: bool = True,
    repo_root: Path | None = None,
) -> Path:
    """Build a throwaway brain at `project` and return that path.

    `persona` / `user`: True for the default test double, a string for custom text,
    False to leave the file out entirely.

    `extra_files`: paths relative to the project root mapped to their text content,
    for the one-off files a single check needs (an activation record, a seeded list).

    `repo_root` defaults to this brain's own `.claude/`, resolved from this file.
    """
    repo_root = repo_root or CLAUDE_DIR
    project = Path(project)

    if clean:
        _clean(project)

    (project / ".claude").mkdir(parents=True, exist_ok=True)

    if venv_junction:
        _junction(project, repo_root)
    if skills:
        _copy_skills(project, repo_root, skills)
    if shared:
        _copy_shared(project, repo_root, shared)
    if memory_guard:
        _write_guard(project, repo_root, hook_matcher, hook_timeout)

    if persona is not False:
        text = DEFAULT_PERSONA_MD if persona is True else persona
        (project / "persona.md").write_text(text, encoding="utf-8")
    if user is not False:
        text = DEFAULT_USER_MD if user is True else user
        (project / "user.md").write_text(text, encoding="utf-8")

    (project / "CLAUDE.md").write_text(claude_md, encoding="utf-8")

    if mcp is not None:
        _write_mcp(project, repo_root, mcp, data_dir)

    for rel, content in (extra_files or {}).items():
        dest = project / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

    return project

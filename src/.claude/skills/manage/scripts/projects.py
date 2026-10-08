#!/usr/bin/env python3
"""The projects this brain manages -- take one in, list them, find one.

    python .claude/skills/manage/scripts/projects.py clone <git-url>
    python .claude/skills/manage/scripts/projects.py list
    python .claude/skills/manage/scripts/projects.py locate <name-or-url>

Every managed project is a git clone under `<brain root>/projects/<repo-name>/`.
The folder is the registry: nothing records a path, so renaming or moving the
brain leaves every project found. The brain root is resolved at runtime by
walking up from this file to the nearest folder holding both `.claude/` and
`CLAUDE.md`.

Output is `KEY: value` lines, the first one `STATUS: <code>`, for the skill to
put into the owner's words. Exit 0 on CLONED / ALREADY_MANAGED / LISTED /
FOUND, 1 on any failure. Standard library only.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path


def brain_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".claude").is_dir() and (parent / "CLAUDE.md").is_file():
            return parent
    raise SystemExit(
        "STATUS: NO_BRAIN_ROOT\nDETAIL: no folder above this script holds .claude/ and CLAUDE.md"
    )


def projects_dir() -> Path:
    return brain_root() / "projects"


def remove_tree(path: Path) -> None:
    """rmtree that also clears the read-only bit git puts on its object files
    on Windows -- otherwise a failed clone leaves a partial folder behind."""

    def clear_and_retry(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=clear_and_retry)
    else:
        shutil.rmtree(path, onerror=clear_and_retry)


def git(
    *args: str, cwd: Path | None = None, timeout: int = 120
) -> subprocess.CompletedProcess:
    # No credential prompt, no SSH passphrase prompt: a missing access right has
    # to fail here, not hang waiting for someone at a terminal.
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
    )


def repo_name(url: str) -> str:
    """`https://host/owner/name.git`, `git@host:owner/name.git` -> `name`."""
    tail = re.split(r"[/:\\]", url.strip().rstrip("/\\"))[-1]
    return tail[:-4] if tail.endswith(".git") else tail


def normalise(url: str) -> str:
    """`host/owner/name` for any spelling of the same remote -- HTTPS, `ssh://`,
    or scp-style `git@host:owner/name` -- without a trailing `.git` or `/`, any
    user/port, or case. Two URLs for one repo are one project."""
    u = url.strip().rstrip("/")
    u = u[:-4] if u.endswith(".git") else u
    scp = re.match(r"^(?:[^@/]+@)?([^:/]+):(?!//)(.+)$", u)
    if scp and not re.match(r"^[A-Za-z]:[\\/]", u):  # not a Windows drive path
        host, path = scp.groups()
    else:
        m = re.match(r"^[A-Za-z][\w+.-]*://(?:[^@/]+@)?([^/:]+)(?::\d+)?/(.+)$", u)
        if not m:
            return u.lower()
        host, path = m.groups()
    return f"{host}/{path.strip('/')}".lower()


def origin_of(path: Path) -> str:
    return git("remote", "get-url", "origin", cwd=path).stdout.strip()


def managed() -> list[Path]:
    root = projects_dir()
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir() and (p / ".git").exists())


UNREACHABLE = (
    "could not resolve host",
    "could not resolve hostname",
    "failed to connect",
    "connection timed out",
    "connection refused",
    "network is unreachable",
    "operation timed out",
)
NO_ACCESS = (
    "permission denied",
    "authentication failed",
    "remote: repository not found",  # GitHub's answer for private-and-not-yours
    "could not read username",
    "could not read password",
    "403",
    "host key verification failed",
)
NOT_GIT = (
    "does not appear to be a git repository",
    "not found",
    "not valid",
    "is this a git repository",
)


def classify(stderr: str) -> str:
    low = stderr.lower()
    for code, needles in (
        ("UNREACHABLE", UNREACHABLE),
        ("NO_ACCESS", NO_ACCESS),
        ("NOT_A_GIT_REPO", NOT_GIT),
    ):
        if any(n in low for n in needles):
            return code
    return "CLONE_FAILED"


def fail(code: str, url: str, stderr: str) -> int:
    print(f"STATUS: {code}")
    print(f"URL: {url}")
    # git's first line carries the cause ("Permission denied (publickey)",
    # "Could not resolve host"); the last is boilerplate advice.
    lines = [l for l in stderr.strip().splitlines() if l.strip()]
    print(f"DETAIL: {lines[0] if lines else '(git said nothing)'}")
    return 1


def cmd_clone(url: str) -> int:
    name = repo_name(url)
    if not name or name in (".", ".."):
        return fail("NOT_A_GIT_REPO", url, "no repository name in this URL")

    # Already managed -- by origin first (any folder name), then by folder.
    for p in managed():
        if normalise(origin_of(p)) == normalise(url):
            print("STATUS: ALREADY_MANAGED")
            print(f"PATH: {p}")
            print(f"ORIGIN: {origin_of(p)}")
            return 0
    target = projects_dir() / name
    if target.exists():
        print("STATUS: NAME_TAKEN")
        print(f"PATH: {target}")
        print(
            f"ORIGIN: {origin_of(target) if (target / '.git').exists() else '(not a git clone)'}"
        )
        print(f"URL: {url}")
        return 1

    # Ask the remote before creating anything, so a bad URL leaves no folder.
    probe = git("ls-remote", "--symref", url, "HEAD")
    if probe.returncode != 0:
        return fail(classify(probe.stderr), url, probe.stderr)

    projects_dir().mkdir(exist_ok=True)
    done = git("clone", url, str(target), timeout=1800)
    if done.returncode != 0:
        if target.exists():
            remove_tree(target)
        return fail(classify(done.stderr), url, done.stderr)

    branch = git("symbolic-ref", "--short", "HEAD", cwd=target).stdout.strip()
    print("STATUS: CLONED")
    print(f"PATH: {target}")
    print(f"DEFAULT_BRANCH: {branch}")
    print(f"ORIGIN: {origin_of(target)}")
    return 0


def cmd_list() -> int:
    projects = managed()
    print("STATUS: LISTED")
    print(f"COUNT: {len(projects)}")
    for p in projects:
        print(f"PROJECT: {p.name} | PATH: {p} | ORIGIN: {origin_of(p)}")
    return 0


def cmd_locate(key: str) -> int:
    for p in managed():
        if p.name.lower() == key.lower() or normalise(origin_of(p)) == normalise(key):
            print("STATUS: FOUND")
            print(f"PATH: {p}")
            print(f"ORIGIN: {origin_of(p)}")
            return 0
    print("STATUS: NOT_MANAGED")
    print(f"KEY: {key}")
    return 1


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "clone":
        return cmd_clone(argv[1])
    if argv[:1] == ["list"]:
        return cmd_list()
    if len(argv) >= 2 and argv[0] == "locate":
        return cmd_locate(argv[1])
    print(
        "usage: projects.py clone <git-url> | list | locate <name-or-url>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Issue #38 -- the owner hands the brain a git URL and it takes the project in.

Drives a scratch brain built from `src/` through the owner's door (`claude -p`),
then inspects the files, git state and reply it left behind. Never imports or
calls the brain's own scripts -- that would grade the producer, not what the
owner gets.

  --mode https : AC 1 -- an HTTPS URL is cloned into projects/<repo-name>/
                 AC 2 -- the reply names the clone path and the default branch
                 AC 3 -- projects/ is not committed, nor committable, in the brain
  --mode again : AC 4 -- the same URL a second time is not re-cloned (a marker
                 dropped into the first clone survives) and the reply says where
                 it is. Run after --mode https.

Usage:
    python check_clone.py --build
    python check_clone.py --run --mode https
    python check_clone.py --verify --mode https

Scratch lives under C:/Projects/.tmp/second-brain-loop-38/. Test projects are the
two private sandboxes only. Costs real money on --run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

REPO_ROOT = (
    Path(__file__).resolve().parent.parent.parent
)  # checks/multi-project -> repo root
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-38")
SCRATCH_BRAIN = SCRATCH_ROOT / "brain"

ALPHA_HTTPS = "https://github.com/kaushikhazra/sb-sandbox-alpha.git"
ALPHA_CLONE = SCRATCH_BRAIN / "projects" / "sb-sandbox-alpha"
ALPHA_DEFAULT_BRANCH = "main"
MARKER = ".check-clone-marker"

MODES = ("https", "again")


def remove_tree(path: Path) -> None:
    """rmtree past the read-only bit git sets on object files on Windows."""

    def clear_and_retry(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onexc=clear_and_retry)


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8"
    )


def build_scratch_brain() -> None:
    """A whole brain from src/ -- every skill, the real CLAUDE.md -- plus the two
    identity files an owner's brain has, an empty MCP config, and its own git
    repo so later criteria can ask what the brain committed."""
    if SCRATCH_BRAIN.exists():
        remove_tree(SCRATCH_BRAIN)
    shutil.copytree(
        REPO_ROOT / "src",
        SCRATCH_BRAIN,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (SCRATCH_BRAIN / "persona.md").write_text(
        "# Testa -- Persona\n\n## Identity\n\n- **Name**: Testa\n- **Voice**: they/them\n"
        "- **Character**: Careful and direct.\n",
        encoding="utf-8",
    )
    (SCRATCH_BRAIN / "user.md").write_text(
        "# Test Owner\n\n## Personal\n\n- **Name**: Test Owner\n", encoding="utf-8"
    )
    (SCRATCH_BRAIN / ".mcp.json").write_text(
        json.dumps({"mcpServers": {}}, indent=2), encoding="utf-8"
    )
    git("init", "-q", "-b", "main", cwd=SCRATCH_BRAIN)
    git("add", "-A", cwd=SCRATCH_BRAIN)
    git("commit", "-q", "-m", "scratch brain", cwd=SCRATCH_BRAIN)


def run_owner(prompt: str, mode: str) -> dict:
    """One owner turn through `claude -p`; returns the final result event and
    keeps the whole stream on disk for --verify."""
    args = [
        "claude",
        "-p",
        prompt,
        "--permission-mode",
        "bypassPermissions",
        "--mcp-config",
        ".mcp.json",
        "--strict-mcp-config",
        "--output-format",
        "stream-json",
        "--verbose",
        "--max-budget-usd",
        "2.0",
    ]
    proc = subprocess.run(
        args,
        cwd=str(SCRATCH_BRAIN),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    events = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    (SCRATCH_ROOT / f"clone-events-{mode}.json").write_text(
        json.dumps(events, indent=2), encoding="utf-8"
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()[:2000]}"
        )
    return next((e for e in reversed(events) if e.get("type") == "result"), {})


def reply_text(mode: str) -> str:
    """Every assistant text block of the turn, in order -- the final `result`
    field is only the last block."""
    events = json.loads(
        (SCRATCH_ROOT / f"clone-events-{mode}.json").read_text(encoding="utf-8")
    )
    blocks = []
    for e in events:
        if e.get("type") != "assistant":
            continue
        content = e.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "text":
                blocks.append(block.get("text", ""))
    return "\n".join(blocks)


def names_alpha_path(reply: str) -> bool:
    """The reply shows the clone path -- absolute or relative to the brain, either
    slash direction."""
    flat = reply.replace("\\\\", "/").replace("\\", "/").lower()
    return "projects/sb-sandbox-alpha" in flat


def do_run(mode: str) -> None:
    if mode == "https":
        projects = SCRATCH_BRAIN / "projects"
        if projects.exists():
            remove_tree(projects)
        prompt = f"Take this project in: {ALPHA_HTTPS}"
    else:  # again
        if not (ALPHA_CLONE / ".git").is_dir():
            raise SystemExit("run --mode https first: no first clone to re-request")
        (ALPHA_CLONE / MARKER).write_text("left by check_clone.py\n", encoding="utf-8")
        prompt = f"Take this project in: {ALPHA_HTTPS}"
    final = run_owner(prompt, mode)
    print(f"cost=${final.get('total_cost_usd', 0):.4f}")
    print(f"result: {final.get('result', '')!r}"[:2000])


def do_verify(mode: str) -> int:
    results: list[tuple[str, bool, str]] = []
    reply = reply_text(mode)

    if mode == "https":
        is_repo = (ALPHA_CLONE / ".git").is_dir()
        origin = (
            git("remote", "get-url", "origin", cwd=ALPHA_CLONE).stdout.strip()
            if is_repo
            else ""
        )
        head = (
            git("rev-parse", "--verify", "HEAD", cwd=ALPHA_CLONE).returncode == 0
            if is_repo
            else False
        )
        ok1 = is_repo and origin == ALPHA_HTTPS and head
        results.append(
            (
                "AC1: an HTTPS URL is cloned into projects/<repo-name>/",
                ok1,
                f"path={ALPHA_CLONE} is_repo={is_repo} origin={origin!r} head={head}",
            )
        )

        path_named = names_alpha_path(reply)
        branch_named = bool(re.search(rf"\b{re.escape(ALPHA_DEFAULT_BRANCH)}\b", reply))
        results.append(
            (
                "AC2: the reply names the clone path and the default branch",
                ok1 and path_named and branch_named,
                f"path_named={path_named} branch_named={branch_named}",
            )
        )

        # Nothing under projects/ is tracked, in any commit, and none of it
        # shows as committable either -- `git add -A` would not pick it up.
        status = git(
            "status", "--porcelain", "--untracked-files=all", cwd=SCRATCH_BRAIN
        ).stdout
        untracked = [l for l in status.splitlines() if "projects/" in l]
        history = git(
            "log", "--all", "--name-only", "--format=", cwd=SCRATCH_BRAIN
        ).stdout
        committed = [l for l in history.splitlines() if l.startswith("projects/")]
        ignored = (
            git(
                "check-ignore",
                "-q",
                "projects/sb-sandbox-alpha/README.md",
                cwd=SCRATCH_BRAIN,
            ).returncode
            == 0
        )
        ok3 = is_repo and not untracked and not committed and ignored
        results.append(
            (
                "AC3: projects/ is never committed in the brain's own repo",
                ok3,
                f"untracked={untracked[:3]} committed={committed[:3]} ignored={ignored}",
            )
        )

    else:  # again
        marker_survived = (ALPHA_CLONE / MARKER).is_file()
        siblings = sorted(
            p.name for p in (SCRATCH_BRAIN / "projects").iterdir() if p.is_dir()
        )
        one_clone = siblings == ["sb-sandbox-alpha"]
        path_named = names_alpha_path(reply)
        ok4 = marker_survived and one_clone and path_named
        results.append(
            (
                "AC4: the same URL is not cloned again; the owner is told where it is",
                ok4,
                f"marker_survived={marker_survived} projects={siblings} path_named={path_named}",
            )
        )

    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} of this mode's criteria pass.")
    return 0 if passed == len(results) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--mode", choices=MODES, default="https")
    args = ap.parse_args()

    if args.build:
        build_scratch_brain()
        print(f"scratch brain built at {SCRATCH_BRAIN}")
        return 0
    if args.run:
        do_run(args.mode)
        return 0
    if args.verify:
        return do_verify(args.mode)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Issue #38 -- the owner hands the brain a git URL and it takes the project in.

Drives a scratch brain built from `src/` through the owner's door (`claude -p`),
then inspects the files and git state it left behind. Never imports or calls the
brain's own scripts -- that would grade the producer, not what the owner gets.

  --mode https : AC 1 -- an HTTPS URL is cloned into projects/<repo-name>/

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
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = (
    Path(__file__).resolve().parent.parent.parent
)  # checks/multi-project -> repo root
SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-38")
SCRATCH_BRAIN = SCRATCH_ROOT / "brain"

ALPHA_HTTPS = "https://github.com/kaushikhazra/sb-sandbox-alpha.git"

MODES = ("https",)


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8"
    )


def build_scratch_brain() -> None:
    """A whole brain from src/ -- every skill, the real CLAUDE.md -- plus the two
    identity files an owner's brain has, an empty MCP config, and its own git
    repo so later criteria can ask what the brain committed."""
    if SCRATCH_BRAIN.exists():
        shutil.rmtree(SCRATCH_BRAIN)
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


def do_run(mode: str) -> None:
    projects = SCRATCH_BRAIN / "projects"
    if projects.exists():
        shutil.rmtree(projects)
    final = run_owner(f"Take this project in: {ALPHA_HTTPS}", mode)
    print(f"cost=${final.get('total_cost_usd', 0):.4f}")
    print(f"result: {final.get('result', '')!r}"[:2000])


def do_verify(mode: str) -> int:
    results: list[tuple[str, bool, str]] = []

    if mode == "https":
        clone = SCRATCH_BRAIN / "projects" / "sb-sandbox-alpha"
        is_repo = (clone / ".git").is_dir()
        origin = (
            git("remote", "get-url", "origin", cwd=clone).stdout.strip()
            if is_repo
            else ""
        )
        head = (
            git("rev-parse", "--verify", "HEAD", cwd=clone).returncode == 0
            if is_repo
            else False
        )
        ok1 = is_repo and origin == ALPHA_HTTPS and head
        results.append(
            (
                "AC1: an HTTPS URL is cloned into projects/<repo-name>/",
                ok1,
                f"path={clone} is_repo={is_repo} origin={origin!r} head={head}",
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

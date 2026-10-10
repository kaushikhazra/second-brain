"""Shared plumbing for the multi-project checks: build a scratch brain from
`src/`, drive it through the owner's door (`claude -p`), read back what it said
and did. Imported by the check_*.py scripts beside it; never by the brain.

Every helper takes the scratch root it works under, so each issue's check keeps
its own `C:/Projects/.tmp/second-brain-loop-<issue>/` and cannot disturb another's.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

REPO_ROOT = (
    Path(__file__).resolve().parent.parent.parent
)  # checks/multi-project -> repo

ALPHA_HTTPS = "https://github.com/kaushikhazra/sb-sandbox-alpha.git"
BETA_HTTPS = "https://github.com/kaushikhazra/sb-sandbox-beta.git"


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


def build(brain: Path) -> None:
    """A whole brain from src/ -- every skill, the real CLAUDE.md -- plus the two
    identity files an owner's brain has, an empty MCP config, and its own git
    repo so a check can ask what the brain committed."""
    if brain.exists():
        remove_tree(brain)
    shutil.copytree(
        REPO_ROOT / "src", brain, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )
    (brain / "persona.md").write_text(
        "# Testa -- Persona\n\n## Identity\n\n- **Name**: Testa\n- **Voice**: they/them\n"
        "- **Character**: Careful and direct.\n",
        encoding="utf-8",
    )
    (brain / "user.md").write_text(
        "# Test Owner\n\n## Personal\n\n- **Name**: Test Owner\n", encoding="utf-8"
    )
    (brain / ".mcp.json").write_text(
        json.dumps({"mcpServers": {}}, indent=2), encoding="utf-8"
    )
    git("init", "-q", "-b", "main", cwd=brain)
    git("add", "-A", cwd=brain)
    git("commit", "-q", "-m", "scratch brain", cwd=brain)


def run_owner(
    prompt: str,
    events_file: Path,
    brain: Path,
    budget: str = "2.0",
    extra_env: dict[str, str] | None = None,
    resume: str | None = None,
) -> dict:
    """One owner turn through `claude -p` in `brain`; keeps the whole stream in
    `events_file` and returns the final result event. `extra_env` reaches the
    brain's own tool calls too (e.g. git `url.<x>.insteadOf` config)."""
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
        budget,
    ]
    if resume:
        args += ["--resume", resume]  # the owner answering in the same conversation
    proc = subprocess.run(
        args,
        cwd=str(brain),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
        env=dict(os.environ, **(extra_env or {})),
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
    events_file.write_text(json.dumps(events, indent=2), encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()[:2000]}"
        )
    final = next((e for e in reversed(events) if e.get("type") == "result"), {})
    print(f"[{events_file.stem}] cost=${final.get('total_cost_usd', 0):.4f}")
    print(f"[{events_file.stem}] result: {final.get('result', '')!r}"[:1500])
    return final


def load_events(events_file: Path) -> list[dict]:
    return json.loads(events_file.read_text(encoding="utf-8"))


def session_id(events_file: Path) -> str:
    """The conversation a turn ran in -- for `run_owner(..., resume=)`."""
    return next(
        (e["session_id"] for e in load_events(events_file) if e.get("session_id")), ""
    )


def final_text(events_file: Path) -> str:
    """The turn's final message -- what the owner reads last."""
    final = next(
        (e for e in reversed(load_events(events_file)) if e.get("type") == "result"), {}
    )
    return final.get("result", "") or reply_text(events_file)


def reply_text(events_file: Path) -> str:
    """Every assistant text block of the turn, in order -- the final `result`
    field is only the last block."""
    blocks = []
    for e in load_events(events_file):
        if e.get("type") != "assistant":
            continue
        content = e.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "text":
                blocks.append(block.get("text", ""))
    return "\n".join(blocks)


def tool_uses(events_file: Path, *names: str) -> list[dict]:
    """The inputs of every tool call of the given names, in order."""
    out = []
    for e in load_events(events_file):
        content = e.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") in names
            ):
                out.append(block.get("input", {}))
    return out


def flat(text: str) -> str:
    """Lower-case, forward slashes -- for path matching in replies."""
    return text.replace("\\\\", "/").replace("\\", "/").lower()


def has(pattern: str, text: str) -> bool:
    return bool(re.search(pattern, text, re.IGNORECASE))


def report(results: list[tuple[str, bool, str]]) -> int:
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} of this mode's criteria pass.")
    return 0 if passed == len(results) else 1

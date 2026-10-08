#!/usr/bin/env python3
"""Issue #38 -- the owner hands the brain a git URL and it takes the project in.

Drives a scratch brain built from `src/` through the owner's door (`claude -p`),
then inspects the files, git state, reply and tool trace it left behind. Never
imports or calls the brain's own scripts -- that would grade the producer, not
what the owner gets.

  --mode https    : AC 1 -- an HTTPS URL is cloned into projects/<repo-name>/
                    AC 2 -- the reply names the clone path and the default branch
                    AC 3 -- projects/ is not committed, nor committable, in the brain
  --mode again    : AC 4 -- alpha asked for again, by its HTTPS and by its SSH
                    spelling: a marker dropped into the first clone survives, no
                    `git clone` runs, the reply says it is already there and where,
                    and does not read as a failure.
  --mode fail     : AC 5 -- unreachable host, missing access (an SSH URL; this
                    machine has no GitHub key), not a git repo: each reply names
                    its own cause and none of the other two, and no folder is left.
  --mode list     : AC 6 -- the reply names each project's path and origin URL.
  --mode relocate : AC 7 -- the brain copied to a renamed folder lists alpha at
                    the new path and does not re-clone it.

Run the modes in that order: each one after `https` uses the clone it left.

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
MOVED_BRAIN = SCRATCH_ROOT / "brain-moved"

ALPHA_HTTPS = "https://github.com/kaushikhazra/sb-sandbox-alpha.git"
ALPHA_SSH = "git@github.com:kaushikhazra/sb-sandbox-alpha.git"
ALPHA_CLONE = SCRATCH_BRAIN / "projects" / "sb-sandbox-alpha"
ALPHA_DEFAULT_BRANCH = "main"
MARKER = ".check-clone-marker"

# AC 5's three causes: the URL the owner hands over, and what the reply must say.
FAILURES = {
    "unreachable": (
        "https://no-such-host-xyz.invalid/a/b.git",
        r"(?:could|does|did)(?: not|n't) (?:be )?(?:reach|resolve)|unreachable|network",
    ),
    "noaccess": (
        "git@github.com:kaushikhazra/sb-sandbox-beta.git",
        r"\baccess\b|permission",
    ),
    "notgit": (
        "https://example.com/",
        r"(?:is ?n[o']t|not|doesn't point (?:at|to)|does not point (?:at|to)) a git repo",
    ),
}

FAILURE_WORDS = r"different project|could(?: not|n't)|failed|no access|permission|error"

MODES = ("https", "again", "fail", "list", "relocate")


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
    for old in (SCRATCH_BRAIN, MOVED_BRAIN):
        if old.exists():
            remove_tree(old)
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


def run_owner(prompt: str, tag: str, brain: Path = SCRATCH_BRAIN) -> dict:
    """One owner turn through `claude -p`; returns the final result event and
    keeps the whole stream on disk as clone-events-<tag>.json for --verify."""
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
        cwd=str(brain),
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
    (SCRATCH_ROOT / f"clone-events-{tag}.json").write_text(
        json.dumps(events, indent=2), encoding="utf-8"
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {proc.returncode}): {proc.stderr.strip()[:2000]}"
        )
    final = next((e for e in reversed(events) if e.get("type") == "result"), {})
    print(f"[{tag}] cost=${final.get('total_cost_usd', 0):.4f}")
    print(f"[{tag}] result: {final.get('result', '')!r}"[:1500])
    return final


def load_events(tag: str) -> list[dict]:
    return json.loads(
        (SCRATCH_ROOT / f"clone-events-{tag}.json").read_text(encoding="utf-8")
    )


def reply_text(tag: str) -> str:
    """Every assistant text block of the turn, in order -- the final `result`
    field is only the last block."""
    blocks = []
    for e in load_events(tag):
        if e.get("type") != "assistant":
            continue
        content = e.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "text":
                blocks.append(block.get("text", ""))
    return "\n".join(blocks)


def bash_commands(tag: str) -> list[str]:
    cmds = []
    for e in load_events(tag):
        content = e.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") in ("Bash", "PowerShell")
            ):
                cmds.append(block.get("input", {}).get("command", ""))
    return cmds


def lead_paragraph(text: str) -> str:
    """The reply's first paragraph -- what the owner reads first -- with any
    cause it explicitly rules out ("not an access problem") taken away, since
    ruling a cause out is not naming it."""
    lead = text.strip().split("\n\n", 1)[0]
    return re.sub(
        r"\bnot an? (?:\w+ (?:or \w+ )?)?(?:access|network|address)(?: or \w+)? problem",
        "",
        lead,
        flags=re.IGNORECASE,
    )


def flat(text: str) -> str:
    return text.replace("\\\\", "/").replace("\\", "/").lower()


def names_path(reply: str, brain: Path = SCRATCH_BRAIN) -> bool:
    """The reply shows alpha's clone path -- relative to the brain, or absolute
    under THIS brain (so a moved brain naming its old home does not pass)."""
    f = flat(reply)
    absolute = flat(str(brain / "projects" / "sb-sandbox-alpha"))
    other_abs = re.findall(r"[a-z]:/[^\s`'\"|)]*projects/sb-sandbox-alpha", f)
    if any(a != absolute for a in other_abs):
        return False
    return "projects/sb-sandbox-alpha" in f


def project_folders(brain: Path = SCRATCH_BRAIN) -> list[str]:
    root = brain / "projects"
    return sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def do_run(mode: str) -> None:
    if mode == "https":
        projects = SCRATCH_BRAIN / "projects"
        if projects.exists():
            remove_tree(projects)
        run_owner(f"Take this project in: {ALPHA_HTTPS}", "https")
        return
    if not (ALPHA_CLONE / ".git").is_dir():
        raise SystemExit("run --mode https first: these modes use its clone")

    if mode == "again":
        (ALPHA_CLONE / MARKER).write_text("left by check_clone.py\n", encoding="utf-8")
        run_owner(f"Take this project in: {ALPHA_HTTPS}", "again-https")
        run_owner(f"Take this project in: {ALPHA_SSH}", "again-ssh")
    elif mode == "fail":
        for cause, (url, _) in FAILURES.items():
            run_owner(f"Take this project in: {url}", f"fail-{cause}")
    elif mode == "list":
        run_owner(
            "Which projects do you manage? Tell me where each one is and where it came from.",
            "list",
        )
    else:  # relocate
        if MOVED_BRAIN.exists():
            remove_tree(MOVED_BRAIN)
        shutil.copytree(SCRATCH_BRAIN, MOVED_BRAIN)
        run_owner(
            "Which projects do you manage? Tell me where each one is and where it came from.",
            "relocate-list",
            MOVED_BRAIN,
        )
        run_owner(f"Take this project in: {ALPHA_HTTPS}", "relocate-again", MOVED_BRAIN)


def do_verify(mode: str) -> int:
    results: list[tuple[str, bool, str]] = []

    if mode == "https":
        reply = reply_text("https")
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

        path_named = names_path(reply)
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

    elif mode == "again":
        marker_survived = (ALPHA_CLONE / MARKER).is_file()
        one_clone = project_folders() == ["sb-sandbox-alpha"]
        details = [f"marker_survived={marker_survived} projects={project_folders()}"]
        ok4 = marker_survived and one_clone
        for tag in ("again-https", "again-ssh"):
            reply = reply_text(tag)
            hand_clone = [
                c for c in bash_commands(tag) if re.search(r"\bgit\s+clone\b", c)
            ]
            said_already = bool(re.search(r"\balready\b", reply, re.IGNORECASE))
            reads_failed = bool(re.search(FAILURE_WORDS, reply, re.IGNORECASE))
            path_named = names_path(reply)
            ok = path_named and said_already and not reads_failed and not hand_clone
            ok4 = ok4 and ok
            details.append(
                f"{tag}: path_named={path_named} said_already={said_already} "
                f"reads_failed={reads_failed} hand_clone={len(hand_clone)}"
            )
        results.append(
            (
                "AC4: the same project is not cloned again; the owner is told where it is",
                ok4,
                " | ".join(details),
            )
        )

    elif mode == "fail":
        # The cause is judged on the reply's first paragraph -- what the owner
        # reads first -- not on the advice after it, which may well mention
        # another cause ("try the HTTPS URL"). See lead_paragraph.
        replies = {
            cause: lead_paragraph(reply_text(f"fail-{cause}")) for cause in FAILURES
        }
        folders = project_folders()
        no_partial = folders == ["sb-sandbox-alpha"]
        ok5 = no_partial
        details = [f"projects={folders}"]
        for cause, (_, own) in FAILURES.items():
            says_own = bool(re.search(own, replies[cause], re.IGNORECASE))
            says_other = [
                other
                for other, (_, pat) in FAILURES.items()
                if other != cause and re.search(pat, replies[cause], re.IGNORECASE)
            ]
            ok5 = ok5 and says_own and not says_other
            details.append(f"{cause}: own={says_own} also={says_other}")
        results.append(
            (
                "AC5: each failure has a distinct message and leaves no partial folder",
                ok5,
                " | ".join(details),
            )
        )

    elif mode == "list":
        reply = reply_text("list")
        path_named = names_path(reply)
        origin_named = "github.com/kaushikhazra/sb-sandbox-alpha" in flat(reply)
        results.append(
            (
                "AC6: the owner can list managed projects with path and origin",
                path_named and origin_named,
                f"path_named={path_named} origin_named={origin_named}",
            )
        )

    else:  # relocate
        listed = reply_text("relocate-list")
        again = reply_text("relocate-again")
        list_ok = names_path(listed, MOVED_BRAIN)
        again_ok = names_path(again, MOVED_BRAIN) and bool(
            re.search(r"\balready\b", again, re.IGNORECASE)
        )
        one_clone = project_folders(MOVED_BRAIN) == ["sb-sandbox-alpha"]
        marker = (MOVED_BRAIN / "projects" / "sb-sandbox-alpha" / MARKER).is_file()
        results.append(
            (
                "AC7: after the brain is moved, every managed project is still found",
                list_ok and again_ok and one_clone and marker,
                f"listed_at_new_path={list_ok} again_found_at_new_path={again_ok} "
                f"projects={project_folders(MOVED_BRAIN)} marker_survived={marker}",
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

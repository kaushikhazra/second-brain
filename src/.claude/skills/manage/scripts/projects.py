#!/usr/bin/env python3
"""The projects this brain manages -- take one in, list them, find one.

    python .claude/skills/manage/scripts/projects.py clone <git-url>
    python .claude/skills/manage/scripts/projects.py list
    python .claude/skills/manage/scripts/projects.py locate <name-or-url>
    python .claude/skills/manage/scripts/projects.py learn <name>
    python .claude/skills/manage/scripts/projects.py stale <name>
    python .claude/skills/manage/scripts/projects.py refresh <name>
    python .claude/skills/manage/scripts/projects.py trackers
    python .claude/skills/manage/scripts/projects.py tracker <name> [--set tracker=gitlab] [--clear]

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

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
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
    """The origin URL as configured -- not `git remote get-url`, which applies
    `url.<x>.insteadOf` rewrites and would report a mirror's path instead of
    the project's real address (found by #40's check)."""
    return git("config", "--get", "remote.origin.url", cwd=path).stdout.strip()


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


def find(key: str) -> Path | None:
    for p in managed():
        if p.name.lower() == key.lower() or normalise(origin_of(p)) == normalise(key):
            return p
    return None


def not_managed(key: str) -> int:
    print("STATUS: NOT_MANAGED")
    print(f"KEY: {key}")
    return 1


def cmd_locate(key: str) -> int:
    p = find(key)
    if p is None:
        return not_managed(key)
    print("STATUS: FOUND")
    print(f"PATH: {p}")
    print(f"ORIGIN: {origin_of(p)}")
    return 0


# ---- learned context (issue #39) -------------------------------------------
#
# What the brain learned about a project lives in `.claude/projects/<name>.md`
# in the brain -- never inside the project's own clone, never under projects/
# (every folder there is a project). Its frontmatter is a fingerprint the
# script writes itself, so `stale` can tell when CLAUDE.md changed upstream.

PROSE_SECTIONS = (
    "Purpose",
    "Development method",
    "Conventions",
    "Code and tests",
    "Project skills and rules (.claude/)",
)
TO_FILL = "_(to fill from the material `learn` printed)_"


def record_path(name: str) -> Path:
    return brain_root() / ".claude" / "projects" / f"{name}.md"


def blob(p: Path, rel: str | None, rev: str = "HEAD") -> str:
    if not rel:
        return "none"
    out = git("rev-parse", f"{rev}:{rel}", cwd=p)
    return out.stdout.strip() if out.returncode == 0 else "none"


def readme_of(p: Path) -> str | None:
    found = sorted(
        f.name
        for f in p.iterdir()
        if f.is_file() and f.name.lower().startswith("readme")
    )
    return found[0] if found else None


def hooks_of(p: Path) -> list[str]:
    """Every hook the project declares, as `event | matcher | command | file`."""
    lines = []
    for name in ("settings.json", "settings.local.json"):
        f = p / ".claude" / name
        if not f.is_file():
            continue
        try:
            hooks = json.loads(f.read_text(encoding="utf-8")).get("hooks", {})
        except (ValueError, OSError) as exc:
            lines.append(f"(could not read .claude/{name}: {exc})")
            continue
        for event, groups in hooks.items():
            for group in groups or []:
                for h in group.get("hooks", []):
                    lines.append(
                        f"{event} | {group.get('matcher', '*') or '*'} | "
                        f"{h.get('command', h.get('type', '?'))} | .claude/{name}"
                    )
    return lines


def read_text(f: Path) -> str:
    try:
        return f.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"(could not read: {exc})"


def frontmatter(record: Path) -> dict[str, str]:
    text = read_text(record)
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    pairs = (line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    return {k.strip(): v.strip() for k, v in pairs}


def cmd_learn(key: str) -> int:
    p = find(key)
    if p is None:
        return not_managed(key)
    readme = readme_of(p)
    has_claude_md = (p / "CLAUDE.md").is_file()
    hooks = hooks_of(p)
    record = record_path(p.name)
    record.parent.mkdir(parents=True, exist_ok=True)

    body = [
        "---",
        f"project: {p.name}",
        f"origin: {origin_of(p)}",
        f"learned_at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"commit: {git('rev-parse', 'HEAD', cwd=p).stdout.strip()}",
        f"claude_md: {blob(p, 'CLAUDE.md') if has_claude_md else 'none'}",
        f"readme: {blob(p, readme)}",
        "---",
        "",
        f"# {p.name} — learned context",
        "",
    ]
    if not has_claude_md:
        body += [
            "**No CLAUDE.md.** Learned from the README and the folder structure.",
            "",
        ]
    for section in PROSE_SECTIONS:
        body += [f"## {section}", "", TO_FILL, ""]
    body += ["## Hooks — listed, not adopted", ""]
    body += [f"- {h}" for h in hooks] or ["- none"]
    record.write_text("\n".join(body) + "\n", encoding="utf-8")

    print("STATUS: LEARN_MATERIAL")
    print(f"PROJECT: {p.name}")
    print(f"PATH: {p}")
    print(f"RECORD: {record}")
    print(f"HAS_CLAUDE_MD: {'yes' if has_claude_md else 'no'}")
    print(f"HOOKS: {len(hooks)}")
    print("\n=== CLAUDE.md ===")
    print(read_text(p / "CLAUDE.md") if has_claude_md else "(none)")
    print(f"\n=== {readme or 'README'} ===")
    print(read_text(p / readme) if readme else "(none)")
    print("\n=== .claude/ ===")
    claude_dir = p / ".claude"
    files = (
        sorted(f for f in claude_dir.rglob("*") if f.is_file())
        if claude_dir.is_dir()
        else []
    )
    for f in files:
        print(f.relative_to(p).as_posix())
    if not files:
        print("(none)")
    for f in files:
        if f.suffix.lower() == ".md":  # skills and rules are markdown
            print(f"\n--- {f.relative_to(p).as_posix()} ---")
            print(read_text(f))
    print("\n=== hooks ===")
    print("\n".join(hooks) or "(none)")
    print("\n=== top level ===")
    for f in sorted(p.iterdir()):
        if f.name != ".git":
            print(f.name + ("/" if f.is_dir() else ""))
    print("\n=== code host and issue tracker ===")
    settings = load_settings(p.name)
    settings["detected"] = detect(p)
    save_settings(p.name, settings)
    print_tracker(p, settings)
    return 0


# ---- code host and issue tracker (issue #40) --------------------------------
#
# What was detected, what the owner overrode, and which credential notices were
# already given live in `.claude/projects/<name>.json` beside the learned record.
# `learn` rewrites only `detected`; an override survives every relearn and every
# restart. Nothing here contacts a tracker's API -- detection reads the remote
# URL and the project's own files; the credential check is local.

SUPPORTED = ("github", "gitlab")
DISPLAY = {"github": "GitHub", "gitlab": "GitLab"}

NEEDS = {
    "github": "the GitHub CLI signed in (`gh auth login`), or a GITHUB_TOKEN environment variable",
    "gitlab": "the GitLab CLI signed in (`glab auth login`), or a GITLAB_TOKEN environment variable",
}


def settings_path(name: str) -> Path:
    return brain_root() / ".claude" / "projects" / f"{name}.json"


def load_settings(name: str) -> dict:
    f = settings_path(name)
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    except (ValueError, OSError):
        return {}


def save_settings(name: str, settings: dict) -> None:
    f = settings_path(name)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def tracker_of_host(host: str) -> str:
    if host == "github.com" or host.startswith("github."):
        return "github"
    if "gitlab" in host:
        return "gitlab"
    return host.split(".")[-2] if host.count(".") >= 1 else host or "unknown"


def detect(p: Path) -> dict:
    """Code host from the remote URL; tracker from the project's own files if
    they name one, else the code host's own tracker."""
    origin = origin_of(p)
    host = normalise(origin).split("/", 1)[0] if origin else "unknown"
    code_host = tracker_of_host(host)
    evidence = [f"remote URL {origin} (host {host})"]
    tracker, tracker_evidence = code_host, f"the code host's own issues ({host})"
    if (p / ".gitlab-ci.yml").is_file():
        evidence.append(".gitlab-ci.yml in the project")
    if (p / ".github").is_dir():
        evidence.append(".github/ in the project")
    for doc in ("CLAUDE.md", readme_of(p) or ""):
        text = read_text(p / doc) if doc and (p / doc).is_file() else ""
        jira = re.search(r"https?://[\w.-]*atlassian\.net/\S*|\bjira\b", text, re.I)
        if jira:
            tracker, tracker_evidence = "jira", f"{doc} names Jira ({jira.group(0)})"
            break
    return {
        "code_host": code_host,
        "tracker": tracker,
        "how": "; ".join(evidence) + f"; tracker from {tracker_evidence}",
    }


def credentials(tracker: str) -> bool:
    """Local check only -- never a network call to a tracker."""
    if tracker == "github":
        if os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"):
            return True
        try:
            return (
                subprocess.run(
                    ["gh", "auth", "status"], capture_output=True, timeout=30
                ).returncode
                == 0
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
    if tracker == "gitlab":
        if os.environ.get("GITLAB_TOKEN"):
            return True
        home = Path.home()
        return any(
            (d / "glab-cli" / "config.yml").is_file()
            for d in (home / ".config", Path(os.environ.get("APPDATA", home)))
        )
    return False


def effective(settings: dict) -> tuple[str, str, str]:
    detected = settings.get("detected", {})
    override = settings.get("override", {})
    code_host = override.get("code_host") or detected.get("code_host", "unknown")
    tracker = override.get("tracker") or detected.get("tracker", "unknown")
    source = []
    for field, value in (("code_host", code_host), ("tracker", tracker)):
        source.append(
            f"{field}: {'set by the owner' if field in override else 'detected'}"
        )
    return code_host, tracker, "; ".join(source)


def print_tracker(p: Path, settings: dict) -> None:
    code_host, tracker, source = effective(settings)
    supported = tracker in SUPPORTED
    print(f"CODE_HOST: {code_host}")
    print(f"TRACKER: {tracker}")
    print(f"SOURCE: {source}")
    print(
        f"HOW_DETECTED: {settings.get('detected', {}).get('how', '(not detected yet)')}"
    )
    print(f"SUPPORTED: {'yes' if supported else 'no'}")
    if not supported:
        print(
            "ISSUE_WORK: unavailable -- the project is still managed, but monitoring and issue work are not available for this tracker"
        )
        return
    if credentials(tracker):
        print("CREDENTIALS: present")
        return
    told = settings.setdefault("credentials_told", [])
    print("CREDENTIALS: missing")
    print(f"NEEDED: {NEEDS[tracker]}")
    print(
        f"TELL_OWNER: {'no -- already told' if tracker in told else 'yes -- first time'}"
    )
    if tracker not in told:
        told.append(tracker)
        save_settings(p.name, settings)


def cmd_trackers() -> int:
    print("STATUS: TRACKERS")
    print(f"SUPPORTED: {', '.join(DISPLAY[t] for t in SUPPORTED)}")
    return 0


def cmd_tracker(key: str, sets: list[str]) -> int:
    """Show the project's code host and tracker; `--set field=value` overrides,
    `--clear` returns to what was detected."""
    p = find(key)
    if p is None:
        return not_managed(key)
    settings = load_settings(p.name)
    if not settings.get("detected"):
        settings["detected"] = detect(p)
    for item in sets:
        if item == "--clear":
            settings.pop("override", None)
            continue
        field, _, value = item.partition("=")
        if field not in ("code_host", "tracker") or not value:
            print("STATUS: BAD_OVERRIDE")
            print(f"DETAIL: expected code_host=<name> or tracker=<name>, got {item!r}")
            return 1
        settings.setdefault("override", {})[field] = value.strip().lower()
    save_settings(p.name, settings)
    print("STATUS: TRACKER")
    print(f"PROJECT: {p.name}")
    print_tracker(p, settings)
    return 0


def cmd_stale(key: str) -> int:
    """CURRENT or STALE: does the record's CLAUDE.md match the one upstream?"""
    p = find(key)
    if p is None:
        return not_managed(key)
    record = record_path(p.name)
    if not record.is_file():
        print("STATUS: NO_RECORD")
        print(f"PROJECT: {p.name}")
        return 0
    fetched = git("fetch", "--quiet", "origin", cwd=p, timeout=300)
    if fetched.returncode != 0:
        return fail(classify(fetched.stderr), origin_of(p), fetched.stderr)
    learned = frontmatter(record).get("claude_md", "")
    upstream = blob(p, "CLAUDE.md", "origin/HEAD")
    print(f"STATUS: {'CURRENT' if learned == upstream else 'STALE'}")
    print(f"PROJECT: {p.name}")
    print(f"LEARNED_CLAUDE_MD: {learned}")
    print(f"UPSTREAM_CLAUDE_MD: {upstream}")
    return 0


def cmd_refresh(key: str) -> int:
    """Fast-forward the clone to upstream, refusing to touch local work."""
    p = find(key)
    if p is None:
        return not_managed(key)
    pulled = git("pull", "--ff-only", "--quiet", cwd=p, timeout=600)
    if pulled.returncode != 0:
        print("STATUS: REFRESH_FAILED")
        print(f"PROJECT: {p.name}")
        lines = [l for l in pulled.stderr.strip().splitlines() if l.strip()]
        print(f"DETAIL: {lines[0] if lines else '(git said nothing)'}")
        return 1
    print("STATUS: REFRESHED")
    print(f"PROJECT: {p.name}")
    print(f"COMMIT: {git('rev-parse', 'HEAD', cwd=p).stdout.strip()}")
    return 0


def main(argv: list[str]) -> int:
    # Project files are UTF-8; a Windows console code page would garble them in
    # the material `learn` prints (an em dash came out as "?" before this).
    sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) >= 2 and argv[0] == "clone":
        return cmd_clone(argv[1])
    if argv[:1] == ["list"]:
        return cmd_list()
    if len(argv) >= 2 and argv[0] == "locate":
        return cmd_locate(argv[1])
    if argv[:1] == ["trackers"]:
        return cmd_trackers()
    if len(argv) >= 2 and argv[0] == "tracker":
        sets = [a for a in argv[2:] if a != "--set"]
        return cmd_tracker(argv[1], sets)
    commands = {"learn": cmd_learn, "stale": cmd_stale, "refresh": cmd_refresh}
    if len(argv) >= 2 and argv[0] in commands:
        return commands[argv[0]](argv[1])
    print(
        "usage: projects.py clone <git-url> | list | locate <name-or-url>"
        " | learn <name> | stale <name> | refresh <name>"
        " | trackers | tracker <name> [--set field=value ...] [--clear]",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

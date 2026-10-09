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
    python .claude/skills/manage/scripts/projects.py monitor <name> on|off
    python .claude/skills/manage/scripts/projects.py monitored
    python .claude/skills/manage/scripts/projects.py issues
    python .claude/skills/manage/scripts/projects.py issue <name> <n>
    python .claude/skills/manage/scripts/projects.py decide <name> <n> yes|no|later

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


def hook_entries(p: Path) -> tuple[list[dict], list[str]]:
    """Every hook the project declares, as dicts (event, matcher, command, file,
    hook = the whole entry), plus a note for each settings file that could not be read."""
    entries, notes = [], []
    for name in ("settings.json", "settings.local.json"):
        f = p / ".claude" / name
        if not f.is_file():
            continue
        try:
            hooks = json.loads(f.read_text(encoding="utf-8")).get("hooks", {})
        except (ValueError, OSError) as exc:
            notes.append(f"(could not read .claude/{name}: {exc})")
            continue
        for event, groups in hooks.items():
            for group in groups or []:
                for h in group.get("hooks", []):
                    entries.append(
                        {
                            "event": event,
                            "matcher": group.get("matcher", "*") or "*",
                            "command": h.get("command", h.get("type", "?")),
                            "file": f".claude/{name}",
                            "hook": h,
                        }
                    )
    return entries, notes


def hooks_of(p: Path) -> list[str]:
    """Every hook the project declares, as `event | matcher | command | file`."""
    entries, notes = hook_entries(p)
    return notes + [
        f"{e['event']} | {e['matcher']} | {e['command']} | {e['file']}" for e in entries
    ]


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


# ---- monitoring (issue #41) -------------------------------------------------
#
# A project is watched only when the owner switched monitoring on for it. The
# heartbeat runs `issues` each beat: it reads the open issues of monitored
# projects only, from each project's own tracker, and compares them with what
# was already seen. All of it lives in `.claude/projects/<name>.json`:
#   monitor        true/false -- the owner's choice
#   seen_issues    {number: title} -- reported once, never again while open
#   issues_failure the failure already told to the owner (cleared on recovery)


def repo_slug(p: Path) -> str:
    """`owner/name` (or `group/sub/name`) from the configured origin."""
    return normalise(origin_of(p)).split("/", 1)[1] if origin_of(p) else ""


def open_issues(p: Path, tracker: str) -> tuple[dict[str, str] | None, str]:
    """({number: title}, "") or (None, failure code). GitHub through `gh`,
    GitLab through `glab` -- each project's own tracker, never another's."""
    if not credentials(tracker):
        return None, "NOT_SIGNED_IN"
    slug = repo_slug(p)
    if tracker == "github":
        args = [
            "gh",
            "issue",
            "list",
            "-R",
            slug,
            "--state",
            "open",
            "--json",
            "number,title",
            "--limit",
            "500",
        ]
    else:
        args = [
            "glab",
            "issue",
            "list",
            "-R",
            slug,
            "--output",
            "json",
            "--per-page",
            "100",
        ]
    try:
        out = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"UNREACHABLE ({exc.__class__.__name__})"
    if out.returncode != 0:
        err = out.stderr.lower()
        if any(w in err for w in ("auth", "login", "401", "403", "token")):
            return None, "NOT_SIGNED_IN"
        return None, "UNREACHABLE"
    try:
        items = json.loads(out.stdout or "[]")
    except ValueError:
        return None, "UNREACHABLE"
    key = "number" if tracker == "github" else "iid"
    return {str(i[key]): i.get("title", "") for i in items}, ""


def cmd_monitor(key: str, state: str) -> int:
    p = find(key)
    if p is None:
        return not_managed(key)
    settings = load_settings(p.name)
    if not settings.get("detected"):
        settings["detected"] = detect(p)
    _, tracker, _ = effective(settings)
    if state == "on" and tracker not in SUPPORTED:
        print("STATUS: MONITOR_UNAVAILABLE")
        print(f"PROJECT: {p.name}")
        print(f"TRACKER: {tracker}")
        return 1
    settings["monitor"] = state == "on"
    save_settings(p.name, settings)
    print(f"STATUS: MONITOR_{state.upper()}")
    print(f"PROJECT: {p.name}")
    print(f"TRACKER: {tracker}")
    return 0


def cmd_monitored() -> int:
    rows = []
    for p in managed():
        settings = load_settings(p.name)
        rows.append((p.name, bool(settings.get("monitor")), effective(settings)[1]))
    print("STATUS: MONITORED")
    print(f"COUNT: {sum(1 for _, on, _ in rows if on)}")
    for name, on, tracker in rows:
        print(
            f"PROJECT: {name} | MONITOR: {'on' if on else 'off'} | TRACKER: {tracker}"
        )
    return 0


def cmd_issues() -> int:
    """One beat: report each open issue of a monitored project once; drop the
    ones that closed; tell each tracker failure once, until it recovers."""
    print("STATUS: ISSUES")
    for p in managed():
        settings = load_settings(p.name)
        if not settings.get("monitor"):
            continue  # monitored projects only -- nothing is fetched otherwise
        _, tracker, _ = effective(settings)
        current, failure = open_issues(p, tracker)
        if current is None:
            told = settings.get("issues_failure") == failure
            print(
                f"FAILURE: {p.name} | {failure} | TELL_OWNER: {'no -- already told' if told else 'yes -- first time'}"
            )
            if failure == "NOT_SIGNED_IN" and tracker in NEEDS:
                print(f"NEEDED: {NEEDS[tracker]}")
            if not told:
                settings["issues_failure"] = failure
                save_settings(p.name, settings)
            continue
        if settings.pop("issues_failure", None):
            print(f"RECOVERED: {p.name}")
        seen = settings.get("seen_issues", {})
        for number in sorted(set(current) - set(seen), key=int):
            print(f"NEW: {p.name} | #{number} | {current[number]}")
        for number in sorted(set(seen) - set(current), key=int):
            print(f"CLOSED: {p.name} | #{number} | {seen[number]} (dropped from seen)")
        settings["seen_issues"] = {n: current[n] for n in sorted(current, key=int)}
        save_settings(p.name, settings)
    return 0


# ---- due diligence (issue #42) ----------------------------------------------
#
# Before any work on an issue, the brain walks the owner through it and waits
# for a yes. The answer is recorded in `.claude/projects/<name>.json` under
# `decisions` against the issue's `updated_at`, so a no or a later stands until
# the issue itself changes.


def fetch_issue(p: Path, tracker: str, number: str) -> tuple[dict | None, str]:
    if tracker not in SUPPORTED:
        return None, "UNSUPPORTED"
    if not credentials(tracker):
        return None, "NOT_SIGNED_IN"
    slug = repo_slug(p)
    if tracker == "github":
        args = [
            "gh",
            "issue",
            "view",
            number,
            "-R",
            slug,
            "--json",
            "number,title,body,state,updatedAt,labels,comments,url",
        ]
    else:
        args = ["glab", "issue", "view", number, "-R", slug, "--output", "json"]
    try:
        out = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, "UNREACHABLE"
    if out.returncode != 0:
        return None, "NOT_FOUND" if "not found" in out.stderr.lower() else "UNREACHABLE"
    try:
        data = json.loads(out.stdout)
    except ValueError:
        return None, "UNREACHABLE"
    return {
        "number": str(data.get("number", data.get("iid", number))),
        "title": data.get("title", ""),
        "body": data.get("body", data.get("description", "")) or "",
        "state": str(data.get("state", "")).lower(),
        "updated_at": data.get("updatedAt", data.get("updated_at", "")),
        "comments": len(data.get("comments", []) or []),
        "url": data.get("url", data.get("web_url", "")),
    }, ""


def has_criteria(body: str) -> bool:
    """Checkable criteria: an acceptance-criteria heading with numbered or
    checkbox items under it, or at least two numbered items anywhere."""
    heading = re.search(
        r"^#+\s*acceptance criteria|^\*\*acceptance criteria\*\*", body, re.I | re.M
    )
    items = re.findall(r"^\s*(?:\d+\.|- \[[ x]\])\s+\S", body, re.M)
    return bool(heading and items) or len(items) >= 2


def cmd_issue(key: str, number: str) -> int:
    p = find(key)
    if p is None:
        return not_managed(key)
    settings = load_settings(p.name)
    _, tracker, _ = effective(settings)
    issue, failure = fetch_issue(p, tracker, number.lstrip("#"))
    if issue is None:
        print("STATUS: ISSUE_UNAVAILABLE")
        print(f"PROJECT: {p.name}")
        print(f"CAUSE: {failure}")
        return 1
    prior = settings.get("decisions", {}).get(issue["number"])
    changed = bool(prior) and prior.get("updated_at") != issue["updated_at"]
    print("STATUS: ISSUE")
    print(f"PROJECT: {p.name}")
    print(f"NUMBER: {issue['number']}")
    print(f"TITLE: {issue['title']}")
    print(f"STATE: {issue['state']}")
    print(f"UPDATED_AT: {issue['updated_at']}")
    print(f"URL: {issue['url']}")
    print(f"COMMENTS: {issue['comments']}")
    print(f"CHECKABLE_CRITERIA: {'yes' if has_criteria(issue['body']) else 'no'}")
    if prior:
        print(
            f"PRIOR_DECISION: {prior['answer']} (recorded {prior.get('recorded_at', '?')})"
        )
        print(f"CHANGED_SINCE: {'yes' if changed else 'no'}")
    else:
        print("PRIOR_DECISION: none")
    print("\n=== body ===")
    print(issue["body"] or "(empty)")
    return 0


def cmd_decide(key: str, number: str, answer: str) -> int:
    p = find(key)
    if p is None:
        return not_managed(key)
    settings = load_settings(p.name)
    _, tracker, _ = effective(settings)
    issue, failure = fetch_issue(p, tracker, number.lstrip("#"))
    if issue is None:
        print("STATUS: ISSUE_UNAVAILABLE")
        print(f"CAUSE: {failure}")
        return 1
    settings.setdefault("decisions", {})[issue["number"]] = {
        "answer": answer,
        "updated_at": issue["updated_at"],
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    save_settings(p.name, settings)
    print("STATUS: DECIDED")
    print(f"PROJECT: {p.name}")
    print(f"NUMBER: {issue['number']}")
    print(f"ANSWER: {answer}")
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
    if len(argv) >= 3 and argv[0] == "issue":
        return cmd_issue(argv[1], argv[2])
    if len(argv) >= 4 and argv[0] == "decide" and argv[3] in ("yes", "no", "later"):
        return cmd_decide(argv[1], argv[2], argv[3])
    if argv[:1] == ["monitored"]:
        return cmd_monitored()
    if argv[:1] == ["issues"]:
        return cmd_issues()
    if len(argv) >= 3 and argv[0] == "monitor" and argv[2] in ("on", "off"):
        return cmd_monitor(argv[1], argv[2])
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
        " | trackers | tracker <name> [--set field=value ...] [--clear]"
        " | monitor <name> on|off | monitored | issues"
        " | issue <name> <n> | decide <name> <n> yes|no|later",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

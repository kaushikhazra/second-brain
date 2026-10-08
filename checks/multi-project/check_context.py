#!/usr/bin/env python3
"""Issue #39 -- the brain learns a managed project's CLAUDE.md and context.

Drives a scratch brain built from `src/` through the owner's door (`claude -p`):
the project is taken in with #38's capability in one session, and asked about in
a fresh one -- what the brain knows must outlive the session that learned it.

  --mode takein : AC 1 -- after the take-in session, the learned record
                  `.claude/projects/sb-sandbox-alpha.md` exists, its fingerprint
                  matches the clone, every prose section is filled, and it holds
                  what only CLAUDE.md (method, conventions), README (purpose) and
                  .claude/ (the session hook) say.
  --mode know   : AC 2 -- in a fresh session, "what do you know about
                  sb-sandbox-alpha?" gets its purpose, development method,
                  conventions, and where code and tests live -- AND a fact
                  planted only in the learned record, so an answer looked up
                  from the project's files on the spot does not pass.

Usage:
    python check_context.py --build
    python check_context.py --run --mode takein
    python check_context.py --verify --mode takein

Scratch lives under C:/Projects/.tmp/second-brain-loop-39/. Test projects are the
two private sandboxes only. Costs real money on --run.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import scratch_brain as sb

SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-39")
BRAIN = SCRATCH_ROOT / "brain"

ALPHA = BRAIN / "projects" / "sb-sandbox-alpha"
RECORD = BRAIN / ".claude" / "projects" / "sb-sandbox-alpha.md"

# A fact planted in the learned record only -- nowhere in the clone, nowhere
# upstream. An answer that carries it came from what the brain learned; one
# that re-reads the project's files cannot know it.
PLANTED = "Codename: Juniper Kestrel."

MODES = ("takein", "know")


def events(tag: str) -> Path:
    return SCRATCH_ROOT / f"context-events-{tag}.json"


def frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    if not m:
        return {}
    pairs = (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
    return {k.strip(): v.strip() for k, v in pairs}


def section(text: str, heading: str) -> str:
    m = re.search(
        rf"^##\s+{re.escape(heading)}.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S
    )
    return m.group(1).strip() if m else ""


def do_run(mode: str) -> None:
    if mode == "takein":
        for old in (BRAIN / "projects", BRAIN / ".claude" / "projects"):
            if old.exists():
                sb.remove_tree(old)
        sb.run_owner(f"Take this project in: {sb.ALPHA_HTTPS}", events("takein"), BRAIN)
        return
    # know: uses --mode takein's clone and record
    if not RECORD.is_file():
        raise SystemExit("run --mode takein first: no learned record to ask about")
    text = RECORD.read_text(encoding="utf-8")
    if PLANTED not in text:
        text = re.sub(
            r"(^##\s+Purpose.*?$)", rf"\1\n\n{PLANTED}", text, count=1, flags=re.M
        )
        RECORD.write_text(text, encoding="utf-8")
    sb.run_owner("What do you know about sb-sandbox-alpha?", events("know-ask"), BRAIN)


def do_verify(mode: str) -> int:
    results: list[tuple[str, bool, str]] = []

    if mode == "takein":
        exists = RECORD.is_file()
        text = RECORD.read_text(encoding="utf-8") if exists else ""
        fm = frontmatter(text)
        head = sb.git("rev-parse", "HEAD", cwd=ALPHA).stdout.strip()
        claude_blob = sb.git("rev-parse", "HEAD:CLAUDE.md", cwd=ALPHA).stdout.strip()
        fingerprint = fm.get("commit") == head and fm.get("claude_md") == claude_blob
        unfilled = "(to fill" in text
        method = sb.has(r"spec", section(text, "Development method"))
        conventions = sb.has(r"3\.11|standard library", section(text, "Conventions"))
        readme = sb.has(r"greet", section(text, "Purpose"))
        claude_dir = sb.has(
            r"mark_session|settings\.json|hook", section(text, "Project skills")
        )
        hook = "mark_session" in section(text, "Hooks")
        ok1 = (
            exists
            and fingerprint
            and not unfilled
            and method
            and conventions
            and readme
            and claude_dir
            and hook
        )
        results.append(
            (
                "AC1: on take-in the brain reads CLAUDE.md, .claude/ and README into its record",
                ok1,
                f"record={exists} fingerprint_matches_clone={fingerprint} unfilled={unfilled} "
                f"method(CLAUDE.md)={method} conventions(CLAUDE.md)={conventions} "
                f"purpose(README)={readme} .claude/={claude_dir} hook_listed={hook}",
            )
        )

    elif mode == "know":
        reply = sb.reply_text(events("know-ask"))
        f = sb.flat(reply)
        purpose = sb.has(r"\bgreet", reply)
        method = sb.has(r"spec[- ]driven|requirement\.md|spec (?:comes )?first", reply)
        conventions = [
            sb.has(r"standard library|stdlib", reply),
            sb.has(r"3\.11", reply),
            sb.has(r"small|named for what they return", reply),
        ]
        code_at = "src/" in f or sb.has(r"\bsrc\b", reply)
        tests_at = "tests/" in f or sb.has(r"\btests\b.{0,40}unittest|unittest", reply)
        learned = sb.has(r"juniper\W+kestrel", reply)
        ok2 = (
            purpose
            and method
            and sum(conventions) >= 2
            and code_at
            and tests_at
            and learned
        )
        # Informational, not graded: did the asking session open the project's
        # own files, or answer from what was learned at take-in?
        reads = [
            u.get("file_path", "") or u.get("command", "")
            for u in sb.tool_uses(events("know-ask"), "Read", "Bash", "PowerShell")
        ]
        read_project = [r for r in reads if "sb-sandbox-alpha" in sb.flat(r)]
        results.append(
            (
                "AC2: 'what do you know about <project>' gives purpose, method, conventions, code+tests",
                ok2,
                f"purpose={purpose} method={method} conventions={conventions} "
                f"code_at={code_at} tests_at={tests_at} from_record(planted)={learned} "
                f"| asked-session reads of the project: {len(read_project)}",
            )
        )

    return sb.report(results)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--mode", choices=MODES, default="takein")
    args = ap.parse_args()

    if args.build:
        SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
        sb.build(BRAIN)
        print(f"scratch brain built at {BRAIN}")
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

#!/usr/bin/env python3
"""Issue #7, cycle 1 -- activation-mechanism and structural checks for
`.claude/skills/news/`.

Mirrors `.claude/skills/curiosity/check_curiosity.py`'s shape exactly for the
activation half (issue #7's AC 1-6 are, criterion for criterion, the same
shape as issue #6's AC 1-6, just for the `news` habit) -- drives
`.claude/shared/activation.py` directly (mechanism tier) against a scratch
brain root, plus a real two-process restart for AC 5.

The structural half checks what `SKILL.md` and `youtube_subs.py` actually say,
not what a live run does: the format/verify-link/quiet-day/keyword-file/
YouTube-keys/keep rules are all stated in `SKILL.md`; the script has no RSS
URL anywhere; `news-keywords.txt` exists at the brain root and is named in the
skill.

The list-producing behaviour itself (AC 7-19) needs a live scripted-agent run
with real network access -- cycle 2's work, once cycle 1's mechanism is
trusted. Not attempted here.

Usage: python check_news.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ACTIVATION_PY = REPO_ROOT / ".claude" / "shared" / "activation.py"
SKILL_MD = REPO_ROOT / ".claude" / "skills" / "news" / "SKILL.md"
SESSION_START_MD = REPO_ROOT / ".claude" / "skills" / "session-start" / "SKILL.md"
YOUTUBE_SUBS_PY = (
    REPO_ROOT / ".claude" / "skills" / "news" / "scripts" / "youtube_subs.py"
)
KEYWORDS_FILE = REPO_ROOT / "news-keywords.txt"
GITIGNORE = REPO_ROOT / ".gitignore"

SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-7")
SCRATCH_BRAIN = SCRATCH_ROOT / "brain"

sys.path.insert(0, str(ACTIVATION_PY.parent))


def build_scratch_brain() -> Path:
    # Clean only this script's own subtree -- never the shared loop-7 root
    # (issue #6 cycle 2 found this the hard way in check_curiosity.py).
    if SCRATCH_BRAIN.exists():
        shutil.rmtree(SCRATCH_BRAIN)
    SCRATCH_BRAIN.mkdir(parents=True)
    (SCRATCH_BRAIN / ".claude").mkdir()
    (SCRATCH_BRAIN / "CLAUDE.md").write_text("# scratch brain\n", encoding="utf-8")
    return SCRATCH_BRAIN


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    if not ACTIVATION_PY.is_file():
        print(f"[FAIL] activation.py not found at {ACTIVATION_PY}")
        return 1
    if not SKILL_MD.is_file():
        print(f"[FAIL] news SKILL.md not found at {SKILL_MD}")
        return 1
    if not YOUTUBE_SUBS_PY.is_file():
        print(f"[FAIL] youtube_subs.py not found at {YOUTUBE_SUBS_PY}")
        return 1

    import activation as act  # noqa: E402

    skill_text = SKILL_MD.read_text(encoding="utf-8")
    youtube_text = YOUTUBE_SUBS_PY.read_text(encoding="utf-8")
    session_start_text = SESSION_START_MD.read_text(encoding="utf-8")

    scratch_brain = build_scratch_brain()
    path = scratch_brain / ".claude" / "activations.json"

    # --- AC 1: fresh record -> needs asking. ---
    fresh = act.load_record(path)
    ok1 = act.needs_ask(fresh, "news", "0.3.1")
    results.append(("AC1: a fresh record needs asking (news)", ok1, f"needs_ask={ok1}"))

    # --- AC 2: a yes is recorded, news runs once a day from then on (active). ---
    r = act.set_answer(fresh, "news", "0.3.1", active=True)
    ok2 = act.is_active(r, "news") and not act.needs_ask(r, "news", "0.3.1")
    results.append(
        (
            "AC2: a yes is recorded, active from that session on (news)",
            ok2,
            f"is_active={act.is_active(r, 'news')} needs_ask={act.needs_ask(r, 'news', '0.3.1')}",
        )
    )

    # --- AC 3: a no/no-answer is recorded, one-line hint given, no re-ask until
    # VERSION changes. ---
    r_no = act.set_answer(fresh, "news", "0.3.1", active=False)
    same_version_no_reask = not act.needs_ask(r_no, "news", "0.3.1")
    next_version_reasks = act.needs_ask(r_no, "news", "0.4.0")
    ok3 = (
        same_version_no_reask
        and next_version_reasks
        and not act.is_active(r_no, "news")
    )
    hint_in_session_start = "/news on" in session_start_text
    hint_in_skill = "/news on" in skill_text
    ok3 = ok3 and hint_in_session_start and hint_in_skill
    results.append(
        (
            "AC3: a no/no-answer is recorded, one-line hint given, no re-ask until VERSION changes (news)",
            ok3,
            f"same_version_no_reask={same_version_no_reask} next_version_reasks={next_version_reasks} "
            f"hint_in_session_start={hint_in_session_start} hint_in_skill={hint_in_skill}",
        )
    )

    # --- AC 4: /news on|off|status work at any time and say what state resulted. ---
    on_record = act.set_answer({}, "news", "0.3.1", active=True)
    off_record = act.set_answer(on_record, "news", "0.3.1", active=False)
    on_off_roundtrip_ok = act.is_active(on_record, "news") and not act.is_active(
        off_record, "news"
    )
    says_on = "News is on." in skill_text
    says_off = "News is off." in skill_text
    says_status = bool(
        re.search(
            r"status.{0,200}(active|inactive)", skill_text, re.IGNORECASE | re.DOTALL
        )
    )
    ok4 = on_off_roundtrip_ok and says_on and says_off and says_status
    results.append(
        (
            "AC4: /news on|off|status work at any time and say what resulted",
            ok4,
            f"roundtrip_ok={on_off_roundtrip_ok} says_on={says_on} says_off={says_off} says_status={says_status}",
        )
    )

    # --- AC 5: the recorded answer survives a restart and is git-ignored. Real
    # process boundary: one subprocess writes, a SEPARATE one reads back. ---
    write_script = (
        "import sys; sys.path.insert(0, %r); import activation as act; "
        "r = act.set_answer(act.load_record(act.Path(%r)), 'news', '0.3.1', active=True); "
        "act.save_record(act.Path(%r), r)"
    ) % (str(ACTIVATION_PY.parent), str(path), str(path))
    p_write = subprocess.run(
        [sys.executable, "-c", write_script], capture_output=True, text=True, timeout=15
    )
    read_script = (
        "import sys, json; sys.path.insert(0, %r); import activation as act; "
        "r = act.load_record(act.Path(%r)); print(json.dumps(r))"
    ) % (str(ACTIVATION_PY.parent), str(path))
    p_read = subprocess.run(
        [sys.executable, "-c", read_script], capture_output=True, text=True, timeout=15
    )
    restart_ok = p_write.returncode == 0 and p_read.returncode == 0
    try:
        restarted_record = json.loads(p_read.stdout.strip())
    except json.JSONDecodeError:
        restarted_record = {}
    restart_ok = restart_ok and restarted_record.get("news", {}).get("active") is True
    gitignore_text = GITIGNORE.read_text(encoding="utf-8")
    gitignored = ".claude/activations.json" in gitignore_text
    ok5 = restart_ok and gitignored
    results.append(
        (
            "AC5: the recorded answer survives a restart and is git-ignored (news)",
            ok5,
            f"restart_ok={restart_ok} gitignored={gitignored} p_write.rc={p_write.returncode} p_read.rc={p_read.returncode}",
        )
    )

    # --- AC 6 (structural half): with news off, nothing is printed, fetched or
    # scheduled -- session-start's daily-habits step skips the habit entirely
    # when inactive. Behavioral half is a later cycle's headless run. ---
    daily_habits_gates = bool(
        re.search(
            r"is_active.{0,200}false.{0,80}skip",
            session_start_text,
            re.IGNORECASE | re.DOTALL,
        )
    )
    skill_states_off_rule = bool(
        re.search(
            r"nothing\s+about\s+news\s+is\s+printed,\s+fetched\s+or\s+scheduled",
            skill_text,
        )
    )
    ok6_structural = daily_habits_gates and skill_states_off_rule
    results.append(
        (
            "AC6 (structural half): off-gate text routes to nothing; behavioral half pending a headless run",
            ok6_structural,
            f"daily_habits_gates={daily_habits_gates} skill_states_off_rule={skill_states_off_rule}",
        )
    )

    # --- Structural: the skill states each list-production rule. ---
    def stated(pattern: str, flags=re.IGNORECASE | re.DOTALL) -> bool:
        return bool(re.search(pattern, skill_text, flags))

    ac7 = stated(r"no summary.{0,80}no comment.{0,80}no category") or stated(
        r"nothing else.{0,300}no summary"
    )
    ac8 = stated(r"verify every link")
    ac9 = stated(r"no fixed length") and stated(r"quiet day")
    ac12 = "news-keywords.txt" in skill_text
    ac14 = stated(r"YouTube") and stated(r"not configured")
    ac16_17 = stated(r"newest date first") and stated(
        r"no checkbox, no status, and no due date"
    )
    ac18 = stated(r"no network")
    ac13 = stated(r"search\w*.{0,20}live") and stated(r"no cache")
    for name, ok in (
        ("AC7: format rule stated (bold headline + link, nothing else)", ac7),
        ("AC8: verify-every-link rule stated", ac8),
        ("AC9: no fixed length / quiet-day rule stated", ac9),
        ("AC12: keyword file named as the only knob", ac12),
        ("AC13: searched live, no cache, rule stated", ac13),
        ("AC14: YouTube-needs-keys / not-configured rule stated", ac14),
        (
            "AC16/AC17: keep rule -- newest date first, no checkbox/status/due-date",
            ac16_17,
        ),
        ("AC18: no-network rule stated", ac18),
    ):
        results.append((name, ok, "found" if ok else "not found in SKILL.md"))

    # --- AC 11 (structural half): the daily-habits step in session-start
    # actually gates on ran_today, and skips silently when already run today.
    ac11_structural = bool(re.search(r"ran_today", session_start_text)) and bool(
        re.search(r"skip\s+silently", session_start_text, re.IGNORECASE)
    )
    results.append(
        (
            "AC11 (structural half): daily-habits step gates on ran_today, skips if already run today",
            ac11_structural,
            "found" if ac11_structural else "not found in session-start SKILL.md",
        )
    )

    # --- AC 19 (structural half): a news failure never stops session-start
    # from completing -- stated explicitly in session-start's daily-habits step.
    ac19_structural = (
        "never stops this session from having completed" in session_start_text
    )
    results.append(
        (
            "AC19 (structural half): a news failure never stops /session-start from completing",
            ac19_structural,
            "found" if ac19_structural else "not found in session-start SKILL.md",
        )
    )

    # --- Structural: the script has no RSS URL anywhere. ---
    no_rss_url = "feeds/videos.xml" not in youtube_text and "ATOM =" not in youtube_text
    results.append(
        (
            "Structural: youtube_subs.py has no RSS URL/namespace",
            no_rss_url,
            "clean" if no_rss_url else "found an RSS reference",
        )
    )

    # --- Structural: news-keywords.txt exists at the brain root. ---
    keywords_exists = KEYWORDS_FILE.is_file()
    results.append(
        (
            "Structural: news-keywords.txt exists at the brain root",
            keywords_exists,
            str(KEYWORDS_FILE) if keywords_exists else "missing",
        )
    )

    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} of this script's criteria pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

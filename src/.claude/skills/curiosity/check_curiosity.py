#!/usr/bin/env python3
"""Issue #6, cycle 1 -- activation-mechanism checks for `.claude/skills/curiosity/`.

This cycle proves the activation mechanism itself (AC 1-5), the record's
persistence and git-ignore status (AC 5), and the STRUCTURAL half of AC 6 and
AC 8 -- that the heartbeat's `goal.md` and the skill's own text route a
disabled/off-gate case to "do nothing", checked by reading those files
directly, not by running a live pass. The BEHAVIORAL half of AC 6-9 (a real
`/session-start` or heartbeat run that actually obeys the gate) needs a
headless scripted-agent run and is a later cycle's work, once the activation
mechanism proven here is trusted -- see this story's `observe.md`.

Drives `.claude/shared/activation.py` directly (mechanism-tier proof, the
strongest tier this story's `observe.md` recognises) against a scratch brain
root under `C:/Projects/.tmp/second-brain-loop-6/`. Never touches the live
`.claude/activations.json`.

Usage: python check_curiosity.py
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
SKILL_MD = REPO_ROOT / ".claude" / "skills" / "curiosity" / "SKILL.md"
SESSION_START_MD = REPO_ROOT / ".claude" / "skills" / "session-start" / "SKILL.md"
HEARTBEAT_GOAL_MD = REPO_ROOT / ".claude" / "skills" / "heartbeat" / "goal.md"
GITIGNORE = REPO_ROOT / ".gitignore"

SCRATCH_ROOT = Path("C:/Projects/.tmp/second-brain-loop-6")
SCRATCH_BRAIN = SCRATCH_ROOT / "brain"

sys.path.insert(0, str(ACTIVATION_PY.parent))


def build_scratch_brain() -> Path:
    # Clean only this script's OWN subtree -- SCRATCH_ROOT is shared with
    # check_curiosity_pass_scripted_agent.py's scratch project and data dirs;
    # wiping the whole root would delete siblings mid-use (found the hard way
    # in cycle 2).
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
        print(f"[FAIL] curiosity SKILL.md not found at {SKILL_MD}")
        return 1

    import activation as act  # noqa: E402  (path inserted above)

    scratch_brain = build_scratch_brain()
    path = scratch_brain / ".claude" / "activations.json"

    # --- AC 1: fresh record -> needs asking. ---
    fresh = act.load_record(path)
    ok1 = act.needs_ask(fresh, "curiosity", "0.3.1")
    results.append(("AC1: a fresh record needs asking", ok1, f"needs_ask={ok1}"))

    # --- AC 2: a yes is recorded and curiosity is active from that session on. ---
    r = act.set_answer(fresh, "curiosity", "0.3.1", active=True)
    ok2 = act.is_active(r, "curiosity") and not act.needs_ask(r, "curiosity", "0.3.1")
    results.append(
        (
            "AC2: a yes is recorded, active from that session on",
            ok2,
            f"is_active={act.is_active(r, 'curiosity')} needs_ask={act.needs_ask(r, 'curiosity', '0.3.1')}",
        )
    )

    # --- AC 3: a no (or no answer) is recorded, and not asked again until VERSION
    # changes. Two halves: same-version -> no re-ask; changed-version -> re-ask. ---
    r_no = act.set_answer(fresh, "curiosity", "0.3.1", active=False)
    same_version_no_reask = not act.needs_ask(r_no, "curiosity", "0.3.1")
    next_version_reasks = act.needs_ask(r_no, "curiosity", "0.4.0")
    ok3 = (
        same_version_no_reask
        and next_version_reasks
        and not act.is_active(r_no, "curiosity")
    )
    # Checks for the CONCRETE hint command, not a generic phrase -- issue #7
    # turned session-start's activation step into a table shared by two
    # habits, and a generic "hint for switching it on later" sentence
    # regressed to a table-relative one ("that habit's one-line hint from
    # the table above"), which is still correct but no longer matches a
    # fixed phrase. The command itself is the part that must not go missing.
    hint_in_session_start = "/curiosity on" in SESSION_START_MD.read_text(
        encoding="utf-8"
    )
    hint_in_skill = "/curiosity on" in SKILL_MD.read_text(encoding="utf-8")
    ok3 = ok3 and hint_in_session_start and hint_in_skill
    results.append(
        (
            "AC3: a no/no-answer is recorded, one-line hint given, no re-ask until VERSION changes",
            ok3,
            f"same_version_no_reask={same_version_no_reask} next_version_reasks={next_version_reasks} "
            f"hint_in_session_start={hint_in_session_start} hint_in_skill={hint_in_skill}",
        )
    )

    # --- AC 4: /curiosity on, off, status work at any time and say what state
    # resulted. Drive activation.py the way the skill's own documented handling
    # does, and check the skill states the confirmation text for each. ---
    on_record = act.set_answer({}, "curiosity", "0.3.1", active=True)
    off_record = act.set_answer(on_record, "curiosity", "0.3.1", active=False)
    on_off_roundtrip_ok = act.is_active(on_record, "curiosity") and not act.is_active(
        off_record, "curiosity"
    )
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    says_on = "Curiosity is on." in skill_text
    says_off = "Curiosity is off." in skill_text
    says_status = bool(
        re.search(
            r"status.{0,200}(active|inactive)", skill_text, re.IGNORECASE | re.DOTALL
        )
    )
    ok4 = on_off_roundtrip_ok and says_on and says_off and says_status
    results.append(
        (
            "AC4: /curiosity on|off|status work at any time and say what resulted",
            ok4,
            f"roundtrip_ok={on_off_roundtrip_ok} says_on={says_on} says_off={says_off} says_status={says_status}",
        )
    )

    # --- AC 5: the recorded answer survives a restart and is git-ignored. A
    # real restart, not the same process: write via a subprocess, read back via
    # a SEPARATE subprocess. ---
    write_script = (
        "import sys; sys.path.insert(0, %r); import activation as act; "
        "r = act.set_answer(act.load_record(act.Path(%r)), 'curiosity', '0.3.1', active=True); "
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
    restart_ok = (
        restart_ok and restarted_record.get("curiosity", {}).get("active") is True
    )
    gitignore_text = GITIGNORE.read_text(encoding="utf-8")
    gitignored = ".claude/activations.json" in gitignore_text
    ok5 = restart_ok and gitignored
    results.append(
        (
            "AC5: the recorded answer survives a restart and is git-ignored",
            ok5,
            f"restart_ok={restart_ok} gitignored={gitignored} p_write.rc={p_write.returncode} p_read.rc={p_read.returncode}",
        )
    )

    # --- AC 6 (structural half): with curiosity off, nothing is printed,
    # stored or scheduled. Checked here as: the heartbeat's goal.md gates
    # EVERY invocation on the record's active flag before calling /curiosity
    # at all, and the skill itself re-checks is_active for the heartbeat-fired
    # path. The behavioral half (a live run that actually produces no output)
    # is a later cycle. ---
    heartbeat_text = HEARTBEAT_GOAL_MD.read_text(encoding="utf-8")
    heartbeat_gates_on_active = bool(
        re.search(
            r"present and active.{0,200}run it",
            heartbeat_text,
            re.IGNORECASE | re.DOTALL,
        )
    ) and bool(
        re.search(
            r"inactive.{0,80}do nothing", heartbeat_text, re.IGNORECASE | re.DOTALL
        )
    )
    skill_reasserts_gate = "re-checks" in skill_text and "is_active" in skill_text
    ok6_structural = heartbeat_gates_on_active and skill_reasserts_gate
    results.append(
        (
            "AC6 (structural half): off-gate text routes to nothing; behavioral half pending a headless run",
            ok6_structural,
            f"heartbeat_gates_on_active={heartbeat_gates_on_active} skill_reasserts_gate={skill_reasserts_gate}",
        )
    )

    # --- AC 8 (structural half): never fires while the owner is in
    # conversation or the brain is mid-task. Text-presence check only; the
    # behavioral half is the same later-cycle headless run as AC 7. ---
    says_never_in_conversation = bool(
        re.search(
            r"never fires.{0,120}conversation", skill_text, re.IGNORECASE | re.DOTALL
        )
    )
    heartbeat_says_idle_condition = "Idle is the condition" in heartbeat_text
    ok8_structural = says_never_in_conversation and heartbeat_says_idle_condition
    results.append(
        (
            "AC8 (structural half): text says it never fires mid-conversation/mid-task; behavioral half pending",
            ok8_structural,
            f"says_never_in_conversation={says_never_in_conversation} heartbeat_says_idle_condition={heartbeat_says_idle_condition}",
        )
    )

    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} of this script's criteria pass.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

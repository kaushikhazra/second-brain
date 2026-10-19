#!/usr/bin/env python3
"""PreToolUse hook for issue #47: every shell command is judged before it runs.

Protocol: JSON on stdin -- {"tool_name": "Bash"|"PowerShell", "tool_input":
{"command": ...}}. Deny-then-ack, and it never allows. A suspicious command
(deletes / overwrites / production / off-machine, any band at or above allow_below)
is denied once, with the reason and an ack code: the hash of the exact command text.
Re-running the same command with `# guard-ack:<code>` appended makes the hook stay
silent, so the owner's own permission rules decide. A missing, wrong or borrowed ack
is denied again. A safe command gets no output at all. `#` starts a comment in both
Bash and PowerShell, so the ack changes nothing that runs.

Stdlib only, like memory_guard.py: it runs with the bare `python` on PATH and
starts fresh on every tool call, so nothing heavy is imported. The model is a
linear one over hashed character n-grams; scoring a command is a few hundred
array look-ups per question.

    command ──▶ unwrap ──▶ features ──▶ 4 linear heads ──▶ bands ──▶ decision
               (decode      (hashed       delete · overwrite
                wrappers,    char and     · production · exfil)
                base64, hex) word grams)

Weights: command_guard.bin (float32: NUM_FEATURES x 4, then 4 biases) and
command_guard.json (dims, n-gram ranges, thresholds, version), written by
guard/train.py. Trained on synthetic and public commands only (AC 7).
"""

import base64
import binascii
import hashlib
import json
import re
import sys
import zlib
from array import array
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUESTIONS = ["delete", "overwrite", "production", "exfil"]
SAYS = {
    "delete": "deletes something",
    "overwrite": "overwrites or loses existing data",
    "production": "touches production",
    "exfil": "sends data off the machine",
}
MAX_DEPTH = 3

# ---------------------------------------------------------------- unwrap (AC 2)
# The model must judge what will actually run, so wrappers are opened and
# encoded payloads decoded first. Each finding is appended to the text the
# model reads; the original stays too, since the wrapper itself is a signal.

SHELL_C = re.compile(
    r"""\b(?:ba|z|k|da)?sh(?:\.exe)?\s+(?:-\w+\s+)*-c\s+(?P<q>['"])(?P<body>.*?)(?P=q)""",
    re.S,
)
PY_C = re.compile(
    r"""\b(?:python[\d.]*|py)(?:\.exe)?\s+(?:-\w+\s+)*-c\s+(?P<q>['"])(?P<body>.*?)(?P=q)""",
    re.S,
)
PS_CMD = re.compile(
    r"""\b(?:powershell|pwsh)(?:\.exe)?\b[^"'\n]*?-(?:c|command)\s+(?P<q>['"])(?P<body>.*?)(?P=q)""",
    re.S | re.I,
)
PS_ENC = re.compile(
    r"""-(?:e|ec|enc|encodedcommand)\s+(?P<b64>[A-Za-z0-9+/=]{8,})""", re.I
)
EVALS = re.compile(
    r"""\b(?:eval|iex|invoke-expression)\s*\(?\s*(?P<q>['"])(?P<body>.*?)(?P=q)""",
    re.S | re.I,
)
B64 = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")
HEX = re.compile(r"(?:\\x[0-9a-fA-F]{2}){4,}|\b(?:[0-9a-fA-F]{2}){8,}\b")


def _printable(raw):
    try:
        s = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            s = raw.decode("utf-16-le")
        except UnicodeDecodeError:
            return None
    s = s.replace("\x00", "")
    ok = sum(ch.isprintable() or ch in "\n\t\r" for ch in s)
    return s if s and ok / len(s) > 0.95 else None


def _b64(token):
    try:
        return _printable(
            base64.b64decode(token + "=" * (-len(token) % 4), validate=True)
        )
    except (binascii.Error, ValueError):
        return None


def _hex(token):
    try:
        return _printable(bytes.fromhex(token.replace("\\x", "")))
    except ValueError:
        return None


def unwrap(command, depth=0):
    """The command plus every inner command and decoded payload found in it."""
    found = []
    if depth >= MAX_DEPTH:
        return found
    for rx in (SHELL_C, PY_C, PS_CMD, EVALS):
        for m in rx.finditer(command):
            found.append(m.group("body"))
    for m in PS_ENC.finditer(command):
        try:
            text = base64.b64decode(m.group("b64")).decode("utf-16-le")
            found.append(text)
        except (binascii.Error, UnicodeDecodeError, ValueError):
            pass
    for m in B64.finditer(command):
        text = _b64(m.group(0))
        if text and text not in found:
            found.append(text)
    for m in HEX.finditer(command):
        text = _hex(m.group(0))
        if text:
            found.append(text)
    for inner in list(found):
        found.extend(unwrap(inner, depth + 1))
    return found


def readable(command):
    """What the model reads: the command, then everything decoded out of it."""
    return "\n".join([command, *unwrap(command)])


# ---------------------------------------------------------------- features
# Character n-grams catch syntax (`rm -rf`, `>|`, `--force`) wherever it sits;
# word unigrams and bigrams catch the verbs. Both are hashed into one space.
# crc32 is in the stdlib and stable across Python versions and machines,
# so training and the hook agree on every index.

WORD = re.compile(r"[A-Za-z0-9_.:/\\-]+|[|>&;<$`]+")


def features(text, num_features, char_range=(2, 5)):
    t = " " + text.lower() + " "
    idx = set()
    lo, hi = char_range
    for n in range(lo, hi + 1):
        for i in range(len(t) - n + 1):
            idx.add(
                zlib.crc32(b"c" + t[i : i + n].encode("utf-8", "replace"))
                % num_features
            )
    words = WORD.findall(text.lower())
    for w in words:
        idx.add(zlib.crc32(b"w" + w.encode("utf-8", "replace")) % num_features)
    for a, b in zip(words, words[1:]):
        idx.add(zlib.crc32(b"b" + f"{a} {b}".encode("utf-8", "replace")) % num_features)
    return idx


# ---------------------------------------------------------------- model


def load(folder=HERE):
    meta = json.loads((folder / "command_guard.json").read_text(encoding="utf-8"))
    w = array("f")
    with open(folder / "command_guard.bin", "rb") as fh:
        w.fromfile(fh, meta["num_features"] * len(QUESTIONS) + len(QUESTIONS))
    return meta, w


def scores(command, meta, w):
    """Probability, per question, that the command does that thing."""
    import math

    nf, nq = meta["num_features"], len(QUESTIONS)
    idx = features(readable(command), nf, tuple(meta["char_range"]))
    out = {}
    for q, name in enumerate(QUESTIONS):
        z = w[nf * nq + q] + sum(w[i * nq + q] for i in idx)
        out[name] = 1 / (1 + math.exp(-max(-30.0, min(30.0, z))))
    return out


ACK = re.compile(r"\s*#\s*guard-ack:(?P<code>[0-9a-fA-F]+)\s*\Z")
ACK_LEN = 6


def split_ack(command):
    """(command without its trailing ack comment, the code the ack carried or None)."""
    m = ACK.search(command)
    if not m:
        return command.strip(), None
    return command[: m.start()].strip(), m.group("code").lower()


def ack_code(command):
    """Short hash of the exact command text: an ack cannot be written before the
    command is known, and one command's ack means nothing on another."""
    return hashlib.sha256(command.encode("utf-8", "replace")).hexdigest()[:ACK_LEN]


def decide(p, meta):
    """Band and the questions that tripped. The band only shapes the wording of the
    denial: "deny" is a confident suspicion, "ask" a possible one, "allow" says
    nothing. Any band but "allow" is denied until acked. The names predate this
    and stay so training and the reports keep reading the same bands."""
    risky = [q for q in QUESTIONS if p[q] >= meta["deny_at"]]
    if risky:
        return "deny", risky
    unsure = [q for q in QUESTIONS if p[q] >= meta["allow_below"]]
    if unsure:
        return "ask", unsure
    return "allow", []


def switched_on():
    """The owner's /guard setting, from the activation record beside this hook folder
    (.claude/activations.json, entry "guard"; the shape shared/activation.py writes).
    Read inline, not through that module: the hook runs on its own and stays fast.
    No record, no entry or an unreadable file all mean off -- a new brain starts off."""
    try:
        record = json.loads((HERE.parent / "activations.json").read_text("utf-8"))
        return record["guard"]["active"] is True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def main():
    try:
        call = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if call.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    if not switched_on():
        return 0  # the guard is off: nothing is checked, denied or acknowledged
    raw = (call.get("tool_input") or {}).get("command") or ""
    command, acked = split_ack(raw)
    code = ack_code(command)
    try:
        meta, w = load()
    except OSError:
        reason = "The command guard has no weights, so it could not check this command."
    else:
        band, why = decide(scores(command, meta, w), meta)
        if not why:
            return 0  # nothing suspected: no output, the normal permission flow decides
        reason = (
            "The command guard "
            + ("is confident" if band == "deny" else "suspects")
            + " this command "
            + " and ".join(SAYS[q] for q in why)
            + ". It is a small model and can be wrong."
        )
    if acked == code:
        return 0  # checked and re-run with the matching ack: the owner's rules decide
    reason += (
        f" If you checked and still want it, re-run the same command with ` # guard-ack:{code}`"
        " appended (on a new last line if it ends in a heredoc)."
    )
    # deny, never allow: allow would skip the owner's own permission rules
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

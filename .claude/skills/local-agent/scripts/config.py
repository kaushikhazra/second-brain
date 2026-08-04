"""Persisted configuration for the local-agent skill.

Three things are remembered between runs, in `config.json` beside `SKILL.md`:
the Python interpreter to execute under, which ollama to talk to, and which
model to use. None of them are guessed — an unconfigured skill asks once and
saves the answer.

The ollama host is explicit by design. There is no network scanning: either it
is the local daemon or the caller says where it is.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any

CONFIG_FILENAME = "config.json"
DEFAULT_HOST = "http://localhost:11434"
DEFAULT_PORT = 11434

# Import name -> pip requirement. `pydantic` backs the result models, `ddgs`
# backs the web_search tool; without either the skill cannot honour its
# advertised contract, so both are checked before a run starts.
REQUIRED_PACKAGES: tuple[tuple[str, str], ...] = (
    ("pydantic", "pydantic"),
    ("ddgs", "ddgs"),
)


class ConfigError(ValueError):
    """Raised when configuration input cannot be used."""


def skill_directory() -> Path:
    """The skill root — the directory containing SKILL.md."""

    return Path(__file__).resolve().parents[1]


def config_path() -> Path:
    return skill_directory() / CONFIG_FILENAME


# Config values that are filesystem paths. Stored relative to the skill
# directory so a brain that is copied or moved keeps working, and resolved back
# to absolute on load so nothing downstream has to know the difference.
PATH_KEYS: tuple[str, ...] = ("python",)


def to_stored_path(value: str | None, base: Path | None = None) -> str | None:
    """Convert a path into the relative form written to config.json."""

    if not value:
        return value
    anchor = base or skill_directory()
    try:
        # Forward slashes even on Windows: valid there, and it keeps the JSON
        # free of escaped backslashes.
        return Path(os.path.relpath(Path(value), anchor)).as_posix()
    except (ValueError, OSError):
        # A different drive on Windows has no relative form — keep it absolute.
        return value


def from_stored_path(value: str | None, base: Path | None = None) -> str | None:
    """Resolve a stored path back to an absolute one.

    An absolute value is passed through untouched, so a hand-edited config
    still works.
    """

    if not value:
        return value
    candidate = Path(value)
    if candidate.is_absolute():
        return str(candidate)
    anchor = base or skill_directory()
    return str((anchor / candidate).resolve())


def normalise_host(value: str) -> str:
    """Turn user input into an ollama base URL.

    Accepts a bare IP or hostname, a host:port, or a full URL with any path
    (including the legacy `/v1` suffix, which is discarded). The port defaults
    to ollama's 11434 so `192.168.1.5` is enough.
    """

    raw = (value or "").strip()
    if not raw:
        raise ConfigError("Ollama host must not be empty")

    if "://" not in raw:
        raw = f"http://{raw}"

    parts = urllib.parse.urlsplit(raw)
    if not parts.hostname:
        raise ConfigError(f"Could not read a host from {value!r}")
    if parts.scheme not in ("http", "https"):
        raise ConfigError(f"Unsupported scheme {parts.scheme!r} in {value!r}")

    port = parts.port or DEFAULT_PORT
    return f"{parts.scheme}://{parts.hostname}:{port}"


def default_config() -> dict[str, Any]:
    return {"python": None, "ollama_host": DEFAULT_HOST, "model": None}


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Read config.json, falling back to defaults for anything absent.

    A corrupt file is treated as absent rather than fatal: the skill can always
    be reconfigured, and refusing to start would be the worse failure.
    """

    target = path or config_path()
    config = default_config()
    try:
        # utf-8-sig, not utf-8: Windows editors and PowerShell's `Out-File
        # -Encoding utf8` prepend a BOM, and a plain utf-8 read leaves it in the
        # string, so json.loads fails and the whole file is silently ignored.
        raw = target.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return config

    try:
        stored = json.loads(raw)
    except ValueError:
        return config

    if isinstance(stored, dict):
        for key in config:
            if stored.get(key) is not None:
                config[key] = stored[key]

    anchor = target.parent
    for key in PATH_KEYS:
        config[key] = from_stored_path(config.get(key), anchor)
    return config


def save_config(config: dict[str, Any], path: Path | None = None) -> Path:
    """Write config.json, creating the skill directory entry if needed."""

    target = path or config_path()
    payload = {key: config.get(key) for key in default_config()}
    anchor = target.parent
    for key in PATH_KEYS:
        payload[key] = to_stored_path(payload.get(key), anchor)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def is_configured(config: dict[str, Any]) -> bool:
    """A config is usable once a model has been chosen; host always has a default."""

    return bool(config.get("model"))


def missing_dependencies() -> list[str]:
    """Return pip requirement names that are not importable in this interpreter."""

    return [
        requirement
        for module, requirement in REQUIRED_PACKAGES
        if importlib.util.find_spec(module) is None
    ]


def interpreter_matches(configured: str | None) -> bool:
    """Is the configured interpreter the one already running?

    Compared by resolved path so a symlink or a differently-cased Windows path
    does not cause a pointless re-exec loop.
    """

    if not configured:
        return True
    try:
        return Path(configured).resolve() == Path(sys.executable).resolve()
    except OSError:  # pragma: no cover - unreachable path on a sane filesystem
        return False


def resolve_interpreter(configured: str | None) -> str | None:
    """Return the interpreter to switch to, or None to stay in this process."""

    if not configured or interpreter_matches(configured):
        return None
    if not Path(configured).is_file():
        raise ConfigError(f"Configured python interpreter does not exist: {configured}")
    return configured


def reexec_guard_active() -> bool:
    """True when this process is already the result of a re-exec."""

    return os.environ.get("LOCAL_AGENT_REEXEC") == "1"

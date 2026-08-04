"""CLI entry point for the local-agent skill."""

from __future__ import annotations

import asyncio
import argparse
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from config import (
    ConfigError,
    DEFAULT_HOST,
    config_path,
    is_configured,
    load_config,
    missing_dependencies,
    normalise_host,
    reexec_guard_active,
    resolve_interpreter,
    save_config,
)
from tools import RuntimeLog, install_runtime_log

DEFAULT_MODEL = "ornith:9b"
DEFAULT_ENDPOINT = DEFAULT_HOST
OVERALL_TIMEOUT_SECONDS = 600

# Bound lazily so a missing dependency is reported as JSON instead of blowing up
# at import time; `agent` pulls in pydantic, which is one of the things being
# checked for. Tests patch this attribute directly.
RUNNER = None

# Path-ish strings that fail to resolve are almost always typos rather than
# intentional prompts, so they are rejected instead of being sent to the model.
PATH_LIKE_SUFFIXES = (".txt", ".md", ".prompt", ".json", ".yaml", ".yml")


@dataclass
class RunResult:
    """Final CLI result printed for both success and failure."""

    status: str
    summary: str
    files_touched: list[str]
    commands_run: list[str]
    error_type: str | None
    error_message: str | None
    endpoint_used: str
    model_used: str
    context_length_ceiling: int | None = None
    context_length_active: int | None = None
    needs_configuration: bool = False
    available_models: list[str] = field(default_factory=list)
    configuration_required: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        # Derived here rather than at each call site: --status builds a result
        # directly and previously reported needs_configuration=false while
        # carrying a question, contradicting the documented contract.
        if self.configuration_required is not None:
            self.needs_configuration = True


class ResolverError(ValueError):
    """Raised when a task or system argument resolves to invalid text."""


class ArgumentParseError(ValueError):
    """Raised when CLI parsing fails and must be converted into RunResult JSON."""


@dataclass
class PreflightResult:
    available_models: list[str]
    context_length_ceiling: int | None = None
    context_length_active: int | None = None


class JsonArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that preserves normal help behavior and reports parse errors to main()."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        raise ArgumentParseError(message)


def _print_result(result: RunResult) -> None:
    print(json.dumps(asdict(result)))


def looks_like_a_path(value: str) -> bool:
    """Would a human have meant this string as a file path?

    Used to reject typos. A prompt is normally prose — multi-line, or with
    spaces and no separators. A single-line token carrying a path separator or
    a text-file suffix is a path that failed to resolve.
    """

    candidate = value.strip()
    if not candidate or "\n" in candidate:
        return False
    if candidate.lower().endswith(PATH_LIKE_SUFFIXES):
        return True
    if " " in candidate:
        return False
    # A bare separator is not enough — a literal like "yes/no" is prose. Only
    # explicitly rooted or relative-prefixed forms are treated as paths.
    if candidate.startswith(("./", "../", ".\\", "..\\", "~/", "~\\", "/")):
        return True
    return Path(candidate).is_absolute()


def resolve_text_argument(value: str, argument_name: str) -> str:
    """Resolve a literal string or existing file path into text."""

    candidate = Path(value)
    if not candidate.is_file() and looks_like_a_path(value):
        raise ResolverError(
            f"{argument_name} looks like a file path but no such file exists: {value}. "
            "Pass the literal text, or correct the path."
        )
    if candidate.is_file():
        try:
            with open(candidate, "r", encoding="utf-8-sig", newline="") as handle:
                resolved = handle.read()
        except UnicodeDecodeError as exc:
            raise ResolverError(
                f"Failed to read {argument_name} from {candidate}: {exc}"
            ) from exc
        except OSError as exc:
            raise ResolverError(
                f"Failed to read {argument_name} from {candidate}: {exc}"
            ) from exc
    else:
        resolved = value

    if not resolved.strip():
        raise ResolverError(
            f"{argument_name} resolved to empty or whitespace-only text"
        )
    return resolved


def _build_api_url(endpoint: str, path: str) -> str:
    parsed = urllib.parse.urlsplit(endpoint)
    if not parsed.scheme or not parsed.netloc:
        raise ResolverError(f"Invalid endpoint URL: {endpoint}")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _build_tags_url(endpoint: str) -> str:
    return _build_api_url(endpoint, "/api/tags")


def _fetch_context_length_ceiling(
    endpoint: str, model_name: str, timeout: float
) -> int | None:
    """Query /api/show for the model's architecture context ceiling."""
    show_url = _build_api_url(endpoint, "/api/show")
    body = json.dumps({"name": model_name}).encode("utf-8")
    request = urllib.request.Request(
        show_url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    model_info = payload.get("model_info", {})
    family = payload.get("details", {}).get("family", "")
    if family:
        value = model_info.get(f"{family}.context_length")
        if isinstance(value, int):
            return value
    # Fallback: scan all keys for any context_length entry.
    for key, value in model_info.items():
        if key.endswith(".context_length") and isinstance(value, int):
            return value
    return None


def _fetch_context_length_active(
    endpoint: str, model_name: str, timeout: float
) -> int | None:
    """Query /api/ps for the currently loaded model's active context length.

    The field name 'context_length' was confirmed against a live loaded model:
    GET /api/ps returned {"models":[{..., "context_length": 4096, ...}]}.
    This reflects the in-use window, which may be smaller than the ceiling if
    OLLAMA_CONTEXT_LENGTH is not set or is set below the model maximum.
    """
    ps_url = _build_api_url(endpoint, "/api/ps")
    request = urllib.request.Request(ps_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    for model in payload.get("models", []):
        if isinstance(model, dict) and model.get("name") == model_name:
            value = model.get("context_length")
            if isinstance(value, int):
                return value
    return None


def perform_preflight(
    endpoint: str, model_name: str, timeout: float = 5.0
) -> PreflightResult:
    """Probe the ollama tags endpoint, verify the requested model, and gather context info."""

    tags_url = _build_tags_url(endpoint)
    request = urllib.request.Request(tags_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise ConnectionError(
            str(exc.reason if hasattr(exc, "reason") else exc)
        ) from exc
    except socket.timeout as exc:
        raise ConnectionError(str(exc)) from exc
    except TimeoutError as exc:
        raise ConnectionError(str(exc)) from exc
    except OSError as exc:
        raise ConnectionError(str(exc)) from exc
    except ValueError as exc:
        raise ConnectionError(
            f"Invalid JSON from preflight endpoint {tags_url}: {exc}"
        ) from exc

    available_models = [
        model.get("name")
        for model in payload.get("models", [])
        if isinstance(model, dict) and model.get("name")
    ]
    if model_name not in available_models:
        available_display = (
            ", ".join(available_models) if available_models else "(none)"
        )
        raise LookupError(
            f"Requested model '{model_name}' was not found. Available models: {available_display}"
        )

    ceiling = _fetch_context_length_ceiling(endpoint, model_name, timeout)
    active = _fetch_context_length_active(endpoint, model_name, timeout)
    print(
        f"preflight: context_length_ceiling={ceiling} context_length_active={active}",
        file=sys.stderr,
    )
    return PreflightResult(
        available_models=available_models,
        context_length_ceiling=ceiling,
        context_length_active=active,
    )


async def _run_with_timeout(
    task_text: str,
    system_text: str,
    model_name: str,
    timeout_seconds: float,
) -> "Any":
    # asyncio cancellation stops the agent coroutine at its await points, which
    # fixes the old "timeout only stops waiting" behavior. A sync tool already
    # executing in a worker thread cannot be interrupted by this cancellation;
    # that residual window is bounded by the tool's own timeout (run_command:
    # 120s, web_search: 30s) and is intentionally documented rather than
    # engineered around with subprocess isolation.
    return await asyncio.wait_for(
        _resolve_runner()(task_text, system_text, model_name), timeout=timeout_seconds
    )


def _resolve_runner():
    """Return the agent runner, importing it only when it is actually needed.

    Deferred so a missing dependency is reported as JSON rather than raised as
    an ImportError while this module loads. A patched RUNNER always wins.
    """

    if RUNNER is not None:
        return RUNNER
    from agent import run_agent_summary

    return run_agent_summary


def _map_runner_exception(
    exc: Exception,
    context_length_ceiling: int | None = None,
    context_length_active: int | None = None,
) -> tuple[str, str, str]:
    from agent import ModelBehaviorError, OutputValidationError, ToolCallLimitExceeded

    message = str(exc)
    if isinstance(exc, ToolCallLimitExceeded):
        return (
            "tool_call_limit_exceeded",
            "Agent run exceeded the 15 successful tool call limit",
            message,
        )
    if isinstance(exc, OutputValidationError):
        ctx_hint = ""
        if context_length_active is not None:
            ctx_hint = (
                f" Active context window: {context_length_active} tokens"
                f" (model ceiling: {context_length_ceiling}). Context overflow is a"
                " possible cause; pass --num-ctx, or set OLLAMA_CONTEXT_LENGTH on the"
                " server to change the default window."
            )
        return (
            "structured_output_validation_failed",
            "Agent run exceeded the structured output validation retry limit",
            message + ctx_hint,
        )
    if isinstance(exc, ModelBehaviorError):
        # A reply that is not shaped like a chat message at all (no assistant
        # message) is most likely a truncated response from an overflowing window.
        return (
            "context_overflow",
            "Agent run failed: model returned an unexpected response, likely due to context overflow",
            message,
        )
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError, asyncio.CancelledError)):
        return (
            "overall_timeout_exceeded",
            "Agent run exceeded the 600 second overall timeout",
            message,
        )
    return ("agent_run_failed", "Agent run failed before completing", message)


def _error_result(
    *,
    summary: str,
    error_type: str,
    error_message: str,
    endpoint_used: str,
    model_used: str,
    runtime_log: RuntimeLog,
    context_length_ceiling: int | None = None,
    context_length_active: int | None = None,
    needs_configuration: bool = False,
    available_models: list[str] | None = None,
    configuration_required: dict[str, Any] | None = None,
) -> RunResult:
    return RunResult(
        status="error",
        summary=summary,
        files_touched=runtime_log.files_touched,
        commands_run=runtime_log.commands_run,
        error_type=error_type,
        error_message=error_message,
        endpoint_used=endpoint_used,
        model_used=model_used,
        context_length_ceiling=context_length_ceiling,
        context_length_active=context_length_active,
        needs_configuration=needs_configuration or configuration_required is not None,
        available_models=available_models or [],
        configuration_required=configuration_required,
    )


def _build_parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(prog="run.py")
    parser.add_argument(
        "--task",
        required=True,
        help="Literal task text or an existing UTF-8 file path.",
    )
    parser.add_argument(
        "--system",
        required=True,
        help="Literal system prompt text or an existing UTF-8 file path.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Ollama model name. Defaults to the configured model.",
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help="Ollama base URL. Defaults to the configured host.",
    )
    parser.add_argument(
        "--num-ctx",
        type=int,
        default=None,
        help=(
            "Context window for this run, in tokens. Omit to use the server default "
            "(OLLAMA_CONTEXT_LENGTH). Only honoured on the native API."
        ),
    )
    return parser


def _build_configure_parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(prog="run.py --configure")
    parser.add_argument("--configure", action="store_true")
    parser.add_argument("--set-host", default=None, help="Ollama host, IP, or full URL.")
    parser.add_argument("--set-model", default=None, help="Model name to use by default.")
    parser.add_argument(
        "--set-python",
        default=None,
        help="Interpreter to run the skill under. Use 'none' to clear it.",
    )
    return parser


def _bootstrap_endpoint_and_model(argv: Sequence[str] | None) -> tuple[str, str]:
    """Best-effort endpoint/model for error paths that fire before full parsing."""

    config = load_config()
    endpoint = config.get("ollama_host") or DEFAULT_ENDPOINT
    model = config.get("model") or DEFAULT_MODEL
    parser = JsonArgumentParser(add_help=False)
    parser.add_argument("--model", default=None)
    parser.add_argument("--endpoint", default=None)
    try:
        namespace, _ = parser.parse_known_args(argv)
    except ArgumentParseError:
        return endpoint, model
    return (namespace.endpoint or endpoint), (namespace.model or model)


def list_available_models(endpoint: str, timeout: float = 5.0) -> list[str]:
    """Best-effort model list for the configuration prompt. Never raises."""

    try:
        request = urllib.request.Request(_build_tags_url(endpoint), method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []
    return [
        model.get("name")
        for model in payload.get("models", [])
        if isinstance(model, dict) and model.get("name")
    ]


def _reexec(interpreter: str, argv: Sequence[str] | None) -> int:
    """Re-run this script under the configured interpreter.

    A subprocess rather than os.execv so a broken interpreter can still be
    reported as JSON. The child's stdout is forwarded untouched, preserving the
    one-JSON-object-per-invocation contract.
    """

    command = [interpreter, str(Path(__file__).resolve()), *(argv or sys.argv[1:])]
    environment = {**os.environ, "LOCAL_AGENT_REEXEC": "1"}
    completed = subprocess.run(command, capture_output=True, text=True, env=environment)
    if completed.stdout:
        sys.stdout.write(completed.stdout)
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    return 0


def _self_command() -> list[str]:
    """How to invoke this script again, for the resolve command handed back."""

    return [sys.executable, str(Path(__file__).resolve())]


def _choice(
    *,
    field_name: str,
    question: str,
    options: list[dict[str, str]],
    flag: str,
    allow_custom: bool = False,
) -> dict[str, Any]:
    """Describe a decision the caller must put to the user.

    The skill is always driven by an agent harness, never by a human at a
    terminal, so a blocked run does not prompt — it returns the question, the
    options, and the exact command that records the answer. The caller asks the
    user and re-invokes.
    """

    return {
        "field": field_name,
        "question": question,
        "options": options,
        "allow_custom": allow_custom,
        "resolve_command": [*_self_command(), "--configure", flag, "<value>"],
    }


def model_choice(models: list[str], endpoint: str) -> dict[str, Any]:
    return _choice(
        field_name="model",
        question=f"Which ollama model should the local agent use on {endpoint}?",
        options=[{"value": name, "label": name, "description": ""} for name in models],
        flag="--set-model",
        allow_custom=not models,
    )


def host_choice(current: str) -> dict[str, Any]:
    """Local daemon or an address the user supplies. Never a network scan."""

    options = [
        {
            "value": DEFAULT_HOST,
            "label": "Local ollama",
            "description": f"The daemon on this machine ({DEFAULT_HOST})",
        },
    ]
    if current and current != DEFAULT_HOST:
        options.append(
            {"value": current, "label": current, "description": "Currently configured host"}
        )
    return _choice(
        field_name="ollama_host",
        question="Which ollama should the local agent talk to?",
        options=options,
        flag="--set-host",
        allow_custom=True,
    )


def interpreter_choice(configured: str | None) -> dict[str, Any]:
    """Offer the interpreters we can actually see, rather than asking blind."""

    candidates: list[dict[str, str]] = []
    brain_venv = Path(__file__).resolve().parents[3] / ".venv" / "Scripts" / "python.exe"
    if brain_venv.is_file():
        candidates.append(
            {
                "value": str(brain_venv),
                "label": "Brain venv",
                "description": "Self-contained interpreter under .claude/.venv",
            }
        )
    candidates.append(
        {
            "value": sys.executable,
            "label": "Current interpreter",
            "description": sys.executable,
        }
    )
    if configured:
        candidates.append(
            {"value": "none", "label": "Clear the setting", "description": f"Stop using {configured}"}
        )
    return _choice(
        field_name="python",
        question="Which Python interpreter should the local agent run under?",
        options=candidates,
        flag="--set-python",
        allow_custom=True,
    )


def dependency_choice(absent: list[str], interpreter: str) -> dict[str, Any]:
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    install = f'"{interpreter}" -m pip install -r "{requirements}"'
    return {
        "field": "dependencies",
        "question": f"Install the missing packages ({', '.join(absent)}) for {interpreter}?",
        "options": [
            {"value": install, "label": "Install now", "description": install},
        ],
        "allow_custom": False,
        "resolve_command": [interpreter, "-m", "pip", "install", "-r", str(requirements)],
    }


def status(runtime_log: RuntimeLog) -> int:
    """Report configuration and reachability without running or changing anything.

    Lets the caller orient before it puts a question to the user: one call says
    whether the interpreter is usable, the packages are installed, the host
    answers, and the configured model is actually there.
    """

    config = load_config()
    endpoint = config.get("ollama_host") or DEFAULT_ENDPOINT
    configured_model = config.get("model") or ""

    interpreter_error = None
    try:
        resolve_interpreter(config.get("python"))
    except ConfigError as exc:
        interpreter_error = str(exc)

    absent = missing_dependencies()
    models = list_available_models(endpoint)

    # Report the first blocker that would stop a real run, in the order a run
    # would hit them.
    blocked_on: dict[str, Any] | None = None
    if interpreter_error:
        blocked_on = interpreter_choice(config.get("python"))
    elif absent:
        blocked_on = dependency_choice(absent, config.get("python") or sys.executable)
    elif not models:
        blocked_on = host_choice(endpoint)
    elif not configured_model or configured_model not in models:
        blocked_on = model_choice(models, endpoint)

    findings = [
        f"interpreter: {interpreter_error or (config.get('python') or 'current')}",
        f"dependencies: {'missing ' + ', '.join(absent) if absent else 'ok'}",
        f"host {endpoint}: {'reachable' if models else 'no models listed'}",
        f"model: {configured_model or 'not chosen'}",
    ]

    _print_result(
        RunResult(
            status="success",
            summary="; ".join(findings),
            files_touched=[],
            commands_run=[],
            error_type=None,
            error_message=None,
            endpoint_used=endpoint,
            model_used=configured_model,
            available_models=models,
            configuration_required=blocked_on,
        )
    )
    return 0


def configure(argv: Sequence[str] | None, runtime_log: RuntimeLog) -> int:
    """Read/update config.json, prompting only when attached to a terminal."""

    parser = _build_configure_parser()
    try:
        args, _ = parser.parse_known_args(argv)
    except ArgumentParseError as exc:
        _print_result(
            _error_result(
                summary="Configuration arguments could not be parsed",
                error_type="invalid_arguments",
                error_message=str(exc),
                endpoint_used=DEFAULT_ENDPOINT,
                model_used="",
                runtime_log=runtime_log,
            )
        )
        return 0

    config = load_config()

    try:
        if args.set_host:
            config["ollama_host"] = normalise_host(args.set_host)
        if args.set_python is not None:
            config["python"] = None if args.set_python.lower() == "none" else args.set_python
        if args.set_model:
            config["model"] = args.set_model
    except ConfigError as exc:
        _print_result(
            _error_result(
                summary="Configuration value was rejected",
                error_type="invalid_configuration",
                error_message=str(exc),
                endpoint_used=config.get("ollama_host") or DEFAULT_ENDPOINT,
                model_used=config.get("model") or "",
                runtime_log=runtime_log,
            )
        )
        return 0

    endpoint = config.get("ollama_host") or DEFAULT_ENDPOINT
    models = list_available_models(endpoint)

    if not config.get("model"):
        # No prompting: the caller is an agent harness, so hand back the
        # question and let it ask the user.
        blocked_on = model_choice(models, endpoint) if models else host_choice(endpoint)
        _print_result(
            _error_result(
                summary="A model must be chosen before the skill can run",
                error_type="model_not_configured",
                error_message=(
                    f"config.json at {config_path()} has no model. "
                    f"Host {endpoint} offers: {', '.join(models) if models else '(none reachable)'}"
                ),
                endpoint_used=endpoint,
                model_used="",
                runtime_log=runtime_log,
                available_models=models,
                configuration_required=blocked_on,
            )
        )
        return 0

    saved = save_config(config)
    _print_result(
        RunResult(
            status="success",
            summary=(
                f"Configuration saved to {saved}. Host {config['ollama_host']}, "
                f"model {config['model']}, python "
                f"{config['python'] or 'current interpreter'}."
            ),
            files_touched=[str(saved)],
            commands_run=[],
            error_type=None,
            error_message=None,
            endpoint_used=config["ollama_host"],
            model_used=config["model"],
            available_models=models,
        )
    )
    return 0


def _refresh_active_context(endpoint: str, model_name: str, current: int | None) -> int | None:
    """Re-read the active window after the run.

    Preflight asks before the model is loaded, so on a cold start it always
    reports null — precisely when the value would be most useful. Asking again
    afterwards is the only way to observe the window the run actually used.
    """

    return _fetch_context_length_active(endpoint, model_name, 5.0) or current


def main(argv: list[str] | None = None) -> int:
    runtime_log = RuntimeLog()

    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--status" in arguments:
        return status(runtime_log)
    if "--configure" in arguments:
        return configure(arguments, runtime_log)

    config = load_config()

    # Switch interpreters before doing anything else, so the dependency check
    # below reports on the interpreter that will actually run the agent.
    if not reexec_guard_active():
        try:
            target = resolve_interpreter(config.get("python"))
        except ConfigError as exc:
            _print_result(
                _error_result(
                    summary="Configured python interpreter is unusable",
                    error_type="invalid_configuration",
                    error_message=str(exc),
                    endpoint_used=config.get("ollama_host") or DEFAULT_ENDPOINT,
                    model_used=config.get("model") or "",
                    runtime_log=runtime_log,
                    configuration_required=interpreter_choice(config.get("python")),
                )
            )
            return 0
        if target:
            return _reexec(target, arguments)

    absent = missing_dependencies()
    if absent:
        _print_result(
            _error_result(
                summary="Required Python packages are missing",
                error_type="missing_dependencies",
                error_message=(
                    f"Missing: {', '.join(absent)}. Install them with: "
                    f'"{sys.executable}" -m pip install -r '
                    f"{Path(__file__).resolve().parents[1] / 'requirements.txt'}"
                ),
                endpoint_used=config.get("ollama_host") or DEFAULT_ENDPOINT,
                model_used=config.get("model") or "",
                runtime_log=runtime_log,
                configuration_required=dependency_choice(absent, sys.executable),
            )
        )
        return 0

    parser = _build_parser()
    endpoint_used, model_used = _bootstrap_endpoint_and_model(argv)
    # Initialised to None; updated after a successful preflight so that all
    # error paths after preflight can carry the context values.
    ctx_ceiling: int | None = None
    ctx_active: int | None = None

    try:
        args = parser.parse_args(argv)
    except ArgumentParseError as exc:
        result = _error_result(
            summary="CLI argument parsing failed before the agent could run",
            error_type="invalid_arguments",
            error_message=str(exc),
            endpoint_used=endpoint_used,
            model_used=model_used,
            runtime_log=runtime_log,
        )
        _print_result(result)
        return 0

    endpoint_used = args.endpoint or config.get("ollama_host") or DEFAULT_ENDPOINT
    model_used = args.model or config.get("model") or ""

    if not model_used:
        candidates = list_available_models(endpoint_used)
        _print_result(
            _error_result(
                summary="No model has been chosen for this skill yet",
                error_type="model_not_configured",
                error_message=(
                    f"Choose a model and save it: run.py --configure --set-model <name>. "
                    f"Host {endpoint_used} offers: "
                    f"{', '.join(candidates) if candidates else '(none reachable)'}"
                ),
                endpoint_used=endpoint_used,
                model_used="",
                runtime_log=runtime_log,
                available_models=candidates,
                configuration_required=(
                    model_choice(candidates, endpoint_used)
                    if candidates
                    else host_choice(endpoint_used)
                ),
            )
        )
        return 0

    try:
        with install_runtime_log(runtime_log):
            task_text = resolve_text_argument(args.task, "--task")
            system_text = resolve_text_argument(args.system, "--system")
            os.environ["OLLAMA_BASE_URL"] = endpoint_used
            if args.num_ctx is not None:
                os.environ["OLLAMA_NUM_CTX"] = str(args.num_ctx)
            else:
                os.environ.pop("OLLAMA_NUM_CTX", None)
            preflight_result = perform_preflight(endpoint_used, model_used)
            ctx_ceiling = preflight_result.context_length_ceiling
            ctx_active = preflight_result.context_length_active
            summary_result = asyncio.run(
                _run_with_timeout(
                    task_text, system_text, model_used, OVERALL_TIMEOUT_SECONDS
                )
            )
    except ResolverError as exc:
        result = _error_result(
            summary="Input resolution failed before the agent could run",
            error_type="input_resolution_failed",
            error_message=str(exc),
            endpoint_used=endpoint_used,
            model_used=model_used,
            runtime_log=runtime_log,
            context_length_ceiling=ctx_ceiling,
            context_length_active=ctx_active,
        )
    except ConnectionError as exc:
        result = _error_result(
            summary="Endpoint preflight failed because the ollama endpoint is unreachable",
            error_type="endpoint_unreachable",
            error_message=(
                f"{exc}. Point the skill at a reachable ollama with: "
                "run.py --configure --set-host <ip-or-url>"
            ),
            endpoint_used=endpoint_used,
            model_used=model_used,
            runtime_log=runtime_log,
            context_length_ceiling=ctx_ceiling,
            context_length_active=ctx_active,
            configuration_required=host_choice(endpoint_used),
        )
    except LookupError as exc:
        candidates = list_available_models(endpoint_used)
        result = _error_result(
            summary="Endpoint preflight succeeded but the requested model is not available",
            error_type="model_not_found",
            error_message=(
                f"{exc}. Choose one with: run.py --configure --set-model <name>"
            ),
            endpoint_used=endpoint_used,
            model_used=model_used,
            runtime_log=runtime_log,
            context_length_ceiling=ctx_ceiling,
            context_length_active=ctx_active,
            available_models=candidates,
            configuration_required=model_choice(candidates, endpoint_used),
        )
    except Exception as exc:
        ctx_active = _refresh_active_context(endpoint_used, model_used, ctx_active)
        error_type, summary, error_message = _map_runner_exception(
            exc, ctx_ceiling, ctx_active
        )
        result = _error_result(
            summary=summary,
            error_type=error_type,
            error_message=error_message,
            endpoint_used=endpoint_used,
            model_used=model_used,
            runtime_log=runtime_log,
            context_length_ceiling=ctx_ceiling,
            context_length_active=ctx_active,
        )
    else:
        # The model owns summary only. One model turn may include multiple successful
        # tool calls, and failed file-touch attempts stay in the runtime log even
        # though the tool-call budget counts only successful calls.
        ctx_active = _refresh_active_context(endpoint_used, model_used, ctx_active)
        result = RunResult(
            status="success",
            summary=summary_result.summary,
            files_touched=runtime_log.files_touched,
            commands_run=runtime_log.commands_run,
            error_type=None,
            error_message=None,
            endpoint_used=endpoint_used,
            model_used=model_used,
            context_length_ceiling=ctx_ceiling,
            context_length_active=ctx_active,
        )

    _print_result(result)
    return 0


def main_guarded(argv: list[str] | None = None) -> int:
    """Last line of defence for the one-JSON-object-per-invocation contract.

    Anything main() fails to anticipate would otherwise reach stdout/stderr as a
    traceback, which callers cannot parse.
    """

    try:
        return main(argv)
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 - deliberately total
        _print_result(
            RunResult(
                status="error",
                summary="run.py failed unexpectedly before it could report a result",
                files_touched=[],
                commands_run=[],
                error_type="internal_error",
                error_message=f"{type(exc).__name__}: {exc}",
                endpoint_used=DEFAULT_ENDPOINT,
                model_used="",
            )
        )
        return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main_guarded())

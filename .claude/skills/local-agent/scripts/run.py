"""CLI entry point for the local-agent skill."""

from __future__ import annotations

import asyncio
import argparse
import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded

from agent import AgentSummary, run_agent_summary
from tools import RuntimeLog, install_runtime_log

DEFAULT_MODEL = "ornith:9b"
DEFAULT_ENDPOINT = "http://localhost:11434/v1"
OVERALL_TIMEOUT_SECONDS = 600
RUNNER = run_agent_summary


class RunResult(BaseModel):
    """Final CLI result printed for both success and failure."""

    status: Literal["success", "error"]
    summary: str
    files_touched: list[str]
    commands_run: list[str]
    error_type: str | None
    error_message: str | None
    endpoint_used: str
    model_used: str


class ResolverError(ValueError):
    """Raised when a task or system argument resolves to invalid text."""


class ArgumentParseError(ValueError):
    """Raised when CLI parsing fails and must be converted into RunResult JSON."""


@dataclass
class PreflightResult:
    available_models: list[str]


class JsonArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that preserves normal help behavior and reports parse errors to main()."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        raise ArgumentParseError(message)


def _print_result(result: RunResult) -> None:
    print(result.model_dump_json())


def resolve_text_argument(value: str, argument_name: str) -> str:
    """Resolve a literal string or existing file path into text."""

    candidate = Path(value)
    if candidate.is_file():
        try:
            with open(candidate, "r", encoding="utf-8-sig", newline="") as handle:
                resolved = handle.read()
        except UnicodeDecodeError as exc:
            raise ResolverError(f"Failed to read {argument_name} from {candidate}: {exc}") from exc
        except OSError as exc:
            raise ResolverError(f"Failed to read {argument_name} from {candidate}: {exc}") from exc
    else:
        resolved = value

    if not resolved.strip():
        raise ResolverError(f"{argument_name} resolved to empty or whitespace-only text")
    return resolved


def _build_tags_url(endpoint: str) -> str:
    parsed = urllib.parse.urlsplit(endpoint)
    if not parsed.scheme or not parsed.netloc:
        raise ResolverError(f"Invalid endpoint URL: {endpoint}")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, "/api/tags", "", ""))


def perform_preflight(endpoint: str, model_name: str, timeout: float = 5.0) -> PreflightResult:
    """Probe the ollama tags endpoint and verify the requested model exists."""

    tags_url = _build_tags_url(endpoint)
    request = urllib.request.Request(tags_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise ConnectionError(str(exc.reason if hasattr(exc, "reason") else exc)) from exc
    except socket.timeout as exc:
        raise ConnectionError(str(exc)) from exc
    except TimeoutError as exc:
        raise ConnectionError(str(exc)) from exc
    except OSError as exc:
        raise ConnectionError(str(exc)) from exc
    except ValueError as exc:
        raise ConnectionError(f"Invalid JSON from preflight endpoint {tags_url}: {exc}") from exc

    available_models = [
        model.get("name")
        for model in payload.get("models", [])
        if isinstance(model, dict) and model.get("name")
    ]
    if model_name not in available_models:
        available_display = ", ".join(available_models) if available_models else "(none)"
        raise LookupError(f"Requested model '{model_name}' was not found. Available models: {available_display}")
    return PreflightResult(available_models=available_models)


async def _run_with_timeout(
    task_text: str,
    system_text: str,
    model_name: str,
    timeout_seconds: float,
) -> AgentSummary:
    # asyncio cancellation stops the agent coroutine at its await points, which
    # fixes the old "timeout only stops waiting" behavior. A sync tool already
    # executing in a worker thread cannot be interrupted by this cancellation;
    # that residual window is bounded by the tool's own timeout (run_command:
    # 120s, web_search: 30s) and is intentionally documented rather than
    # engineered around with subprocess isolation.
    return await asyncio.wait_for(RUNNER(task_text, system_text, model_name), timeout=timeout_seconds)


def _map_runner_exception(exc: Exception) -> tuple[str, str, str]:
    message = str(exc)
    if isinstance(exc, UsageLimitExceeded):
        return (
            "tool_call_limit_exceeded",
            "Agent run exceeded the 15 successful tool call limit",
            message,
        )
    if isinstance(exc, UnexpectedModelBehavior) and "Exceeded maximum retries (2) for output validation" in message:
        return (
            "structured_output_validation_failed",
            "Agent run exceeded the structured output validation retry limit",
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
    )


def _build_parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(prog="run.py")
    parser.add_argument("--task", required=True, help="Literal task text or an existing UTF-8 file path.")
    parser.add_argument("--system", required=True, help="Literal system prompt text or an existing UTF-8 file path.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model name. Default: {DEFAULT_MODEL}")
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"Ollama base URL. Default: {DEFAULT_ENDPOINT}",
    )
    return parser


def _bootstrap_endpoint_and_model(argv: Sequence[str] | None) -> tuple[str, str]:
    parser = JsonArgumentParser(add_help=False)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    try:
        namespace, _ = parser.parse_known_args(argv)
    except ArgumentParseError:
        return DEFAULT_ENDPOINT, DEFAULT_MODEL
    return namespace.endpoint, namespace.model


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    runtime_log = RuntimeLog()
    endpoint_used, model_used = _bootstrap_endpoint_and_model(argv)

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

    endpoint_used = args.endpoint
    model_used = args.model

    try:
        with install_runtime_log(runtime_log):
            task_text = resolve_text_argument(args.task, "--task")
            system_text = resolve_text_argument(args.system, "--system")
            os.environ["OLLAMA_BASE_URL"] = endpoint_used
            perform_preflight(endpoint_used, model_used)
            summary_result = asyncio.run(
                _run_with_timeout(task_text, system_text, model_used, OVERALL_TIMEOUT_SECONDS)
            )
    except ResolverError as exc:
        result = _error_result(
            summary="Input resolution failed before the agent could run",
            error_type="input_resolution_failed",
            error_message=str(exc),
            endpoint_used=endpoint_used,
            model_used=model_used,
            runtime_log=runtime_log,
        )
    except ConnectionError as exc:
        result = _error_result(
            summary="Endpoint preflight failed because the ollama endpoint is unreachable",
            error_type="endpoint_unreachable",
            error_message=str(exc),
            endpoint_used=endpoint_used,
            model_used=model_used,
            runtime_log=runtime_log,
        )
    except LookupError as exc:
        result = _error_result(
            summary="Endpoint preflight succeeded but the requested model is not available",
            error_type="model_not_found",
            error_message=str(exc),
            endpoint_used=endpoint_used,
            model_used=model_used,
            runtime_log=runtime_log,
        )
    except Exception as exc:
        error_type, summary, error_message = _map_runner_exception(exc)
        result = _error_result(
            summary=summary,
            error_type=error_type,
            error_message=error_message,
            endpoint_used=endpoint_used,
            model_used=model_used,
            runtime_log=runtime_log,
        )
    else:
        # The model owns summary only. One model turn may include multiple successful
        # tool calls, and failed file-touch attempts stay in the runtime log even
        # though UsageLimits(tool_calls_limit=15) counts only successful tool calls.
        result = RunResult(
            status="success",
            summary=summary_result.summary,
            files_touched=runtime_log.files_touched,
            commands_run=runtime_log.commands_run,
            error_type=None,
            error_message=None,
            endpoint_used=endpoint_used,
            model_used=model_used,
        )

    _print_result(result)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

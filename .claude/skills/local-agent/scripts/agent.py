"""Native ollama agent loop for the local-agent skill.

This talks to ollama's own `/api/chat` rather than its OpenAI-compatible `/v1`
shim. The `/v1` route was abandoned deliberately, and every reason was measured
against a live server rather than inferred:

* `num_ctx` is honoured natively and holds for the whole conversation. Over
  `/v1` it is accepted and silently discarded, so the context window could only
  be set server-wide via `OLLAMA_CONTEXT_LENGTH`.
* Native responses use `content: ''` where `/v1` emits `content: null` for a
  reasoning-only turn. Ollama then rejects its own null on the next request with
  `400 invalid message content type: <nil>`, which is unfixable client-side
  without rewriting outgoing bodies.
* Native `format` takes a JSON schema and is grammar-constrained. It coexists
  with `tools` — the model still emits tool calls while being held to the schema.

The cost of owning this loop is that tool schemas, the turn loop, output
validation, and the tool-call budget are all implemented here instead of coming
from a framework.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import typing
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from tools import edit_file, read_file, run_command, web_search, write_file

TOOL_CALL_LIMIT = 15
OUTPUT_RETRIES = 2
HTTP_TIMEOUT_SECONDS = 600
DEFAULT_ENDPOINT = "http://localhost:11434/v1"

# One turn is consumed per tool batch and per output-validation retry. The extra
# headroom covers the final answering turn plus a few no-op turns; it is a
# runaway guard, not a budget the model is expected to reach.
MAX_TURNS = TOOL_CALL_LIMIT + OUTPUT_RETRIES + 5

_JSON_TYPES: dict[Any, str] = {str: "string", int: "integer", float: "number", bool: "boolean"}


class AgentSummary(BaseModel):
    """Structured output emitted by the model."""

    summary: str


class ToolCallLimitExceeded(RuntimeError):
    """Raised when the model exceeds the successful tool call budget."""


class OutputValidationError(RuntimeError):
    """Raised when the model cannot produce schema-valid output within the retries."""


class ModelBehaviorError(RuntimeError):
    """Raised when ollama returns a response that is not shaped like a chat reply."""


TOOL_FUNCTIONS: tuple[Callable[..., str], ...] = (
    read_file,
    write_file,
    edit_file,
    run_command,
    web_search,
)


def build_tool_schema(function: Callable[..., str]) -> dict[str, Any]:
    """Derive an ollama tool schema from a Python function's signature.

    Generated rather than hand-written so the schema cannot drift from the
    implementation in `tools.py`; the first docstring line is the description.
    """

    hints = typing.get_type_hints(function)
    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, parameter in inspect.signature(function).parameters.items():
        annotation = hints.get(name, str)
        properties[name] = {"type": _JSON_TYPES.get(annotation, "string")}
        if parameter.default is inspect.Parameter.empty:
            required.append(name)

    description = (function.__doc__ or "").strip().splitlines()[0] if function.__doc__ else ""
    return {
        "type": "function",
        "function": {
            "name": function.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


TOOL_SCHEMAS: list[dict[str, Any]] = [build_tool_schema(f) for f in TOOL_FUNCTIONS]
TOOL_REGISTRY: dict[str, Callable[..., str]] = {f.__name__: f for f in TOOL_FUNCTIONS}


def native_chat_url(endpoint: str | None = None) -> str:
    """Convert a configured endpoint into ollama's native chat URL.

    The CLI still advertises the `/v1` style endpoint, so any path on it is
    discarded rather than appended to.
    """

    parts = urllib.parse.urlsplit(endpoint or os.environ.get("OLLAMA_BASE_URL") or DEFAULT_ENDPOINT)
    if not parts.scheme or not parts.netloc:
        raise ValueError(f"Invalid ollama endpoint: {endpoint}")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, "/api/chat", "", ""))


def configured_num_ctx() -> int | None:
    """Read the per-run context window, if one was requested.

    Threaded through the environment for the same reason as `OLLAMA_BASE_URL`:
    it keeps the runner signature that `run.py` and its tests depend on.
    """

    raw = os.environ.get("OLLAMA_NUM_CTX")
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def _post_chat(payload: dict[str, Any], url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        return json.loads(response.read())


async def chat_once(
    model_name: str,
    messages: list[dict[str, Any]],
    output_schema: dict[str, Any],
    url: str,
    num_ctx: int | None,
) -> dict[str, Any]:
    """Send one turn and return the assistant message.

    `format` and `tools` are sent together: grammar-constrained decoding
    constrains the text response without suppressing tool calls.
    """

    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "tools": TOOL_SCHEMAS,
        "format": output_schema,
        "stream": False,
    }
    if num_ctx is not None:
        payload["options"] = {"num_ctx": num_ctx}

    # Run the blocking request off the event loop so run.py's overall timeout can
    # cancel this coroutine at an await point.
    body = await asyncio.to_thread(_post_chat, payload, url)
    message = body.get("message")
    if not isinstance(message, dict):
        raise ModelBehaviorError(f"ollama returned no assistant message: {str(body)[:200]}")
    return message


def execute_tool_call(call: dict[str, Any]) -> tuple[str, str]:
    """Run one tool call and return (tool_name, result_text).

    A bad name or bad arguments is reported back to the model as a tool result
    rather than raised, so it can correct itself on the next turn.
    """

    function = call.get("function") or {}
    name = function.get("name") or ""
    arguments = function.get("arguments")

    # Native ollama sends arguments as an object; tolerate a JSON string in case
    # a model or a future version emits the OpenAI shape.
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except ValueError:
            return name, json.dumps({"status": "error", "error": f"Unparsable arguments: {arguments[:200]}"})
    if not isinstance(arguments, dict):
        arguments = {}

    implementation = TOOL_REGISTRY.get(name)
    if implementation is None:
        return name, json.dumps(
            {"status": "error", "error": f"Unknown tool '{name}'. Available: {sorted(TOOL_REGISTRY)}"}
        )

    try:
        return name, implementation(**arguments)
    except TypeError as exc:
        return name, json.dumps({"status": "error", "error": f"Bad arguments for '{name}': {exc}"})


def parse_summary(content: str) -> AgentSummary:
    """Validate one model response against the output contract."""

    if not content.strip():
        raise ValueError("model returned empty content")
    try:
        payload = json.loads(content)
    except ValueError as exc:
        raise ValueError(f"response was not JSON: {exc}") from exc
    try:
        return AgentSummary.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"response did not match the summary schema: {exc}") from exc


async def run_agent_summary(task_text: str, system_text: str, model_name: str) -> AgentSummary:
    """Run the agent once and return the model-authored summary only."""

    url = native_chat_url()
    num_ctx = configured_num_ctx()
    output_schema = AgentSummary.model_json_schema()

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": task_text},
    ]

    tool_calls_used = 0
    validation_retries = 0
    last_validation_error = ""

    for _ in range(MAX_TURNS):
        message = await chat_once(model_name, messages, output_schema, url, num_ctx)
        tool_calls = message.get("tool_calls") or []

        if tool_calls:
            messages.append(message)
            for call in tool_calls:
                if tool_calls_used >= TOOL_CALL_LIMIT:
                    raise ToolCallLimitExceeded(
                        f"Agent exceeded the {TOOL_CALL_LIMIT} successful tool call limit"
                    )
                tool_calls_used += 1
                name, result = execute_tool_call(call)
                messages.append({"role": "tool", "tool_name": name, "content": result})
            continue

        try:
            return parse_summary(message.get("content") or "")
        except ValueError as exc:
            last_validation_error = str(exc)
            if validation_retries >= OUTPUT_RETRIES:
                raise OutputValidationError(
                    f"Exceeded maximum retries ({OUTPUT_RETRIES}) for output validation: "
                    f"{last_validation_error}"
                ) from exc
            validation_retries += 1
            messages.append(message)
            # An empty reply usually means the model considers the conversation
            # finished, so the retry has to give it something to actually do.
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "That reply was not usable: "
                        f"{last_validation_error}. Reply with a single JSON object "
                        'matching {"summary": "<your summary>"} and nothing else.'
                    ),
                }
            )

    raise OutputValidationError(
        f"Agent did not produce a summary within {MAX_TURNS} turns. "
        f"Last validation error: {last_validation_error or 'none'}"
    )

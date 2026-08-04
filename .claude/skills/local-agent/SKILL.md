---
name: local-agent
description: Run a single local ollama-backed agent loop in Python and get one structured JSON result back. Use this when you want one local model invocation to read, write, edit, run shell commands, or web-search autonomously inside `scripts/run.py` instead of coordinating tool calls turn by turn in Claude. Do not use it together with `ollama-coordinator`.
---

# Local Agent

`local-agent` supersedes `ollama-coordinator`. Do not use the two skills together.

Let `DIR` be **this skill's own directory** — the folder containing this `SKILL.md`.
Resolve it from where you loaded this file; do not assume a repository location,
since this skill is copied between checkouts.

Invoke only:

```text
python DIR/scripts/run.py --task <value> --system <value> [--model <name>] [--endpoint <url>]
```

`run.py` is the only Claude-facing interface. Always run the copy that sits beside
this `SKILL.md` — running another checkout's copy silently tests the wrong code.

## When To Use It

Use this skill when you want one local ollama-backed agent run to complete a task inside Python and return one compact JSON object instead of a tool-call transcript.

## Arguments

| Flag | Required | Default | Meaning |
|------|----------|---------|---------|
| `--task` | yes | none | Task text, or an existing UTF-8 file path whose contents become the task |
| `--system` | yes | none | System prompt text, or an existing UTF-8 file path whose contents become the prompt |
| `--model` | no | `ornith:9b` | Ollama model name |
| `--endpoint` | no | `http://localhost:11434/v1` | Ollama base URL; applied by setting `OLLAMA_BASE_URL` before agent construction |

## Path-Or-Literal Rule

`--task` and `--system` use the same rule:

1. If `Path(value).is_file()` is true, the file is read as UTF-8 and a UTF-8 BOM is stripped if present.
2. Otherwise the raw value is used as the literal text.
3. Empty or whitespace-only resolved text is an error.

Implications:

- Existing file path wins over literal interpretation.
- A directory path is treated as literal text.
- A missing path is treated as literal text.
- A non-UTF-8 file fails honestly.
- A zero-byte file resolves to empty text and fails.
- A literal string identical to an existing file path cannot be forced to stay literal.

For long task text or long system prompts, write the text to a temp file and pass the path instead of embedding large content directly on the command line.

## System Prompt Guidance

The system prompt is supplied by the caller on every invocation. It is not stored in this repository.

Compose it so the local model:

- focuses on the concrete task you are delegating
- keeps its final output to a concise summary
- remembers that `summary` is the only model-owned output field
- uses tools only when needed

## Returned JSON

Every invocation prints exactly one JSON object to stdout, including CLI argument failures, runtime failures, and success.

```json
{
  "status": "success|error",
  "summary": "string",
  "files_touched": ["absolute/path"],
  "commands_run": ["exact command"],
  "error_type": "string or null",
  "error_message": "string or null",
  "endpoint_used": "string",
  "model_used": "string",
  "context_length_ceiling": "integer or null",
  "context_length_active": "integer or null"
}
```

Notes:

- On success, `summary` comes from the model.
- On failure, `summary` is assembled in Python by `run.py`.
- `files_touched` and `commands_run` come from Python runtime logging, never from the model.
- Failure output still uses the same JSON shape.
- `context_length_ceiling` is the model's architectural maximum, read from `POST /api/show` → `model_info["<arch>.context_length"]`. Null if the query fails.
- `context_length_active` is the effective window actually in use, read from `GET /api/ps` → `models[*].context_length` (field name confirmed live against ornith:9b). Null if the model is not yet loaded at preflight time or the query fails.
- A mismatch between the two (e.g. ceiling 262144, active 4096) means the server's `OLLAMA_CONTEXT_LENGTH` is constraining the window.

## Bounds

- Maximum successful tool calls: `15`, enforced with `UsageLimits(tool_calls_limit=15)`
- Structured-output validation retries: `2`
- Overall run timeout: `600` seconds

Bound-related failures use distinct `error_type` values:

- `tool_call_limit_exceeded`
- `structured_output_validation_failed`
- `overall_timeout_exceeded`
- `context_overflow`

Preflight failures use:

- `endpoint_unreachable`
- `model_not_found`

Other failure types use:

- `invalid_arguments`
- `input_resolution_failed`
- `agent_run_failed`

### Distinguishing context overflow from schema validation failure

`structured_output_validation_failed` fires when pydantic-ai exhausts its 2 output-validation retries. Context overflow is one possible root cause: when the model's context window is full, ollama truncates the response and the model produces empty or malformed output, which triggers the same retry path.

`context_overflow` fires for any other `UnexpectedModelBehavior` (e.g. the model returns a completely empty response before retries are exhausted). When `structured_output_validation_failed` occurs and `context_length_active` is known, the `error_message` includes the active and ceiling values plus a hint to check `OLLAMA_CONTEXT_LENGTH`.

### Context window

The effective context window is a **server-side property**, not a client-side one. The only way to change it over the `/v1` endpoint is to set `OLLAMA_CONTEXT_LENGTH` in the server's environment before starting ollama.

| Value | Source | Field in JSON |
|-------|--------|--------------|
| Model ceiling | `POST /api/show` → `model_info["<arch>.context_length"]` | `context_length_ceiling` |
| Effective (in-use) | `GET /api/ps` → `models[*].context_length` | `context_length_active` |

If `OLLAMA_CONTEXT_LENGTH` is not set, ollama defaults to a small window (4096 for ornith:9b as observed). The model ceiling (e.g. 262144) is the architectural maximum; the effective window may be far smaller. A `context_length_active` value that is much smaller than `context_length_ceiling` is a reliable indicator that `OLLAMA_CONTEXT_LENGTH` should be set explicitly.

## Timeout Limitation

The overall timeout uses asyncio cancellation, so the agent coroutine is cancelled at await points when the 600 second budget expires.

Accepted limit:

- A synchronous tool that is already executing inside a worker thread cannot be interrupted by asyncio cancellation. In practice that residual window is bounded by the tool's own timeout: `run_command` is `120` seconds and `web_search` is `30` seconds.

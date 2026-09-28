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
python DIR/scripts/run.py --task <value> --system <value> [--model <name>] [--endpoint <url>] [--num-ctx <int>]
python DIR/scripts/run.py --status
python DIR/scripts/run.py --configure [--set-host <ip-or-url>] [--set-model <name>] [--set-python <path|none>]
```

`run.py` is the only Claude-facing interface. Always run the copy that sits beside
this `SKILL.md` — running another checkout's copy silently tests the wrong code.

## Configuration

Settings live in `DIR/config.json` and persist between runs. Nothing is guessed:
an unconfigured skill reports `needs_configuration` rather than picking for you.

| Key | Meaning | Default |
|-----|---------|---------|
| `ollama_host` | Which ollama to talk to — local daemon or a remote box | `http://localhost:11434` |
| `model` | Model to run | none; **must be chosen** |
| `python` | Interpreter to execute under. `null` means "whatever is running now" | `null` |

The host is either localhost or an address you supply — the skill never scans the
network. `--set-host` accepts a bare IP (`192.168.1.5`), a `host:port`, or a full
URL; the port defaults to `11434` and any path (including a legacy `/v1`) is
discarded.

If `python` is set and differs from the running interpreter, `run.py` re-executes
itself under it as a subprocess and forwards its output, so the dependency check
and the run both happen on the interpreter that matters. `LOCAL_AGENT_REEXEC`
guards against a loop.

### The skill never prompts — you do

No human runs `run.py`. The caller is always an agent harness, so a blocked run
does not read stdin; it returns the question, the options, and the command that
records the answer. Take that to the user with your ask-user tool, then re-invoke.

```text
run  →  "needs_configuration": true
        "configuration_required": {
          "field": "model",
          "question": "Which ollama model should the local agent use on http://localhost:11434?",
          "options": [{"value": "ornith:9b", "label": "ornith:9b", "description": ""}],
          "allow_custom": false,
          "resolve_command": ["<python>", "<run.py>", "--configure", "--set-model", "<value>"]
        }
  →  ask the user, using `options` as the choices
  →  run `resolve_command` with their answer substituted for <value>
  →  re-run the original command
```

- `field` is what must be decided: `model`, `ollama_host`, `python`, or `dependencies`.
- `options` are ready to become the choices you offer. Never invent one that is not listed.
- `allow_custom` is true when free text is meaningful — a host address, or a model name on an unreachable server. Offer a write-in only then.
- `resolve_command` is literal except for `<value>`.

**Never pick on the user's behalf**, even when only one option exists. Choosing
the model is the decision this design exists to surface.

### `--status`

`run.py --status` reports interpreter, dependencies, host reachability, and the
configured model without running or changing anything. It returns the same
`configuration_required` block for the first blocker a real run would hit, in the
order a run hits them. Use it to orient before asking the user anything.

## Dependencies

Declared in `DIR/requirements.txt` and checked before every run. Missing packages
produce `missing_dependencies` with the exact install command, instead of an
import traceback.

```text
<python> -m pip install -r DIR/requirements.txt
```

## When To Use It

Use this skill when you want one local ollama-backed agent run to complete a task inside Python and return one compact JSON object instead of a tool-call transcript.

## Arguments

| Flag | Required | Default | Meaning |
|------|----------|---------|---------|
| `--task` | yes | none | Task text, or an existing UTF-8 file path whose contents become the task |
| `--system` | yes | none | System prompt text, or an existing UTF-8 file path whose contents become the prompt |
| `--model` | no | configured `model` | Ollama model name for this run only; does not change `config.json` |
| `--endpoint` | no | configured `ollama_host` | Ollama base URL for this run only; applied by setting `OLLAMA_BASE_URL`. Any path on it is discarded — the agent talks to `/api/chat` on the same host |
| `--num-ctx` | no | server default | Context window for this run, in tokens. Omit to inherit the server's `OLLAMA_CONTEXT_LENGTH`. Passed through `OLLAMA_NUM_CTX` |

## Path-Or-Literal Rule

`--task` and `--system` use the same rule:

1. If `Path(value).is_file()` is true, the file is read as UTF-8 and a UTF-8 BOM is stripped if present.
2. Otherwise, if the value is **shaped like a path**, it is an error — see below.
3. Otherwise the raw value is used as the literal text.
4. Empty or whitespace-only resolved text is an error.

A value is path-shaped when it is single-line and either ends in `.txt`, `.md`,
`.prompt`, `.json`, `.yaml`, `.yml`, or is rooted (`/…`, `C:\…`, `./…`, `../…`,
`~/…`). Prose is unaffected: `answer yes/no` stays literal because a bare
separator is not enough.

Implications:

- Existing file path wins over literal interpretation.
- A path-shaped value that does not resolve **fails loudly** with `input_resolution_failed`. It is not sent to the model.
- A directory path is an error for the same reason.
- A non-UTF-8 file fails honestly.
- A zero-byte file resolves to empty text and fails.
- A literal string identical to an existing file path cannot be forced to stay literal.

Rule 2 exists because the permissive version was worse than useless: a mistyped
path was handed to the model *as its prompt*, and the run looked like a model
failure rather than a typo.

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
  "context_length_active": "integer or null",
  "needs_configuration": "boolean",
  "available_models": ["model name"],
  "configuration_required": "object or null"
}
```

Notes:

- On success, `summary` comes from the model.
- On failure, `summary` is assembled in Python by `run.py`.
- `files_touched` and `commands_run` come from Python runtime logging, never from the model.
- Failure output still uses the same JSON shape.
- `context_length_ceiling` is the model's architectural maximum, read from `POST /api/show` → `model_info["<arch>.context_length"]`. Null if the query fails.
- `context_length_active` is the effective window actually in use, read from `GET /api/ps` → `models[*].context_length` (field name confirmed live against ornith:9b). It is re-read **after** the run, not only at preflight — on a cold start the model is not loaded yet, so the preflight value is null exactly when it would be most useful. Still null if the query fails or the model unloaded immediately.
- `needs_configuration` is true whenever `configuration_required` is present. Surface the question to the user rather than retrying.
- `configuration_required` is the decision to put to the user — see "The skill never prompts". Null on a healthy run.
- `available_models` is populated on a best-effort basis when a choice is needed. Empty means the host could not be listed, which usually means it is unreachable.
- A mismatch between the two (e.g. ceiling 262144, active 4096) means the effective window is being constrained by `--num-ctx` or by the server's `OLLAMA_CONTEXT_LENGTH`.

## Bounds

- Maximum successful tool calls: `15`, counted in the agent loop and enforced before each call is executed
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

Configuration and environment failures use (all carry `needs_configuration: true`):

- `missing_dependencies`
- `model_not_configured`
- `invalid_configuration`

Other failure types use:

- `invalid_arguments`
- `input_resolution_failed`
- `agent_run_failed`
- `internal_error` — a last-resort wrapper so an unanticipated exception is still reported as JSON rather than a traceback

### Distinguishing context overflow from schema validation failure

`structured_output_validation_failed` fires when the agent exhausts its 2 output-validation retries — the model's reply was empty, not JSON, or did not match the summary schema. Context overflow is one possible root cause: when the window is full, ollama truncates the response and the model produces empty or malformed output, which lands on the same retry path.

`context_overflow` fires when ollama returns a body with no assistant message at all. When `structured_output_validation_failed` occurs and `context_length_active` is known, the `error_message` includes the active and ceiling values plus a hint to raise the window.

### Context window

The window can be set **per run** with `--num-ctx`, because the agent uses ollama's native API. Precedence, all measured against a live server:

| How | Honoured? |
|-----|-----------|
| `--num-ctx` on this CLI (native `options.num_ctx`) | Yes — and it holds for every turn of the conversation |
| `OLLAMA_CONTEXT_LENGTH` in the server environment | Yes — the default when `--num-ctx` is omitted |
| `num_ctx` sent over the OpenAI-compatible `/v1` endpoint | **No** — accepted with HTTP 200 and silently discarded |

That last row is why this skill does not use `/v1`. It also means a `num_ctx` set by a separate native call does not survive a `/v1` request, which reloads the model at the server default.

| Value | Source | Field in JSON |
|-------|--------|--------------|
| Model ceiling | `POST /api/show` → `model_info["<arch>.context_length"]` | `context_length_ceiling` |
| Effective (in-use) | `GET /api/ps` → `models[*].context_length` | `context_length_active` |

If neither `--num-ctx` nor `OLLAMA_CONTEXT_LENGTH` is set, ollama falls back to a small window (4096 for ornith:9b as observed). The model ceiling (e.g. 262144) is the architectural maximum; raising the effective window costs KV-cache memory, so it is a choice rather than a free win. `context_length_active` is null when the model was not yet loaded at preflight time.

### Why the native API

The agent talks to `/api/chat`, not the OpenAI-compatible `/v1` shim. Beyond `num_ctx`, the deciding reason is that `/v1` serialises a reasoning-only assistant turn as `content: null`, and ollama then rejects its own output on the following request with `400 invalid message content type: <nil>`. Natively the same turn carries `content: ''` and the failure cannot occur. Native `format` also takes a JSON schema and is grammar-constrained, and it coexists with `tools` — the model still emits tool calls while being held to the output schema.

## Timeout Limitation

The overall timeout uses asyncio cancellation, so the agent coroutine is cancelled at await points when the 600 second budget expires.

Accepted limit:

- A synchronous tool that is already executing inside a worker thread cannot be interrupted by asyncio cancellation. In practice that residual window is bounded by the tool's own timeout: `run_command` is `120` seconds and `web_search` is `30` seconds.

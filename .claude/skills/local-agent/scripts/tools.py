"""Tool implementations for the local-agent skill."""

from __future__ import annotations

import contextlib
import contextvars
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator


@dataclass
class RuntimeLog:
    """In-memory execution log used to assemble RunResult provenance."""

    files_touched: list[str] = field(default_factory=list)
    commands_run: list[str] = field(default_factory=list)
    _seen_files: set[str] = field(default_factory=set)

    def record_file(self, path: str) -> str:
        absolute = str(Path(path).resolve())
        if absolute not in self._seen_files:
            self._seen_files.add(absolute)
            self.files_touched.append(absolute)
        return absolute

    def record_command(self, command: str) -> None:
        self.commands_run.append(command)


_RUNTIME_LOG: contextvars.ContextVar[RuntimeLog | None] = contextvars.ContextVar(
    "local_agent_runtime_log",
    default=None,
)


@contextlib.contextmanager
def install_runtime_log(runtime_log: RuntimeLog) -> Iterator[RuntimeLog]:
    """Install a run-local runtime log for the duration of a block."""

    token = _RUNTIME_LOG.set(runtime_log)
    try:
        yield runtime_log
    finally:
        _RUNTIME_LOG.reset(token)


def _record_file(path: str) -> str:
    absolute = str(Path(path).resolve())
    runtime_log = _RUNTIME_LOG.get()
    if runtime_log is not None:
        return runtime_log.record_file(path)
    return absolute


def _record_command(command: str) -> None:
    runtime_log = _RUNTIME_LOG.get()
    if runtime_log is not None:
        runtime_log.record_command(command)


def _json_result(**payload: object) -> str:
    return json.dumps(payload, ensure_ascii=True)


def read_file(path: str) -> str:
    """Read a UTF-8 text file and return its contents or a structured error string."""

    absolute = _record_file(path)
    try:
        with open(absolute, "r", encoding="utf-8", newline="") as handle:
            content = handle.read()
    except FileNotFoundError:
        return _json_result(status="error", error=f"File not found: {absolute}")
    except UnicodeDecodeError as exc:
        return _json_result(status="error", error=f"File is not valid UTF-8: {absolute}: {exc}")
    except OSError as exc:
        return _json_result(status="error", error=f"Failed to read file {absolute}: {exc}")
    return _json_result(status="success", path=absolute, content=content)


def write_file(path: str, content: str) -> str:
    """Write UTF-8 text to a file, creating parent directories, and report size details."""

    absolute = _record_file(path)
    target = Path(absolute)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
    except OSError as exc:
        return _json_result(status="error", error=f"Failed to write file {absolute}: {exc}")
    return _json_result(
        status="success",
        path=absolute,
        bytes_written=len(content.encode("utf-8")),
        characters_written=len(content),
    )


def edit_file(path: str, old: str, new: str) -> str:
    """Replace exactly one occurrence in a UTF-8 text file or return a structured error string."""

    absolute = _record_file(path)
    try:
        with open(absolute, "r", encoding="utf-8", newline="") as handle:
            original = handle.read()
    except FileNotFoundError:
        return _json_result(status="error", error=f"File not found: {absolute}")
    except UnicodeDecodeError as exc:
        return _json_result(status="error", error=f"File is not valid UTF-8: {absolute}: {exc}")
    except OSError as exc:
        return _json_result(status="error", error=f"Failed to read file {absolute}: {exc}")

    match_count = original.count(old)
    if match_count == 0:
        return _json_result(status="error", error=f"Text to replace was not found in {absolute}")
    if match_count > 1:
        return _json_result(
            status="error",
            error=f"Text to replace matched {match_count} times in {absolute}; provide more context",
        )

    updated = original.replace(old, new, 1)

    try:
        with open(absolute, "w", encoding="utf-8", newline="") as handle:
            handle.write(updated)
    except OSError as exc:
        return _json_result(status="error", error=f"Failed to write file {absolute}: {exc}")

    return _json_result(status="success", path=absolute, replacements=1)


def run_command(command: str) -> str:
    """Run a shell command with a 120 second timeout and return exit code plus combined output."""

    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        _record_command(command)
        output, _ = process.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        if process is not None:
            process.kill()
            output, _ = process.communicate()
        else:
            output = ""
        return _json_result(
            status="error",
            command=command,
            error="Command timed out after 120 seconds",
            exit_code=None,
            output=output,
        )
    except OSError as exc:
        return _json_result(status="error", command=command, error=f"Failed to start command: {exc}")

    return _json_result(
        status="success" if process.returncode == 0 else "error",
        command=command,
        exit_code=process.returncode,
        output=output,
    )


def _default_ddgs_factory() -> Callable[[], object]:
    from ddgs import DDGS

    return DDGS


DDGS_FACTORY: Callable[[], object] = _default_ddgs_factory


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web with ddgs and return title, URL, and snippet for up to max_results hits."""

    try:
        ddgs_class = DDGS_FACTORY()
        with ddgs_class(timeout=30) as client:
            results = list(client.text(query, max_results=max_results))
    except Exception as exc:
        return _json_result(status="error", error=f"Web search failed: {exc}")

    if not results:
        return _json_result(status="success", query=query, results=[], message="No results found")

    normalized_results = []
    for item in results:
        normalized_results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", ""),
            }
        )
    return _json_result(status="success", query=query, results=normalized_results)

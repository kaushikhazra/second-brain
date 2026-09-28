"""Unit tests for run.py."""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import unittest
from pathlib import Path
from unittest import mock

import agent
import config
import run
import tools


class TestResolveTextArgument(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)

    def test_existing_file_uses_file_contents(self):
        path = Path(self.tempdir.name, "task.txt")
        path.write_text("from file", encoding="utf-8")
        self.assertEqual(run.resolve_text_argument(str(path), "--task"), "from file")

    def test_missing_path_is_an_error_not_a_prompt(self):
        # A typo'd path used to be handed to the model as its task text, which
        # silently burned whole runs.
        missing = str(Path(self.tempdir.name, "missing.txt"))
        with self.assertRaisesRegex(run.ResolverError, "looks like a file path"):
            run.resolve_text_argument(missing, "--task")

    def test_directory_is_an_error(self):
        directory = Path(self.tempdir.name, "folder")
        directory.mkdir()
        with self.assertRaisesRegex(run.ResolverError, "looks like a file path"):
            run.resolve_text_argument(str(directory), "--task")

    def test_prose_containing_a_slash_is_still_literal(self):
        for literal in ("answer yes/no", "use the a/b test", "read C:/ and report back"):
            with self.subTest(literal=literal):
                self.assertEqual(run.resolve_text_argument(literal, "--task"), literal)

    def test_path_shapes_are_recognised(self):
        for value in ("./task.txt", "../a/b", "~/prompts/x", "/etc/thing", "notes.md"):
            with self.subTest(value=value):
                self.assertTrue(run.looks_like_a_path(value))

    def test_prose_shapes_are_not_paths(self):
        for value in ("Summarise the findings.", "yes/no", "line 1\nline 2", ""):
            with self.subTest(value=value):
                self.assertFalse(run.looks_like_a_path(value))

    def test_multiline_literal_is_allowed(self):
        literal = "line 1\nline 2"
        self.assertEqual(run.resolve_text_argument(literal, "--task"), literal)

    def test_empty_value_errors(self):
        with self.assertRaises(run.ResolverError):
            run.resolve_text_argument("", "--task")

    def test_zero_byte_file_errors(self):
        path = Path(self.tempdir.name, "empty.txt")
        path.write_bytes(b"")
        with self.assertRaises(run.ResolverError):
            run.resolve_text_argument(str(path), "--task")

    def test_non_utf8_file_errors(self):
        path = Path(self.tempdir.name, "bad.bin")
        path.write_bytes(b"\xff\xfe\x00")
        with self.assertRaises(run.ResolverError):
            run.resolve_text_argument(str(path), "--task")

    def test_utf8_bom_is_stripped(self):
        path = Path(self.tempdir.name, "bom.txt")
        path.write_bytes(b"\xef\xbb\xbfhello")
        self.assertEqual(run.resolve_text_argument(str(path), "--task"), "hello")


class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        # Isolate from whatever config.json happens to exist on this machine,
        # and from whether this interpreter really has the dependencies.
        self.config = {
            "python": None,
            "ollama_host": run.DEFAULT_ENDPOINT,
            "model": run.DEFAULT_MODEL,
        }
        for target, value in (
            ("load_config", lambda *a, **k: dict(self.config)),
            ("missing_dependencies", lambda: []),
        ):
            patcher = mock.patch.object(run, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _invoke_main(self, args: list[str]) -> tuple[int, dict, str]:
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        with (
            contextlib.redirect_stdout(stdout_buffer),
            contextlib.redirect_stderr(stderr_buffer),
        ):
            code = run.main(args)
        stdout_lines = stdout_buffer.getvalue().splitlines()
        self.assertEqual(len(stdout_lines), 1)
        return code, json.loads(stdout_lines[0]), stderr_buffer.getvalue()

    def test_success_assembles_run_result_from_model_summary_and_runtime_provenance(
        self,
    ):
        first_path = Path(self.tempdir.name, "first.txt")
        second_path = Path(self.tempdir.name, "second.txt")
        command = f"{sys.executable} -c \"print('hi')\""

        async def runner(
            task_text: str, system_text: str, model_name: str
        ) -> agent.AgentSummary:
            tools.write_file(str(first_path), "alpha")
            tools.read_file(str(first_path))
            tools.write_file(str(second_path), "beta")
            tools.run_command(command)
            return agent.AgentSummary(summary=f"{task_text} via {model_name}")

        with (
            mock.patch.object(run, "RUNNER", side_effect=runner),
            mock.patch.object(
                run,
                "perform_preflight",
                return_value=run.PreflightResult(["ornith:9b"]),
            ),
        ):
            _, payload, stderr = self._invoke_main(
                ["--task", "Task", "--system", "System"]
            )

        self.assertEqual(stderr, "")
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["summary"], "Task via ornith:9b")
        self.assertEqual(
            payload["files_touched"],
            [str(first_path.resolve()), str(second_path.resolve())],
        )
        self.assertEqual(payload["commands_run"], [command])
        self.assertIsNone(payload["error_type"])
        self.assertEqual(payload["endpoint_used"], run.DEFAULT_ENDPOINT)
        self.assertEqual(payload["model_used"], run.DEFAULT_MODEL)

    def test_endpoint_override_sets_environment_before_runner(self):
        observed: dict[str, str | None] = {}

        async def runner(
            task_text: str, system_text: str, model_name: str
        ) -> agent.AgentSummary:
            observed["endpoint"] = os.environ.get("OLLAMA_BASE_URL")
            observed["model"] = model_name
            return agent.AgentSummary(summary="ok")

        with (
            mock.patch.object(run, "RUNNER", side_effect=runner),
            mock.patch.object(
                run,
                "perform_preflight",
                return_value=run.PreflightResult(["custom:7b"]),
            ),
        ):
            _, payload, _ = self._invoke_main(
                [
                    "--task",
                    "Task",
                    "--system",
                    "System",
                    "--endpoint",
                    "http://localhost:23456/v1",
                    "--model",
                    "custom:7b",
                ]
            )

        self.assertEqual(observed["endpoint"], "http://localhost:23456/v1")
        self.assertEqual(observed["model"], "custom:7b")
        self.assertEqual(payload["endpoint_used"], "http://localhost:23456/v1")
        self.assertEqual(payload["model_used"], "custom:7b")

    def test_preflight_connection_failure_returns_endpoint_unreachable(self):
        with mock.patch.object(
            run, "perform_preflight", side_effect=ConnectionError("connection refused")
        ):
            _, payload, stderr = self._invoke_main(
                ["--task", "Task", "--system", "System"]
            )

        self.assertEqual(stderr, "")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_type"], "endpoint_unreachable")
        self.assertIn("connection refused", payload["error_message"])

    def test_preflight_missing_model_returns_model_not_found(self):
        with mock.patch.object(
            run,
            "perform_preflight",
            side_effect=LookupError(
                "Requested model 'ornith:9b' was not found. Available models: llama3.2, qwen2.5"
            ),
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_type"], "model_not_found")
        self.assertIn("Available models: llama3.2, qwen2.5", payload["error_message"])

    def test_usage_limit_exception_maps_to_tool_call_limit_exceeded(self):
        async def raising_runner(
            task_text: str, system_text: str, model_name: str
        ) -> agent.AgentSummary:
            raise agent.ToolCallLimitExceeded("tool call budget exceeded")

        with (
            mock.patch.object(
                run,
                "perform_preflight",
                return_value=run.PreflightResult(["ornith:9b"]),
            ),
            mock.patch.object(run, "RUNNER", side_effect=raising_runner),
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["error_type"], "tool_call_limit_exceeded")

    def test_output_validation_exception_maps_to_structured_output_validation_failed(
        self,
    ):
        async def raising_runner(
            task_text: str, system_text: str, model_name: str
        ) -> agent.AgentSummary:
            raise agent.OutputValidationError(
                "Exceeded maximum retries (2) for output validation"
            )

        with (
            mock.patch.object(
                run,
                "perform_preflight",
                return_value=run.PreflightResult(["ornith:9b"]),
            ),
            mock.patch.object(run, "RUNNER", side_effect=raising_runner),
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["error_type"], "structured_output_validation_failed")

    def test_output_validation_with_active_context_includes_hint_in_message(self):
        async def raising_runner(
            task_text: str, system_text: str, model_name: str
        ) -> agent.AgentSummary:
            raise agent.OutputValidationError(
                "Exceeded maximum retries (2) for output validation"
            )

        with (
            mock.patch.object(
                run,
                "perform_preflight",
                return_value=run.PreflightResult(
                    ["ornith:9b"],
                    context_length_ceiling=262144,
                    context_length_active=4096,
                ),
            ),
            mock.patch.object(run, "RUNNER", side_effect=raising_runner),
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["error_type"], "structured_output_validation_failed")
        self.assertIn("4096", payload["error_message"])
        self.assertIn("262144", payload["error_message"])
        self.assertEqual(payload["context_length_active"], 4096)
        self.assertEqual(payload["context_length_ceiling"], 262144)

    def test_unexpected_model_behavior_maps_to_context_overflow(self):
        async def raising_runner(
            task_text: str, system_text: str, model_name: str
        ) -> agent.AgentSummary:
            raise agent.ModelBehaviorError("model returned empty response")

        with (
            mock.patch.object(
                run,
                "perform_preflight",
                return_value=run.PreflightResult(["ornith:9b"]),
            ),
            mock.patch.object(run, "RUNNER", side_effect=raising_runner),
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["error_type"], "context_overflow")
        self.assertIn("model returned empty response", payload["error_message"])

    def test_overall_timeout_prevents_late_file_side_effects(self):
        late_path = Path(self.tempdir.name, "late.txt")

        async def slow_runner(
            task_text: str, system_text: str, model_name: str
        ) -> agent.AgentSummary:
            await asyncio.sleep(0.2)
            tools.write_file(str(late_path), "late write")
            return agent.AgentSummary(summary="late")

        with (
            mock.patch.object(
                run,
                "perform_preflight",
                return_value=run.PreflightResult(["ornith:9b"]),
            ),
            mock.patch.object(run, "RUNNER", side_effect=slow_runner),
            mock.patch.object(run, "OVERALL_TIMEOUT_SECONDS", 0.01),
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["error_type"], "overall_timeout_exceeded")
        time.sleep(0.1)
        self.assertFalse(late_path.exists())

    def test_timed_out_run_late_activity_does_not_leak_into_next_run_files_touched(
        self,
    ):
        late_path = Path(self.tempdir.name, "late.txt")
        second_path = Path(self.tempdir.name, "second.txt")
        late_write_finished = threading.Event()

        async def timed_out_runner(
            task_text: str, system_text: str, model_name: str
        ) -> agent.AgentSummary:
            run_context = contextvars.copy_context()

            def late_write() -> None:
                time.sleep(0.05)
                run_context.run(tools.write_file, str(late_path), "late write")
                late_write_finished.set()

            threading.Thread(target=late_write, daemon=True).start()
            await asyncio.sleep(0.2)
            return agent.AgentSummary(summary="too late")

        async def second_runner(
            task_text: str, system_text: str, model_name: str
        ) -> agent.AgentSummary:
            await asyncio.to_thread(late_write_finished.wait, 0.5)
            tools.write_file(str(second_path), "second write")
            return agent.AgentSummary(summary="second")

        with (
            mock.patch.object(
                run,
                "perform_preflight",
                return_value=run.PreflightResult(["ornith:9b"]),
            ),
            mock.patch.object(run, "RUNNER", side_effect=timed_out_runner),
            mock.patch.object(run, "OVERALL_TIMEOUT_SECONDS", 0.01),
        ):
            _, first_payload, _ = self._invoke_main(
                ["--task", "Task one", "--system", "System"]
            )

        with (
            mock.patch.object(
                run,
                "perform_preflight",
                return_value=run.PreflightResult(["ornith:9b"]),
            ),
            mock.patch.object(run, "RUNNER", side_effect=second_runner),
        ):
            _, second_payload, _ = self._invoke_main(
                ["--task", "Task two", "--system", "System"]
            )

        self.assertEqual(first_payload["error_type"], "overall_timeout_exceeded")
        self.assertTrue(late_write_finished.wait(1.0))
        self.assertEqual(second_payload["status"], "success")
        self.assertEqual(second_payload["files_touched"], [str(second_path.resolve())])
        self.assertTrue(late_path.exists())

    def test_generic_runner_failure_is_honest(self):
        async def raising_runner(
            task_text: str, system_text: str, model_name: str
        ) -> agent.AgentSummary:
            raise RuntimeError("boom")

        with (
            mock.patch.object(
                run,
                "perform_preflight",
                return_value=run.PreflightResult(["ornith:9b"]),
            ),
            mock.patch.object(run, "RUNNER", side_effect=raising_runner),
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["error_type"], "agent_run_failed")
        self.assertIn("boom", payload["error_message"])

    def test_input_resolution_failure_returns_error_json(self):
        with mock.patch.object(run, "perform_preflight") as preflight:
            _, payload, _ = self._invoke_main(["--task", "   ", "--system", "System"])

        self.assertEqual(payload["error_type"], "input_resolution_failed")
        preflight.assert_not_called()

    def test_missing_required_flags_emit_single_json_and_keep_usage_off_stdout(self):
        code, payload, stderr = self._invoke_main([])

        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_type"], "invalid_arguments")
        self.assertIn(
            "the following arguments are required: --task, --system",
            payload["error_message"],
        )
        self.assertIn("usage: run.py", stderr)

    def test_missing_dependencies_are_reported_before_anything_runs(self):
        with (
            mock.patch.object(run, "missing_dependencies", lambda: ["ddgs"]),
            mock.patch.object(run, "perform_preflight") as preflight,
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["error_type"], "missing_dependencies")
        self.assertTrue(payload["needs_configuration"])
        self.assertIn("ddgs", payload["error_message"])
        preflight.assert_not_called()

    def test_unconfigured_model_asks_instead_of_guessing(self):
        self.config["model"] = None
        with (
            mock.patch.object(run, "list_available_models", lambda *a, **k: ["a:1", "b:2"]),
            mock.patch.object(run, "perform_preflight") as preflight,
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["error_type"], "model_not_configured")
        self.assertTrue(payload["needs_configuration"])
        self.assertEqual(payload["available_models"], ["a:1", "b:2"])
        preflight.assert_not_called()

    def test_unreachable_endpoint_offers_reconfiguration(self):
        with mock.patch.object(
            run, "perform_preflight", side_effect=ConnectionError("connection refused")
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["error_type"], "endpoint_unreachable")
        self.assertTrue(payload["needs_configuration"])
        self.assertIn("--set-host", payload["error_message"])

    def test_model_not_found_offers_the_available_models(self):
        with (
            mock.patch.object(
                run, "perform_preflight", side_effect=LookupError("Requested model missing")
            ),
            mock.patch.object(run, "list_available_models", lambda *a, **k: ["x:1"]),
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["error_type"], "model_not_found")
        self.assertTrue(payload["needs_configuration"])
        self.assertEqual(payload["available_models"], ["x:1"])

    def test_active_context_is_re_read_after_the_run(self):
        # Preflight sees null on a cold start because the model is not loaded
        # yet; the value is only observable afterwards.
        async def runner(task_text, system_text, model_name):
            return agent.AgentSummary(summary="ok")

        with (
            mock.patch.object(run, "RUNNER", side_effect=runner),
            mock.patch.object(
                run,
                "perform_preflight",
                return_value=run.PreflightResult(
                    ["ornith:9b"], context_length_ceiling=262144, context_length_active=None
                ),
            ),
            mock.patch.object(run, "_fetch_context_length_active", return_value=16384),
        ):
            _, payload, _ = self._invoke_main(["--task", "Task", "--system", "System"])

        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["context_length_active"], 16384)


class TestConfigureCommand(unittest.TestCase):
    """--configure must never prompt when there is no usable terminal."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.path = Path(self.tempdir.name, "config.json")
        self.stored = config.default_config()

        patcher = mock.patch.object(run, "load_config", lambda *a, **k: dict(self.stored))
        patcher.start()
        self.addCleanup(patcher.stop)
        saver = mock.patch.object(
            run, "save_config", lambda cfg, path=None: config.save_config(cfg, self.path)
        )
        saver.start()
        self.addCleanup(saver.stop)

    def _invoke(self, args: list[str]) -> dict:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            run.main(args)
        lines = buffer.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return json.loads(lines[0])

    def test_set_flags_are_persisted_without_prompting(self):
        with mock.patch.object(run, "list_available_models", lambda *a, **k: ["m:1"]):
            payload = self._invoke(
                ["--configure", "--set-host", "192.168.1.5", "--set-model", "m:1"]
            )

        self.assertEqual(payload["status"], "success")
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(saved["ollama_host"], "http://192.168.1.5:11434")
        self.assertEqual(saved["model"], "m:1")

    def test_unchosen_model_returns_a_question_and_never_prompts(self):
        # The caller is an agent harness, so a blocked run hands back the
        # question instead of trying to read stdin. An earlier version prompted
        # here and died with EOFError, emitting a traceback instead of JSON.
        with (
            mock.patch.object(run, "list_available_models", lambda *a, **k: ["m:1", "m:2"]),
            mock.patch("builtins.input", side_effect=AssertionError("must not prompt")),
        ):
            payload = self._invoke(["--configure"])

        self.assertEqual(payload["error_type"], "model_not_configured")
        self.assertTrue(payload["needs_configuration"])
        choice = payload["configuration_required"]
        self.assertEqual(choice["field"], "model")
        self.assertEqual([o["value"] for o in choice["options"]], ["m:1", "m:2"])
        self.assertIn("--set-model", choice["resolve_command"])

    def test_unreachable_host_asks_about_the_host_not_the_model(self):
        with mock.patch.object(run, "list_available_models", lambda *a, **k: []):
            payload = self._invoke(["--configure"])

        choice = payload["configuration_required"]
        self.assertEqual(choice["field"], "ollama_host")
        self.assertTrue(choice["allow_custom"])
        self.assertIn("--set-host", choice["resolve_command"])

    def test_setting_only_python_does_not_prompt_for_a_host(self):
        self.stored["model"] = "already:1"
        with (
            mock.patch.object(run, "list_available_models", lambda *a, **k: ["already:1"]),
            mock.patch("builtins.input", side_effect=AssertionError("must not prompt")),
        ):
            payload = self._invoke(["--configure", "--set-python", "none"])

        self.assertEqual(payload["status"], "success")
        self.assertIsNone(json.loads(self.path.read_text(encoding="utf-8"))["python"])

    def test_bad_host_is_reported_as_invalid_configuration(self):
        payload = self._invoke(["--configure", "--set-host", "ftp://nope"])

        self.assertEqual(payload["error_type"], "invalid_configuration")


class TestStatusCommand(unittest.TestCase):
    def setUp(self) -> None:
        self.stored = {
            "python": None,
            "ollama_host": run.DEFAULT_ENDPOINT,
            "model": "ornith:9b",
        }
        patcher = mock.patch.object(run, "load_config", lambda *a, **k: dict(self.stored))
        patcher.start()
        self.addCleanup(patcher.stop)

    def _invoke(self) -> dict:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            run.main(["--status"])
        lines = buffer.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return json.loads(lines[0])

    def test_a_question_always_sets_needs_configuration(self):
        # These two fields must never disagree, whichever code path builds the
        # result. --status built one directly and got this wrong.
        self.stored["model"] = None
        with (
            mock.patch.object(run, "missing_dependencies", lambda: []),
            mock.patch.object(run, "list_available_models", lambda *a, **k: ["ornith:9b"]),
        ):
            payload = self._invoke()

        self.assertIsNotNone(payload["configuration_required"])
        self.assertTrue(payload["needs_configuration"])

    def test_healthy_setup_reports_no_blocker(self):
        with (
            mock.patch.object(run, "missing_dependencies", lambda: []),
            mock.patch.object(run, "list_available_models", lambda *a, **k: ["ornith:9b"]),
        ):
            payload = self._invoke()

        self.assertEqual(payload["status"], "success")
        self.assertIsNone(payload["configuration_required"])
        self.assertFalse(payload["needs_configuration"])

    def test_status_never_mutates_config(self):
        with (
            mock.patch.object(run, "missing_dependencies", lambda: []),
            mock.patch.object(run, "list_available_models", lambda *a, **k: ["ornith:9b"]),
            mock.patch.object(run, "save_config", side_effect=AssertionError("must not write")),
        ):
            self._invoke()

    def test_blockers_are_reported_in_the_order_a_run_would_hit_them(self):
        # Dependencies come before host reachability, which comes before model.
        with (
            mock.patch.object(run, "missing_dependencies", lambda: ["ddgs"]),
            mock.patch.object(run, "list_available_models", lambda *a, **k: []),
        ):
            payload = self._invoke()

        self.assertEqual(payload["configuration_required"]["field"], "dependencies")

    def test_configured_model_absent_from_host_is_flagged(self):
        with (
            mock.patch.object(run, "missing_dependencies", lambda: []),
            mock.patch.object(run, "list_available_models", lambda *a, **k: ["other:1"]),
        ):
            payload = self._invoke()

        self.assertEqual(payload["configuration_required"]["field"], "model")
        self.assertEqual(payload["available_models"], ["other:1"])


class TestMainGuard(unittest.TestCase):
    def test_unexpected_exception_still_produces_one_json_object(self):
        buffer = io.StringIO()
        with (
            mock.patch.object(run, "main", side_effect=RuntimeError("kaboom")),
            contextlib.redirect_stdout(buffer),
        ):
            code = run.main_guarded([])

        lines = buffer.getvalue().splitlines()
        self.assertEqual(code, 0)
        self.assertEqual(len(lines), 1)
        payload = json.loads(lines[0])
        self.assertEqual(payload["error_type"], "internal_error")
        self.assertIn("kaboom", payload["error_message"])


class TestPreflight(unittest.TestCase):
    def test_build_tags_url_strips_endpoint_path(self):
        self.assertEqual(
            run._build_tags_url("http://localhost:11434/v1"),
            "http://localhost:11434/api/tags",
        )

    def test_perform_preflight_success(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = (
            b'{"models":[{"name":"ornith:9b"}]}'
        )
        with mock.patch.object(run.urllib.request, "urlopen", return_value=response):
            result = run.perform_preflight("http://localhost:11434/v1", "ornith:9b")

        self.assertEqual(result.available_models, ["ornith:9b"])

    def test_perform_preflight_connection_error(self):
        with mock.patch.object(
            run.urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")
        ):
            with self.assertRaises(ConnectionError):
                run.perform_preflight("http://localhost:11434/v1", "ornith:9b")

    def test_perform_preflight_missing_model_lists_available(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = (
            b'{"models":[{"name":"llama3.2"},{"name":"qwen2.5"}]}'
        )
        with mock.patch.object(run.urllib.request, "urlopen", return_value=response):
            with self.assertRaises(LookupError) as exc:
                run.perform_preflight("http://localhost:11434/v1", "ornith:9b")

        self.assertIn("Available models: llama3.2, qwen2.5", str(exc.exception))


class TestSkillContract(unittest.TestCase):
    def test_skill_md_documents_failure_summary_ownership_and_error_types(self):
        skill_path = Path(__file__).resolve().parents[1] / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "Every invocation prints exactly one JSON object to stdout", content
        )
        self.assertIn("On success, `summary` comes from the model.", content)
        self.assertIn(
            "On failure, `summary` is assembled in Python by `run.py`.", content
        )
        for error_type in (
            "invalid_arguments",
            "input_resolution_failed",
            "agent_run_failed",
            "endpoint_unreachable",
            "model_not_found",
            "tool_call_limit_exceeded",
            "structured_output_validation_failed",
            "overall_timeout_exceeded",
            "context_overflow",
            "missing_dependencies",
            "model_not_configured",
            "invalid_configuration",
            "internal_error",
        ):
            self.assertIn(error_type, content)

    def test_skill_md_documents_configuration_and_dependencies(self):
        skill_path = Path(__file__).resolve().parents[1] / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        for fragment in ("config.json", "--configure", "--set-host", "--set-model", "--set-python"):
            self.assertIn(fragment, content)

    def test_requirements_file_lists_every_checked_dependency(self):
        requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
        content = requirements.read_text(encoding="utf-8")

        for _, package in config.REQUIRED_PACKAGES:
            self.assertIn(package, content)


class TestCliScript(unittest.TestCase):
    def test_missing_required_flags_script_output_is_single_json_object(self):
        script = Path(__file__).with_name("run.py")
        completed = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=False,
        )

        stdout_lines = completed.stdout.splitlines()
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(len(stdout_lines), 1)
        payload = json.loads(stdout_lines[0])
        self.assertEqual(payload["error_type"], "invalid_arguments")
        self.assertIn("usage: run.py", completed.stderr)

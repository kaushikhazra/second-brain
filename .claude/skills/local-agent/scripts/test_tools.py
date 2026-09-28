"""Unit tests for tools.py."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import tools


class FakeDDGS:
    def __init__(self, timeout: int):
        self.timeout = timeout

    def __enter__(self) -> "FakeDDGS":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def text(self, query: str, max_results: int = 5):
        return [
            {"title": "Result 1", "href": "https://example.com/1", "body": "Snippet 1"},
            {"title": "Result 2", "href": "https://example.com/2", "body": "Snippet 2"},
        ][:max_results]


class TestTools(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.runtime_log = tools.RuntimeLog()
        self.runtime_log_scope = tools.install_runtime_log(self.runtime_log)
        self.runtime_log_scope.__enter__()
        self.addCleanup(self.runtime_log_scope.__exit__, None, None, None)
        self.addCleanup(self.tempdir.cleanup)

    def test_read_file_success_records_absolute_path(self):
        path = Path(self.tempdir.name, "read.txt")
        path.write_text("hello", encoding="utf-8", newline="")

        result = json.loads(tools.read_file(str(path)))

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["content"], "hello")
        self.assertEqual(self.runtime_log.files_touched, [str(path.resolve())])

    def test_read_file_missing_is_structured_error_and_logged(self):
        path = Path(self.tempdir.name, "missing.txt")

        result = json.loads(tools.read_file(str(path)))

        self.assertEqual(result["status"], "error")
        self.assertIn("File not found", result["error"])
        self.assertEqual(self.runtime_log.files_touched, [str(path.resolve())])

    def test_read_file_non_utf8_is_structured_error(self):
        path = Path(self.tempdir.name, "binary.bin")
        path.write_bytes(b"\xff\xfe\x00")

        result = json.loads(tools.read_file(str(path)))

        self.assertEqual(result["status"], "error")
        self.assertIn("not valid UTF-8", result["error"])

    def test_write_file_creates_parents_and_reports_sizes(self):
        path = Path(self.tempdir.name, "nested", "write.txt")

        result = json.loads(tools.write_file(str(path), "hello"))

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["bytes_written"], 5)
        self.assertEqual(result["characters_written"], 5)
        self.assertEqual(path.read_text(encoding="utf-8"), "hello")
        self.assertEqual(self.runtime_log.files_touched, [str(path.resolve())])

    def test_runtime_log_preserves_first_use_order_and_deduplicates_repeats(self):
        first_path = Path(self.tempdir.name, "first.txt")
        second_path = Path(self.tempdir.name, "second.txt")

        tools.write_file(str(first_path), "alpha")
        tools.read_file(str(first_path))
        tools.write_file(str(second_path), "beta")
        tools.edit_file(str(first_path), "alpha", "gamma")

        self.assertEqual(
            self.runtime_log.files_touched,
            [str(first_path.resolve()), str(second_path.resolve())],
        )

    def test_edit_file_success_preserves_crlf_newlines(self):
        path = Path(self.tempdir.name, "edit.txt")
        path.write_text("line1\r\nold\r\nline3\r\n", encoding="utf-8", newline="")

        result = json.loads(tools.edit_file(str(path), "old", "new"))

        self.assertEqual(result["status"], "success")
        with open(path, "r", encoding="utf-8", newline="") as handle:
            self.assertEqual(handle.read(), "line1\r\nnew\r\nline3\r\n")

    def test_edit_file_zero_match_errors(self):
        path = Path(self.tempdir.name, "edit-zero.txt")
        path.write_text("hello", encoding="utf-8")

        result = json.loads(tools.edit_file(str(path), "missing", "new"))

        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["error"])

    def test_edit_file_multi_match_errors(self):
        path = Path(self.tempdir.name, "edit-multi.txt")
        path.write_text("old old", encoding="utf-8")

        result = json.loads(tools.edit_file(str(path), "old", "new"))

        self.assertEqual(result["status"], "error")
        self.assertIn("matched 2 times", result["error"])

    def test_run_command_non_zero_exit_is_normal_result_and_logged(self):
        command = 'python -c "import sys; sys.stdout.write(\'oops\'); sys.exit(3)"'

        result = json.loads(tools.run_command(command))

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["exit_code"], 3)
        self.assertEqual(result["output"], "oops")
        self.assertEqual(self.runtime_log.commands_run, [command])

    def test_run_command_timeout_is_structured_error(self):
        fake_process = mock.Mock()
        fake_process.communicate.side_effect = [subprocess.TimeoutExpired("cmd", 120), ("late", None)]
        fake_process.returncode = None
        with mock.patch.object(tools.subprocess, "Popen", return_value=fake_process):
            result = json.loads(tools.run_command("slow command"))

        self.assertEqual(result["status"], "error")
        self.assertIn("timed out", result["error"])
        self.assertEqual(self.runtime_log.commands_run, ["slow command"])
        fake_process.kill.assert_called_once()

    def test_web_search_success(self):
        with mock.patch.object(tools, "DDGS_FACTORY", return_value=FakeDDGS):
            result = json.loads(tools.web_search("example", max_results=1))

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["url"], "https://example.com/1")

    def test_web_search_passes_through_30_second_timeout(self):
        observed: dict[str, int] = {}

        class TimeoutDDGS(FakeDDGS):
            def __init__(self, timeout: int):
                super().__init__(timeout)
                observed["timeout"] = timeout

        with mock.patch.object(tools, "DDGS_FACTORY", return_value=TimeoutDDGS):
            json.loads(tools.web_search("example"))

        self.assertEqual(observed["timeout"], 30)

    def test_web_search_zero_results(self):
        class EmptyDDGS(FakeDDGS):
            def text(self, query: str, max_results: int = 5):
                return []

        with mock.patch.object(tools, "DDGS_FACTORY", return_value=EmptyDDGS):
            result = json.loads(tools.web_search("none"))

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["results"], [])
        self.assertIn("No results found", result["message"])

    def test_web_search_library_error_is_structured(self):
        with mock.patch.object(tools, "DDGS_FACTORY", side_effect=RuntimeError("ddgs missing")):
            result = json.loads(tools.web_search("example"))

        self.assertEqual(result["status"], "error")
        self.assertIn("ddgs missing", result["error"])

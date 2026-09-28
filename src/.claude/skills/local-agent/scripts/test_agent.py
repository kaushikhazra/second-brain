"""Unit tests for agent.py."""

from __future__ import annotations

import asyncio
import json
import os
import unittest
from unittest import mock

import agent


class TestToolSchema(unittest.TestCase):
    def test_all_five_tools_are_exposed_in_order(self):
        names = [schema["function"]["name"] for schema in agent.TOOL_SCHEMAS]

        self.assertEqual(
            names, ["read_file", "write_file", "edit_file", "run_command", "web_search"]
        )

    def test_schema_is_derived_from_the_signature(self):
        schema = agent.build_tool_schema(agent.edit_file)["function"]

        self.assertEqual(
            schema["parameters"]["properties"],
            {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}},
        )
        self.assertEqual(schema["parameters"]["required"], ["path", "old", "new"])

    def test_defaulted_parameters_are_optional_and_typed(self):
        schema = agent.build_tool_schema(agent.web_search)["function"]

        self.assertEqual(schema["parameters"]["properties"]["max_results"], {"type": "integer"})
        self.assertEqual(schema["parameters"]["required"], ["query"])

    def test_description_comes_from_the_first_docstring_line(self):
        schema = agent.build_tool_schema(agent.read_file)["function"]

        self.assertTrue(schema["description"].startswith("Read a UTF-8 text file"))
        self.assertNotIn("\n", schema["description"])


class TestEndpointAndOptions(unittest.TestCase):
    def setUp(self) -> None:
        self.original = {k: os.environ.get(k) for k in ("OLLAMA_BASE_URL", "OLLAMA_NUM_CTX")}

    def tearDown(self) -> None:
        for key, value in self.original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_v1_endpoint_is_rewritten_to_the_native_chat_path(self):
        self.assertEqual(
            agent.native_chat_url("http://localhost:11434/v1"),
            "http://localhost:11434/api/chat",
        )

    def test_endpoint_without_a_path_also_works(self):
        self.assertEqual(
            agent.native_chat_url("http://192.168.1.5:11434"),
            "http://192.168.1.5:11434/api/chat",
        )

    def test_endpoint_falls_back_to_the_environment(self):
        os.environ["OLLAMA_BASE_URL"] = "http://elsewhere:9999/v1"

        self.assertEqual(agent.native_chat_url(), "http://elsewhere:9999/api/chat")

    def test_invalid_endpoint_is_rejected(self):
        with self.assertRaises(ValueError):
            agent.native_chat_url("not-a-url")

    def test_num_ctx_is_read_when_set(self):
        os.environ["OLLAMA_NUM_CTX"] = "8192"

        self.assertEqual(agent.configured_num_ctx(), 8192)

    def test_num_ctx_absent_or_unusable_is_none(self):
        for value in (None, "", "abc", "0", "-1"):
            with self.subTest(value=value):
                if value is None:
                    os.environ.pop("OLLAMA_NUM_CTX", None)
                else:
                    os.environ["OLLAMA_NUM_CTX"] = value
                self.assertIsNone(agent.configured_num_ctx())


class TestExecuteToolCall(unittest.TestCase):
    def test_object_arguments_are_passed_through(self):
        with mock.patch.dict(agent.TOOL_REGISTRY, {"fake": lambda text: f"got {text}"}):
            name, result = agent.execute_tool_call(
                {"function": {"name": "fake", "arguments": {"text": "hi"}}}
            )

        self.assertEqual((name, result), ("fake", "got hi"))

    def test_json_string_arguments_are_tolerated(self):
        with mock.patch.dict(agent.TOOL_REGISTRY, {"fake": lambda text: f"got {text}"}):
            _, result = agent.execute_tool_call(
                {"function": {"name": "fake", "arguments": '{"text": "hi"}'}}
            )

        self.assertEqual(result, "got hi")

    def test_unparsable_arguments_are_reported_to_the_model(self):
        _, result = agent.execute_tool_call(
            {"function": {"name": "read_file", "arguments": "{not json"}}
        )

        self.assertEqual(json.loads(result)["status"], "error")

    def test_unknown_tool_is_reported_to_the_model_not_raised(self):
        name, result = agent.execute_tool_call({"function": {"name": "nope", "arguments": {}}})

        self.assertEqual(name, "nope")
        self.assertIn("Unknown tool", json.loads(result)["error"])

    def test_bad_arguments_are_reported_to_the_model_not_raised(self):
        _, result = agent.execute_tool_call(
            {"function": {"name": "read_file", "arguments": {"wrong": "kwarg"}}}
        )

        self.assertIn("Bad arguments", json.loads(result)["error"])


class TestParseSummary(unittest.TestCase):
    def test_valid_payload(self):
        self.assertEqual(agent.parse_summary('{"summary": "done"}').summary, "done")

    def test_empty_content_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty content"):
            agent.parse_summary("   ")

    def test_non_json_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not JSON"):
            agent.parse_summary("just prose")

    def test_wrong_shape_is_rejected(self):
        # The exact failure seen from ornith:9b under the /v1 route.
        with self.assertRaisesRegex(ValueError, "did not match"):
            agent.parse_summary("[1234567]")

    def test_missing_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "did not match"):
            agent.parse_summary('{"result": "done"}')


def _tool_call(name: str, **arguments: object) -> dict:
    return {"function": {"name": name, "arguments": arguments}}


class TestRunAgentSummary(unittest.TestCase):
    def setUp(self) -> None:
        self.original = os.environ.get("OLLAMA_BASE_URL")
        os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434/v1"

    def tearDown(self) -> None:
        if self.original is None:
            os.environ.pop("OLLAMA_BASE_URL", None)
        else:
            os.environ["OLLAMA_BASE_URL"] = self.original

    def _run(self, turns: list[dict]) -> tuple[agent.AgentSummary, mock.AsyncMock]:
        chat = mock.AsyncMock(side_effect=turns)
        with mock.patch.object(agent, "chat_once", chat):
            result = asyncio.run(agent.run_agent_summary("Task", "System", "ornith:9b"))
        return result, chat

    def test_tool_turn_then_summary(self):
        with mock.patch.dict(agent.TOOL_REGISTRY, {"fake": lambda text: f"got {text}"}):
            result, chat = self._run(
                [
                    {"role": "assistant", "content": "", "tool_calls": [_tool_call("fake", text="hi")]},
                    {"role": "assistant", "content": '{"summary": "all done"}'},
                ]
            )

        self.assertEqual(result.summary, "all done")
        self.assertEqual(chat.await_count, 2)

    def test_tool_result_is_fed_back_with_the_native_tool_name_key(self):
        with mock.patch.dict(agent.TOOL_REGISTRY, {"fake": lambda text: "tool output"}):
            _, chat = self._run(
                [
                    {"role": "assistant", "content": "", "tool_calls": [_tool_call("fake", text="hi")]},
                    {"role": "assistant", "content": '{"summary": "done"}'},
                ]
            )

        messages = chat.await_args_list[1].args[1]
        self.assertEqual(
            messages[-1], {"role": "tool", "tool_name": "fake", "content": "tool output"}
        )

    def test_system_and_task_open_the_conversation(self):
        _, chat = self._run([{"role": "assistant", "content": '{"summary": "done"}'}])

        messages = chat.await_args_list[0].args[1]
        self.assertEqual(messages[0], {"role": "system", "content": "System"})
        self.assertEqual(messages[1], {"role": "user", "content": "Task"})

    def test_tool_call_limit_is_enforced(self):
        over_limit = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [_tool_call("fake", text="x")],
            }
            for _ in range(agent.TOOL_CALL_LIMIT + 1)
        ]
        with mock.patch.dict(agent.TOOL_REGISTRY, {"fake": lambda text: "ok"}):
            with self.assertRaises(agent.ToolCallLimitExceeded):
                self._run(over_limit)

    def test_invalid_output_is_retried_then_accepted(self):
        result, chat = self._run(
            [
                {"role": "assistant", "content": "not json at all"},
                {"role": "assistant", "content": '{"summary": "second try"}'},
            ]
        )

        self.assertEqual(result.summary, "second try")
        # The retry must carry an instruction; an empty nudge is what made the
        # model return nothing at all in testing.
        retry_messages = chat.await_args_list[1].args[1]
        self.assertEqual(retry_messages[-1]["role"], "user")
        self.assertIn("summary", retry_messages[-1]["content"])

    def test_exhausted_retries_raise_output_validation_error(self):
        turns = [{"role": "assistant", "content": "nope"} for _ in range(agent.OUTPUT_RETRIES + 1)]

        with self.assertRaises(agent.OutputValidationError):
            self._run(turns)

    def test_empty_reply_is_treated_as_invalid_output(self):
        result, _ = self._run(
            [
                {"role": "assistant", "content": ""},
                {"role": "assistant", "content": '{"summary": "recovered"}'},
            ]
        )

        self.assertEqual(result.summary, "recovered")


class TestChatOnce(unittest.TestCase):
    def _capture_payload(self, body: dict, num_ctx: int | None = None) -> dict:
        captured: dict = {}

        def fake_post(payload, url):
            captured.update({"payload": payload, "url": url})
            return body

        with mock.patch.object(agent, "_post_chat", fake_post):
            message = asyncio.run(
                agent.chat_once(
                    "ornith:9b",
                    [{"role": "user", "content": "hi"}],
                    {"type": "object"},
                    "http://localhost:11434/api/chat",
                    num_ctx,
                )
            )
        captured["message"] = message
        return captured

    def test_tools_and_format_are_sent_together(self):
        captured = self._capture_payload({"message": {"role": "assistant", "content": "ok"}})

        payload = captured["payload"]
        self.assertEqual(payload["format"], {"type": "object"})
        self.assertEqual(len(payload["tools"]), 5)
        self.assertFalse(payload["stream"])
        self.assertEqual(captured["url"], "http://localhost:11434/api/chat")

    def test_num_ctx_is_omitted_when_not_configured(self):
        captured = self._capture_payload({"message": {"role": "assistant", "content": "ok"}})

        self.assertNotIn("options", captured["payload"])

    def test_num_ctx_is_sent_when_configured(self):
        captured = self._capture_payload(
            {"message": {"role": "assistant", "content": "ok"}}, num_ctx=8192
        )

        self.assertEqual(captured["payload"]["options"], {"num_ctx": 8192})

    def test_response_without_a_message_raises_model_behavior_error(self):
        with self.assertRaises(agent.ModelBehaviorError):
            self._capture_payload({"error": "something broke"})

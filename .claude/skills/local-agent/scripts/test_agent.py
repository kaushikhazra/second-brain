"""Unit tests for agent.py."""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest import mock

from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.models.test import TestModel

import agent


class TestAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.original_endpoint = os.environ.get("OLLAMA_BASE_URL")
        os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434/v1"

    def tearDown(self) -> None:
        if self.original_endpoint is None:
            os.environ.pop("OLLAMA_BASE_URL", None)
        else:
            os.environ["OLLAMA_BASE_URL"] = self.original_endpoint

    def test_build_agent_uses_expected_model_string_and_output_contract(self):
        built_agent = agent.build_agent("ornith:9b", "Be concise.")

        self.assertEqual(built_agent.model.model_name, "ornith:9b")
        self.assertEqual(built_agent._output_schema.object_def.name, "AgentSummary")
        self.assertEqual(built_agent._max_result_retries, 2)

    def test_build_agent_registers_all_five_tools(self):
        built_agent = agent.build_agent("ornith:9b", "System")
        tool_names = [tool.name for tool in built_agent._function_toolset.tools.values()]

        self.assertEqual(
            tool_names,
            ["read_file", "write_file", "edit_file", "run_command", "web_search"],
        )

    def test_run_agent_summary_returns_agent_summary_from_real_agent_run(self):
        built_agent = agent.build_agent("ornith:9b", "System")

        summary = asyncio.run(
            built_agent.run(
                "Task",
                model=TestModel(custom_output_args={"summary": "Model summary"}),
            )
        ).output

        self.assertEqual(summary.summary, "Model summary")

    def test_run_agent_summary_applies_tool_call_limit(self):
        class FakeRunResult:
            output = agent.AgentSummary(summary="done")

        fake_agent = mock.Mock()
        fake_agent.run = mock.AsyncMock(return_value=FakeRunResult())
        with mock.patch.object(agent, "build_agent", return_value=fake_agent):
            asyncio.run(agent.run_agent_summary("Task", "System", "ornith:9b"))

        usage_limits = fake_agent.run.call_args.kwargs["usage_limits"]
        self.assertEqual(usage_limits.tool_calls_limit, 15)

    def test_run_agent_summary_propagates_usage_limit_exception(self):
        fake_agent = mock.Mock()
        fake_agent.run = mock.AsyncMock(side_effect=UsageLimitExceeded("limit hit"))
        with mock.patch.object(agent, "build_agent", return_value=fake_agent):
            with self.assertRaises(UsageLimitExceeded):
                asyncio.run(agent.run_agent_summary("Task", "System", "ornith:9b"))

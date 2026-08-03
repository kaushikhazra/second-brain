"""Agent construction and default runner for the local-agent skill."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits

from tools import edit_file, read_file, run_command, web_search, write_file


class AgentSummary(BaseModel):
    """Structured output emitted by the model."""

    summary: str


def build_agent(model_name: str, system_text: str) -> Agent:
    """Build the pydantic-ai agent with the exact tool and output contract."""

    agent = Agent(
        f"ollama:{model_name}",
        instructions=system_text,
        output_type=AgentSummary,
        output_retries=2,
    )
    agent.tool_plain(read_file)
    agent.tool_plain(write_file)
    agent.tool_plain(edit_file)
    agent.tool_plain(run_command)
    agent.tool_plain(web_search)
    return agent


async def run_agent_summary(task_text: str, system_text: str, model_name: str) -> AgentSummary:
    """Run the agent once and return the model-authored summary only."""

    agent = build_agent(model_name, system_text)
    result = await agent.run(
        task_text,
        usage_limits=UsageLimits(tool_calls_limit=15),
    )
    return result.output

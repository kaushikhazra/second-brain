@echo off
REM ============================================================
REM  {{AGENT_ID}} launcher (machine-local, not product)
REM   - only this brain's own MCP servers load (--strict-mcp-config)
REM   - the repos it maintains are its own clones under projects\
REM ============================================================
title {{AGENT_ID}}
cd /d "%~dp0"

set "MCP_TIMEOUT=300000"
REM launched from another Claude session, it would inherit the child marker and save no transcript
set "CLAUDE_CODE_CHILD_SESSION="
set "CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1"

REM --model sonnet: the maintainers' default; change to opus for heavier reasoning
REM --dangerously-skip-permissions: so it can loop unattended without stalling on prompts.
REM    Remove it if this machine's policy does not allow that.
REM No arguments: open with "hello", so the session boots itself instead of waiting for a first message
REM Arguments go FIRST: --mcp-config takes several values and would swallow a trailing prompt
REM --name: a unique window title, so two maintainer windows can be told apart
if "%~1"=="" (set "ARGS="hello"") else (set ARGS=%*)
if exist ".mcp.json" (
  claude %ARGS% --name "{{AGENT_ID}}_%date%_%time: =%" --model sonnet --dangerously-skip-permissions --strict-mcp-config --mcp-config .mcp.json
) else (
  REM first run: no servers at all until /init-brain writes .mcp.json
  claude %ARGS% --name "{{AGENT_ID}}_%date%_%time: =%" --model sonnet --dangerously-skip-permissions --strict-mcp-config --mcp-config "{\"mcpServers\":{}}"
)

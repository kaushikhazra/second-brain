@echo off
REM ============================================================
REM  Second Brain launcher (Windows)
REM  Starts Claude Code in this project as your second brain,
REM  using your installed Claude (normal config) -- no sandbox.
REM  First run: start it, then run  /init-brain  to provision.
REM ============================================================
cd /d "%~dp0"

REM 1) Is Claude Code installed / on PATH?
where claude >nul 2>nul
if errorlevel 1 (
  echo.
  echo   Claude Code was not found on PATH.
  echo   Install it first:  https://claude.com/claude-code
  echo   then run this again.
  echo.
  pause
  exit /b 1
)

REM 2) Give synaptra's MCP server room for its one-time cold start
REM    (loading the embedding model can take ~20s-3min).
set "MCP_TIMEOUT=300000"

REM 3) Launch Claude in this project. On first run, use /init-brain.
echo Starting your second brain...  (first run? run  /init-brain )
claude %*

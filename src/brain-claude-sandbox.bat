@echo off
REM ============================================================
REM  Second Brain launcher -- ISOLATED CLAUDE CONFIG
REM
REM  A thin wrapper around brain.bat. The only thing it adds is
REM  CLAUDE_CONFIG_DIR, so Claude Code keeps its config and
REM  credentials in .claude-config inside this folder instead of
REM  %USERPROFILE%\.claude. Everything else -- the PATH check, the
REM  MCP cold-start timeout, the launch itself -- lives in brain.bat
REM  and is not repeated here.
REM
REM  Use this when you want the brain self-contained enough to hand
REM  around, back up or throw away, or when you already run Claude
REM  Code for something else and do not want the two sharing
REM  settings, MCP servers or history.
REM
REM  First run: start it, then run  /init-brain
REM  You will sign in to Claude once, separately from your usual login.
REM ============================================================
cd /d "%~dp0"

REM Resolved from this file's own location, so the folder can be
REM renamed or moved and this still points at the right place.
set "CLAUDE_CONFIG_DIR=%CD%\.claude-config"

echo.
echo   Claude config dir : %CD%\.claude-config   (isolated)

call "%~dp0brain.bat" %*

#!/bin/sh
# ============================================================
#  Second Brain launcher -- ISOLATED CLAUDE CONFIG (Linux)
#
#  A thin wrapper around brain.sh. The only thing it adds is
#  CLAUDE_CONFIG_DIR, so Claude Code keeps its config and
#  credentials in .claude-config inside this folder instead of
#  ~/.claude. Everything else -- the PATH check, the MCP
#  cold-start timeout, the launch itself -- lives in brain.sh
#  and is not repeated here.
#
#  Use this when you want the brain self-contained enough to hand
#  around, back up or throw away, or when you already run Claude
#  Code for something else and do not want the two sharing
#  settings, MCP servers or history.
#
#  First run: start it, then run  /init-brain
#  You will sign in to Claude once, separately from your usual login.
# ============================================================
cd "$(dirname "$0")" || exit 1

# Resolved from this file's own location, so the folder can be
# renamed or moved and this still points at the right place.
CLAUDE_CONFIG_DIR="$PWD/.claude-config"
export CLAUDE_CONFIG_DIR

echo
echo "  Claude config dir : $CLAUDE_CONFIG_DIR   (isolated)"

exec sh "$PWD/brain.sh" "$@"

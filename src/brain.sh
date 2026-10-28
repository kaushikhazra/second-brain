#!/bin/sh
# ============================================================
#  Second Brain launcher (Linux)
#  Starts Claude Code in this project as your second brain,
#  using your installed Claude (normal config) -- no sandbox.
#  First run: start it, then run  /init-brain  to provision.
#
#  Starting it with nobody at the keyboard (login, a schedule)?
#  Set SECOND_BRAIN_UNATTENDED=1 first. The boot then asks no
#  question (switching on curiosity or the news) and records no
#  answer; those habits stay off until a boot with someone there.
# ============================================================
cd "$(dirname "$0")" || exit 1

# 1) Is Claude Code installed / on PATH?
if ! command -v claude >/dev/null 2>&1; then
  echo
  echo "  Claude Code was not found on PATH."
  echo "  Install it first:  https://claude.com/claude-code"
  echo "  then run this again."
  echo
  exit 1
fi

# 2) Give synaptra's MCP server room for its one-time cold start
#    (loading the embedding model can take ~20s-3min).
MCP_TIMEOUT=300000
export MCP_TIMEOUT

# 3) The skills run `python ...`; Debian-family systems ship only `python3`.
#    Once the brain has its own venv, put it first so `python` is the brain's.
if [ -d ".claude/.venv/bin" ]; then
  PATH="$PWD/.claude/.venv/bin:$PATH"
  export PATH
fi

# 4) aarch64 only: torch and scikit-learn each bundle their own libgomp, and loading the
#    second dies with "cannot allocate memory in static TLS block". Preloading both before
#    anything starts fixes it; the MCP server inherits the variable from here.
first_match() {
  for f in "$@"; do
    if [ -e "$f" ]; then
      echo "$PWD/$f"
      return
    fi
  done
}
if [ "$(uname -m)" = "aarch64" ]; then
  preload=
  for lib in \
    "$(first_match .claude/.venv/lib/python3*/site-packages/torch/lib/libgomp.so.1)" \
    "$(first_match .claude/.venv/lib/python3*/site-packages/scikit_learn.libs/libgomp-*.so*)"
  do
    if [ -n "$lib" ]; then
      preload="${preload:+$preload:}$lib"
    fi
  done
  if [ -n "$preload" ]; then
    LD_PRELOAD="$preload${LD_PRELOAD:+:$LD_PRELOAD}"
    export LD_PRELOAD
  fi
fi

# 5) Launch Claude in this project. On first run, use /init-brain.
echo "Starting your second brain...  (first run? run  /init-brain )"
exec claude "$@"

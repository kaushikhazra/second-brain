#!/bin/sh
# Run a guard hook on the brain's own Python -- never on whatever `python` the machine has.
#
#   sh run_guard.sh <guard.py>        (the tool-call JSON arrives on stdin and passes through)
#
# Interpreter order: .claude/.venv, then the standalone one under .claude/.python (the venv is
# deleted and rebuilt during an update or a move repair; the standalone one stays). Both are found
# from this file's own location, so a renamed or moved brain folder still works.
#
# If neither exists the guard cannot run. Say so loudly (exit 1 is a visible hook error) rather
# than let the tool call through as if it had been checked.
here=$(cd "$(dirname "$0")" && pwd)
claude=$(dirname "$here")

for py in \
    "$claude/.venv/Scripts/python.exe" \
    "$claude/.venv/bin/python" \
    "$claude"/.python/*/python.exe \
    "$claude"/.python/*/bin/python3
do
    if [ -f "$py" ]; then
        exec "$py" "$here/$1"
    fi
done

echo "second-brain: $1 did NOT run -- no Python found under .claude/.venv or .claude/.python. This tool call was not checked. Run /init-brain to repair." >&2
exit 1

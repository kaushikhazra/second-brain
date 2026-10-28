#!/bin/sh
# Linux entry point. Finds the brain's own standalone Python at run time
# (nothing is baked in), then hands over to launch.py.
here=$(cd "$(dirname "$0")" && pwd)
claude=$(dirname "$(dirname "$(dirname "$here")")")
py=
for d in "$claude"/.python/cpython-*; do
    if [ -z "$py" ] && [ -f "$d/bin/python3" ]; then
        py="$d/bin/python3"
    fi
done
if [ -z "$py" ]; then
    echo "[transcribe] ERROR: no Python under \"$claude/.python\". Run /init-brain first." >&2
    exit 2
fi
exec "$py" "$here/launch.py" "$@"

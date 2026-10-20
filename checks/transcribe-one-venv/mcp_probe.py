#!/usr/bin/env python3
"""Issue #72 AC 8: the brain's synaptra MCP server starts and answers a request.

Starts `.claude/.venv/Scripts/synaptra(.exe)` exactly as `.mcp.json` does (stdio,
surrealkv-file backend, a store under the brain), sends `initialize`, lists the
tools and calls `memory_health`. Exit 0 only if all three answer.

    python checks/transcribe-one-venv/mcp_probe.py <brain-root>
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

TIMEOUT = 300  # synaptra's cold start loads an embedding model


def main() -> int:
    brain = Path(sys.argv[1]).resolve()
    exe = (
        brain
        / ".claude"
        / ".venv"
        / ("Scripts/synaptra.exe" if os.name == "nt" else "bin/synaptra")
    )
    env = dict(os.environ)
    env["SYNAPTRA_BACKEND"] = "surrealkv-file"
    env["SYNAPTRA_DB"] = str(brain / ".claude" / "synaptra-data")
    proc = subprocess.Popen(
        [str(exe), "--transport", "stdio"],
        cwd=brain,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    replies: dict[int, dict] = {}
    got = threading.Condition()

    def reader() -> None:
        for line in proc.stdout:
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if "id" in msg:
                with got:
                    replies[msg["id"]] = msg
                    got.notify_all()

    threading.Thread(target=reader, daemon=True).start()

    def send(obj: dict) -> None:
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    def ask(i: int, method: str, params: dict) -> dict | None:
        send({"jsonrpc": "2.0", "id": i, "method": method, "params": params})
        with got:
            got.wait_for(lambda: i in replies, timeout=TIMEOUT)
        return replies.get(i)

    ok = True
    try:
        init = ask(
            1,
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "probe", "version": "0"},
            },
        )
        print("initialize:", "OK" if init and "result" in init else init)
        ok &= bool(init and "result" in init)
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools = ask(2, "tools/list", {})
        names = [t["name"] for t in (tools or {}).get("result", {}).get("tools", [])]
        print(
            f"tools/list: {len(names)} tools",
            "OK" if "memory_health" in names else names,
        )
        ok &= "memory_health" in names
        health = ask(3, "tools/call", {"name": "memory_health", "arguments": {}})
        good = bool(
            health and "result" in health and not health["result"].get("isError")
        )
        print("memory_health:", "OK" if good else health)
        ok &= good
    finally:
        proc.terminate()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

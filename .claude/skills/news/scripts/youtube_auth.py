"""One-time OAuth consent for reading the owner's YouTube subscriptions.

Run once. It opens a browser, the owner approves, and the refresh token is
written to the brain-root `.env`. Nothing is printed that should not be.

Needs in .env first:
    YOUTUBE_CLIENT_ID=...
    YOUTUBE_CLIENT_SECRET=...

Writes back:
    YOUTUBE_REFRESH_TOKEN=...

Stdlib only. The brain root resolves by walking up from this file to the
first directory holding both `.claude/` and `CLAUDE.md` -- never a fixed
parent-directory count.
"""

import http.server
import json
import socket
import threading
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

SCOPE = "https://www.googleapis.com/auth/youtube"
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"


def brain_root(start: "Path | None" = None) -> "Path | None":
    here = start or Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / ".claude").is_dir() and (candidate / "CLAUDE.md").is_file():
            return candidate
    return None


ROOT = brain_root()
ENV = (ROOT / ".env") if ROOT else None


def env(name):
    if ENV is not None and ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return None


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Catcher(http.server.BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        Catcher.code = q.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        msg = "Done. You can close this tab." if Catcher.code else "No code returned."
        self.wfile.write(f"<h3>{msg}</h3>".encode())

    def log_message(self, *a):
        pass


def main():
    if ROOT is None:
        raise SystemExit(
            "Could not resolve the brain root -- no .env to read or write."
        )
    cid, secret = env("YOUTUBE_CLIENT_ID"), env("YOUTUBE_CLIENT_SECRET")
    if not cid or not secret:
        raise SystemExit(
            f"Put YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in {ENV} first."
        )

    port = free_port()
    redirect = f"http://localhost:{port}"
    url = (
        AUTH
        + "?"
        + urllib.parse.urlencode(
            {
                "client_id": cid,
                "redirect_uri": redirect,
                "response_type": "code",
                "scope": SCOPE,
                "access_type": "offline",
                "prompt": "consent",
            }
        )
    )

    server = http.server.HTTPServer(("127.0.0.1", port), Catcher)
    threading.Thread(target=server.handle_request, daemon=True).start()

    print(
        "Opening the browser. Approve the YouTube access (read + manage subscriptions)."
    )
    print(f"If it does not open, paste this in yourself:\n{url}\n")
    webbrowser.open(url)

    for _ in range(120):
        if Catcher.code:
            break
        threading.Event().wait(1)
    if not Catcher.code:
        raise SystemExit("Timed out waiting for consent.")

    body = urllib.parse.urlencode(
        {
            "code": Catcher.code,
            "client_id": cid,
            "client_secret": secret,
            "redirect_uri": redirect,
            "grant_type": "authorization_code",
        }
    ).encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN, data=body)) as r:
        tok = json.load(r)

    refresh = tok.get("refresh_token")
    if not refresh:
        raise SystemExit(f"No refresh token returned. Response keys: {list(tok)}")

    line = f"YOUTUBE_REFRESH_TOKEN={refresh}"
    existing = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    kept = [l for l in existing if not l.strip().startswith("YOUTUBE_REFRESH_TOKEN=")]
    replaced = len(existing) - len(kept)
    ENV.write_text("\n".join(kept + [line]) + "\n", encoding="utf-8")
    what = "replaced" if replaced else "written"
    print(f"Refresh token {what} in {ENV}. Nothing else to do.")


if __name__ == "__main__":
    main()

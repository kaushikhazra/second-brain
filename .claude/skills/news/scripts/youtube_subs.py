"""What the owner's YouTube subscriptions posted recently.

Uses OAuth to list subscriptions (1 quota unit per 50 channels), then the Data
API's `playlistItems` route on each subscription's uploads playlist for recent
videos (1 quota unit per channel per run). There is deliberately no RSS path:
YouTube's public per-channel RSS feed returned 404 on this machine on
2026-09-19, and a card built on it silently reads empty for a live channel
under any burst of requests -- the API route is the one kept, not a fallback
alongside a broken one.

--subscribe and --unsubscribe manage the list. Both resolve EXACTLY -- a handle,
a channel URL, or a UC... id -- and both print what they matched and change
nothing until --yes is given. There is deliberately no name search: one word
matched two different people once, and a silent wrong pick is worse than a
refusal.

usage:  python youtube_subs.py [--days 2] [--limit 20]
        python youtube_subs.py --unsubscribe "<name fragment>" [--yes]
        python youtube_subs.py --subscribe "@handle | url | UC..." [--yes]

Needs in .env, at the brain root: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET,
YOUTUBE_REFRESH_TOKEN. Missing or incomplete -> exits with a message prefixed
NOT_CONFIGURED, distinguishable from an actual failure (AUTH_FAILED,
QUOTA_EXCEEDED, NETWORK_ERROR) so the caller can tell "not set up" from
"set up and broken."
"""

import argparse
import json
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def brain_root(start: "Path | None" = None) -> "Path | None":
    """Walk up from `start` (default: this file's own directory) to the first
    directory holding both `.claude/` and `CLAUDE.md`. Never a fixed
    `parents[N]` depth -- that freezes the assumption that this script always
    lives the same number of directories below the root, which breaks the
    moment either moves."""
    here = start or Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / ".claude").is_dir() and (candidate / "CLAUDE.md").is_file():
            return candidate
    return None


ROOT = brain_root()
ENV = (ROOT / ".env") if ROOT else None
TOKEN_URL = "https://oauth2.googleapis.com/token"
SUBS_URL = "https://www.googleapis.com/youtube/v3/subscriptions"
CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
PLAYLIST_ITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems"
UPLOADS_PAGE_SIZE = 15  # per channel, per run -- still 1 quota unit regardless of size


class NotConfigured(SystemExit):
    pass


class AuthFailed(SystemExit):
    pass


class NetworkError(SystemExit):
    pass


def env(name):
    if ENV is not None and ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return None


def keywords():
    """The owner's words, from news-keywords.txt at the brain root -- not
    from this skill's own file; that file is `/news`'s shared scope, not a
    YouTube-only one (issue #7, AC 12)."""
    if ROOT is None:
        return []
    path = ROOT / "news-keywords.txt"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line.lower())
    return out


def matches(title, words):
    low = title.lower()
    return any(re.search(r"\b" + re.escape(w) + r"\b", low) for w in words)


def _urlopen(req, timeout=30):
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.URLError as e:
        if isinstance(e, urllib.error.HTTPError):
            raise
        raise NetworkError(
            f"NETWORK_ERROR: could not reach the YouTube API: {e.reason}"
        )
    except socket.timeout:
        raise NetworkError("NETWORK_ERROR: timed out reaching the YouTube API")


def access_token():
    if ROOT is None:
        raise NotConfigured(
            "NOT_CONFIGURED: could not resolve the brain root, so no .env to read"
        )
    missing = [
        k
        for k in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
        if not env(k)
    ]
    if missing:
        raise NotConfigured(
            f"NOT_CONFIGURED: missing from {ENV}: {', '.join(missing)}. "
            "Run youtube_auth.py first."
        )
    body = urllib.parse.urlencode(
        {
            "client_id": env("YOUTUBE_CLIENT_ID"),
            "client_secret": env("YOUTUBE_CLIENT_SECRET"),
            "refresh_token": env("YOUTUBE_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        }
    ).encode()
    try:
        with _urlopen(urllib.request.Request(TOKEN_URL, data=body)) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        if e.code in (400, 401):
            raise AuthFailed(
                f"AUTH_FAILED: YouTube refused the refresh token (HTTP {e.code}). "
                "It may have been revoked -- run youtube_auth.py again."
            )
        raise AuthFailed(
            f"AUTH_FAILED: YouTube token refresh failed: HTTP {e.code}: {body_text[:300]}"
        )


def subscriptions(token, full=False):
    """(channelId, title) per subscription. full=True prepends the SUBSCRIPTION id,
    which is what subscriptions.delete takes -- it is not the channel id."""
    out, page = [], None
    while True:
        q = {"part": "snippet", "mine": "true", "maxResults": 50}
        if page:
            q["pageToken"] = page
        req = urllib.request.Request(
            SUBS_URL + "?" + urllib.parse.urlencode(q),
            headers={"Authorization": f"Bearer {token}"},
        )
        with _urlopen(req) as r:
            data = json.load(r)
        for i in data.get("items", []):
            s = i["snippet"]
            if full:
                out.append((i["id"], s["resourceId"]["channelId"], s["title"]))
            else:
                out.append((s["resourceId"]["channelId"], s["title"]))
        page = data.get("nextPageToken")
        if not page:
            return out


def recent_uploads(channel, token):
    """Up to UPLOADS_PAGE_SIZE most recent uploads for one channel, via the
    Data API's playlistItems on its uploads playlist (UC -> UU). 1 quota unit
    regardless of how many come back. Returns None only on an HTTP error
    specific to this one channel (deleted, uploads playlist missing) -- the
    caller reports the channel as unreadable rather than treating None as
    "no recent uploads," which would look identical to a quiet channel."""
    cid, name = channel
    q = {
        "part": "snippet",
        "playlistId": "UU" + cid[2:],
        "maxResults": UPLOADS_PAGE_SIZE,
    }
    req = urllib.request.Request(
        PLAYLIST_ITEMS_URL + "?" + urllib.parse.urlencode(q),
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with _urlopen(req) as r:
            items = json.load(r).get("items", [])
    except urllib.error.HTTPError:
        return None
    out = []
    for it in items:
        sn = it["snippet"]
        vid = sn.get("resourceId", {}).get("videoId")
        if not vid:
            continue
        out.append(
            {
                "channel": name,
                "title": sn.get("title") or "",
                "url": f"https://www.youtube.com/watch?v={vid}",
                "published": sn.get("publishedAt") or "",
            }
        )
    return out


def resolve_channel(token, text):
    """text -> the channel resource. Exact lookups only: an @handle, a channel
    URL, or a UC... id. No name search on purpose."""
    t = text.strip().rstrip("/")
    if "/channel/" in t:
        t = t.split("/channel/", 1)[1].split("/")[0]
    elif "/@" in t:
        t = "@" + t.split("/@", 1)[1].split("/")[0]
    part = "snippet,statistics"
    if re.fullmatch(r"UC[\w-]{22}", t):
        q = {"part": part, "id": t}
    else:
        q = {"part": part, "forHandle": t if t.startswith("@") else "@" + t}
    req = urllib.request.Request(
        CHANNELS_URL + "?" + urllib.parse.urlencode(q),
        headers={"Authorization": f"Bearer {token}"},
    )
    with _urlopen(req) as r:
        items = json.load(r).get("items", [])
    if not items:
        raise SystemExit(
            f"Nothing resolves for {text!r}. Give the @handle or the channel URL."
        )
    return items[0]


def subscribe(token, channel_id):
    body = json.dumps(
        {
            "snippet": {
                "resourceId": {"kind": "youtube#channel", "channelId": channel_id}
            }
        }
    ).encode()
    req = urllib.request.Request(
        SUBS_URL + "?" + urllib.parse.urlencode({"part": "snippet"}),
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with _urlopen(req) as r:
        return r.status


def unsubscribe(token, sub_id):
    req = urllib.request.Request(
        SUBS_URL + "?" + urllib.parse.urlencode({"id": sub_id}),
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE",
    )
    with _urlopen(req) as r:
        return r.status


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=2)
    p.add_argument(
        "--limit", type=int, default=20, help="most items to print. 0 = no cap"
    )
    p.add_argument(
        "--per-channel",
        type=int,
        default=2,
        help="most items any one channel may contribute. 0 = no cap",
    )
    p.add_argument(
        "--shorts", action="store_true", help="include Shorts (excluded by default)"
    )
    p.add_argument(
        "--all", action="store_true", help="skip the keyword scope, show the whole feed"
    )
    p.add_argument(
        "--unsubscribe",
        metavar="TEXT",
        help="channel-name fragment to unsubscribe from",
    )
    p.add_argument(
        "--subscribe",
        metavar="CHANNEL",
        help="@handle, channel URL, or UC... id to subscribe to",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="with --subscribe or --unsubscribe, actually make the change",
    )
    a = p.parse_args()

    if a.subscribe:
        token = access_token()
        ch = resolve_channel(token, a.subscribe)
        cid, title = ch["id"], ch["snippet"]["title"]
        print(("subscribing to " if a.yes else "would subscribe to ") + title)
        if not a.yes:
            raise SystemExit("Nothing changed. Re-run with --yes to subscribe.")
        try:
            subscribe(token, cid)
        except urllib.error.HTTPError as e:
            if e.code == 400 and b"subscriptionDuplicate" in e.read():
                raise SystemExit(f"Already subscribed to {title}.")
            raise
        print(f"subscribed: {title}")
        return

    if a.unsubscribe:
        token = access_token()
        want = a.unsubscribe.lower()
        hits = [s for s in subscriptions(token, full=True) if want in s[2].lower()]
        if not hits:
            raise SystemExit(f"No subscription matches {a.unsubscribe!r}.")
        for _, _, title in hits:
            print(("removing " if a.yes else "would remove ") + title)
        if not a.yes:
            raise SystemExit("Nothing changed. Re-run with --yes to remove.")
        for sub_id, _, title in hits:
            unsubscribe(token, sub_id)
            print(f"unsubscribed: {title}")
        return

    token = access_token()
    subs = subscriptions(token)
    cutoff = datetime.now(timezone.utc) - timedelta(days=a.days)

    with ThreadPoolExecutor(max_workers=8) as pool:
        batches = list(pool.map(lambda c: recent_uploads(c, token), subs))
    unreadable_channels = [subs[i][1] for i, b in enumerate(batches) if b is None]
    all_vids = [v for b in batches if b is not None for v in b]

    recent = []
    for v in all_vids:
        try:
            when = datetime.fromisoformat(v["published"].replace("Z", "+00:00"))
        except ValueError:
            continue
        if when >= cutoff:
            v["when"] = when
            recent.append(v)
    recent.sort(key=lambda v: v["when"], reverse=True)

    total = len(recent)
    if not a.shorts:
        recent = [v for v in recent if "/shorts/" not in v["url"]]
    dropped_shorts = total - len(recent)

    words = [] if a.all else keywords()
    if words:
        recent = [v for v in recent if matches(v["title"], words)]
    scoped = len(recent)

    if a.per_channel:
        seen, capped = {}, []
        for v in recent:
            n = seen.get(v["channel"], 0)
            if n < a.per_channel:
                seen[v["channel"]] = n + 1
                capped.append(v)
        recent = capped

    missed = (
        f" · UNREADABLE: {', '.join(unreadable_channels)}"
        if unreadable_channels
        else ""
    )
    print(
        f"{len(subs)} subscriptions · {total} uploads in {a.days} days · "
        f"{dropped_shorts} Shorts dropped · {scoped} matched your keywords{missed}\n"
    )
    for v in recent[: a.limit] if a.limit else recent:
        print(f"{v['channel']} | {v['title']}")
        print(f"  {v['when']:%Y-%m-%d %H:%M} | {v['url']}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if "quotaExceeded" in body:
            raise SystemExit(
                "QUOTA_EXCEEDED: YouTube API daily quota exhausted. Resets at "
                "midnight US/Pacific (12:30 IST)."
            )
        raise SystemExit(f"YouTube API HTTP {e.code}: {body[:300]}")

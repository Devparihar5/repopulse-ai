"""Collect daily repository observations and freeze comparable editions."""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1] / "data"
TOPICS = ["llm", "ai-agents", "rag", "machine-learning", "generative-ai", "computer-vision"]


def api(path, body=None):
    headers = {"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
               "User-Agent": "RepoPulse-AI", "Accept": "application/vnd.github+json"}
    request = Request("https://api.github.com/" + path, headers=headers,
                      data=json.dumps(body).encode() if body else None)
    for attempt in range(4):
        try:
            with urlopen(request, timeout=60) as response:
                result = json.load(response)
            if isinstance(result, dict) and result.get("errors"):
                raise RuntimeError(result["errors"])
            return result
        except HTTPError as error:
            if attempt == 3 or error.code not in (403, 429, 500, 502, 503, 504):
                raise
            delay = int(error.headers.get("Retry-After", 2 ** (attempt + 1)))
            if error.headers.get("X-RateLimit-Remaining") == "0":
                delay = max(delay, int(error.headers["X-RateLimit-Reset"]) - int(time.time()) + 1)
            if delay > 120:
                raise
            time.sleep(delay)


def discover(day):
    start = day - timedelta(days=29)
    repos = {}
    for topic in TOPICS:
        query = f"topic:{topic} is:public fork:false archived:false stars:>0 created:{start}..{day}"
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": 100}
        result = api("search/repositories?" + urlencode(params))
        if result["incomplete_results"]:
            raise RuntimeError(f"Incomplete GitHub search for {topic}")
        for item in result["items"]:
            created = item["created_at"][:10]
            if start.isoformat() <= created <= day.isoformat():
                repos.setdefault(item["id"], dict(
                    name=item["full_name"], url=item["html_url"], description=item["description"] or "",
                    created=created, stars=item["stargazers_count"], category=topic,
                ))
    keys = sorted(repos, key=lambda key: (-repos[key]["stars"], key))
    return [repos[key] for key in keys[:20]]


def main():
    now = datetime.now(timezone.utc)
    day = now.date()
    path = ROOT / "editions" / f"{day}.json"
    if path.exists():
        return
    repos = discover(day)
    if not repos:
        raise RuntimeError("No recent repositories found")
    edition = dict(date=str(day), observed=now.isoformat(),
                   start=str(day - timedelta(days=29)), repos=repos)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(edition, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(path)


if __name__ == "__main__":
    main()

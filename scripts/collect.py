"""Collect daily repository observations and freeze comparable editions."""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1] / "data"
TOPICS = ["llm", "ai-agents", "rag", "machine-learning", "generative-ai", "computer-vision"]
FIELDS = "id nameWithOwner description url stargazerCount repositoryTopics(first:30){nodes{topic{name}}} isArchived isFork isPrivate"


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
    ids = set()
    for topic in TOPICS:
        for qualifier in ("", f" created:>={day - timedelta(days=30)}"):
            params = {"q": f"topic:{topic} archived:false fork:false is:public{qualifier}",
                      "sort": "stars", "order": "desc", "per_page": 50}
            result = api("search/repositories?" + urlencode(params))
            if result["incomplete_results"]:
                raise RuntimeError(f"Incomplete GitHub search for {topic}")
            ids.update(item["node_id"] for item in result["items"])
    return ids


def observe(ids):
    rows = {}
    query = "query($ids:[ID!]!){nodes(ids:$ids){... on Repository{" + FIELDS + "}}}"
    for start in range(0, len(ids), 50):
        result = api("graphql", {"query": query, "variables": {"ids": ids[start:start + 50]}})
        for repo in result["data"]["nodes"]:
            if not repo or repo["isFork"] or repo["isArchived"] or repo["isPrivate"]:
                continue
            topics = {t["topic"]["name"] for t in repo["repositoryTopics"]["nodes"]}
            category = next((t for t in TOPICS if t in topics), None)
            if category:
                rows[repo["id"]] = dict(name=repo["nameWithOwner"], url=repo["url"],
                                        description=repo["description"] or "", category=category,
                                        stars=repo["stargazerCount"])
    return rows


def rank(rows, previous):
    eligible = []
    for key, repo in rows.items():
        if key in previous and repo["stars"] > previous[key]:
            gain = repo["stars"] - previous[key]
            eligible.append((key, dict(repo, gain=gain), previous[key]))
    eligible.sort(key=lambda item: (-item[1]["gain"], item[2] != 0,
                                     -Fraction(item[1]["gain"], item[2] or 1), item[0]))
    return [repo for _, repo, _ in eligible[:20]]


def most_starred(rows):
    keys = sorted(rows, key=lambda key: (-rows[key]["stars"], key))
    return [rows[key] for key in keys[:20]]


def save(path, value):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(path)


def main():
    now = datetime.now(timezone.utc)
    day = now.date()
    state = json.loads((ROOT / "state.json").read_text())
    if state.get("date") == day.isoformat():
        if "most_starred" not in state:
            rows = observe(sorted(state["stars"]))
            if not rows:
                raise RuntimeError("Unable to recover baseline repository metadata")
            for key, repo in rows.items():
                repo["stars"] = state["stars"][key]
            state["most_starred"] = most_starred(rows)
            save(ROOT / "state.json", state)
        return
    rows = observe(sorted(set(state.get("stars", {})) | discover(day)))
    if not rows:
        raise RuntimeError("Empty observation")
    if state.get("date") == (day - timedelta(days=1)).isoformat():
        edition = dict(date=str(day), start=state["observed"], end=now.isoformat(),
                       tracked=len(rows), repos=rank(rows, state["stars"]))
        path = ROOT / "editions" / f"{day}.json"
        if not path.exists():
            save(path, edition)
    save(ROOT / "state.json", dict(date=str(day), observed=now.isoformat(), most_starred=most_starred(rows),
                                  stars={key: value["stars"] for key, value in rows.items()}))


if __name__ == "__main__":
    main()

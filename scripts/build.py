"""Build portable, server-rendered HTML from frozen JSON editions."""
import json
import shutil
from datetime import datetime
from html import escape
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def stamp(value):
    return datetime.fromisoformat(value).strftime("%d %b %Y, %H:%M UTC")


def render(edition, dates, prefix):
    options = "".join(f'<li><a href="{prefix}editions/{d}/">{d}</a></li>' for d in dates)
    archive = options or "<li>Past editions will appear here.</li>"
    cards = []
    repos = edition["repos"] if edition else []
    for i, repo in enumerate(repos, 1):
        cards.append(f"""<li class="row"><span class="rank">{i:02}</span><div>
<h2><a href="{escape(repo['url'], quote=True)}">{escape(repo['name'])}</a></h2>
<p>{escape(repo['description'])}</p><small>{escape(repo['category'])} · Created <time datetime="{repo['created']}">{repo['created']}</time></small>
</div><strong>{repo['stars']:,}<small>stars</small></strong></li>""")
    detail = (f"Created {edition['start']} through {edition['date']} · Updated {stamp(edition['observed'])}"
              if edition else "Awaiting the first edition")
    status = "No repositories in this edition."
    heading = f"Edition · {edition['date']}" if edition else "Most starred"
    content = '<ol>' + "".join(cards) + '</ol>' if cards else f'<p class="empty">{status}</p>'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{heading} | RepoPulse AI</title><link rel="stylesheet" href="{prefix}style.css"></head>
<body><header><a class="brand" href="{prefix}">RepoPulse <b>AI</b></a>
<nav><a href="{prefix}">Latest</a><a href="#archive">Archive</a></nav></header>
<main><section class="intro"><small>{heading}</small><h1>Top new AI repositories</h1>
<p>The 20 most-starred projects across our AI topics, created in the last 30 days.</p></section>
<p class="window">{detail}</p>{content}
<section id="archive"><h2>Edition archive</h2><ul>{archive}</ul></section>
<footer><a href="https://github.com/Devparihar5/repopulse-ai#ranking">How the ranking works ↗</a></footer>
</main></body></html>"""


def build(data, output):
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy(PROJECT / "web/style.css", output)
    editions = sorted((data / "editions").glob("*.json"), reverse=True)
    dates = [p.stem for p in editions]
    current = read(editions[0]) if editions else None
    (output / "index.html").write_text(render(current, dates, "./"))
    for path in editions:
        folder = output / "editions" / path.stem
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(render(read(path), dates, "../../"))


if __name__ == "__main__":
    build(PROJECT / "data", PROJECT / "dist")

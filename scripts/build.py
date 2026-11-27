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


def render(edition, dates, state, prefix):
    options = "".join(f'<li><a href="{prefix}editions/{d}/">{d}</a></li>' for d in dates)
    archive = options or "<li>Past editions will appear here.</li>"
    cards = []
    repos = edition["repos"] if edition else state.get("most_starred", [])
    for i, repo in enumerate(repos, 1):
        metric = f"+{repo['gain']:,}" if edition else f"{repo['stars']:,}"
        label = "net stars" if edition else "total stars"
        cards.append(f"""<li class="row"><span class="rank">{i:02}</span><div>
<h2><a href="{escape(repo['url'], quote=True)}">{escape(repo['name'])}</a></h2>
<p>{escape(repo['description'])}</p><small>{escape(repo['category'])} · {repo['stars']:,} total stars</small>
</div><strong>{metric}<small>{label}</small></strong></li>""")
    if edition:
        detail = f"{stamp(edition['start'])} — {stamp(edition['end'])} · {edition['tracked']:,} repositories tracked"
        status = "No tracked repositories gained stars during this window."
    else:
        detail = (f"Baseline recorded {stamp(state['observed'])} · {len(state['stars']):,} repositories tracked"
                  if state else "Awaiting the first daily observation")
        status = "The first ranking appears after two consecutive daily observations."
    heading = f"Edition · {edition['date']}" if edition else "Most starred"
    content = '<ol>' + "".join(cards) + '</ol>' if cards else f'<p class="empty">{status}</p>'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{heading} | RepoPulse AI</title><link rel="stylesheet" href="{prefix}style.css"></head>
<body><header><a class="brand" href="{prefix}">RepoPulse <b>AI</b></a>
<nav><a href="{prefix}">Latest</a><a href="#archive">Archive</a></nav></header>
<main><section class="intro"><small>{heading}</small><h1>{'Trending AI repositories' if edition else 'Top AI repositories'}</h1>
<p>{'The top 20 tracked projects by daily net star gain.' if edition else 'The 20 most-starred tracked projects. Daily gains appear after the next consecutive observation.'}</p></section>
<p class="window">{detail}</p>{content}
<section id="archive"><h2>Edition archive</h2><ul>{archive}</ul></section>
<footer><a href="https://github.com/Devparihar5/repopulse-ai#ranking">How the ranking works ↗</a></footer>
</main></body></html>"""


def build(data, output):
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy(PROJECT / "web/style.css", output)
    state = read(data / "state.json")
    editions = sorted((data / "editions").glob("*.json"), reverse=True)
    dates = [p.stem for p in editions]
    current = read(editions[0]) if editions else None
    (output / "index.html").write_text(render(current, dates, state, "./"))
    for path in editions:
        folder = output / "editions" / path.stem
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(render(read(path), dates, state, "../../"))


if __name__ == "__main__":
    build(PROJECT / "data", PROJECT / "dist")

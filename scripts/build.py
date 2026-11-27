"""Build portable, server-rendered HTML from frozen JSON editions."""
import json
import shutil
from datetime import datetime
from html import escape
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


PAGE_STYLES = (PROJECT / "web/style.css").read_text()
THEME_SCRIPT = (PROJECT / "web/theme.js").read_text()


def read(path):
    return json.loads(path.read_text())


def stamp(value):
    return datetime.fromisoformat(value).strftime("%d %b %Y, %H:%M UTC")


def render(edition, dates, prefix):
    options = "".join(f'<li><a href="{prefix}editions/{d}/">{d}</a></li>' for d in dates)
    archive = options or "<li>Past editions will appear here.</li>"
    cards = []
    repos = edition["repos"] if edition else []
    bars = []
    for i, repo in enumerate(repos, 1):
        owner, _, name = repo["name"].partition("/")
        url = escape(repo["url"], quote=True)
        if i <= 5:
            width = 100 * repo["stars"] / max(1, repos[0]["stars"])
            bars.append(f'<li><span>{escape(name)}</span><i style="--width:{width:.2f}%"></i><b>{repo["stars"]:,}</b></li>')
        created = datetime.fromisoformat(repo["created"]).strftime("%d %b %Y")
        cards.append(f"""<li class="row"><span class="rank">{i:02}</span><div class="project">
<small>{escape(owner)}</small><h2><a href="{url}">{escape(name)} <span aria-hidden="true">↗</span></a></h2>
<p>{escape(repo['description'])}</p><div class="meta"><b>{escape(repo['category'])}</b>
<span>Created <time datetime="{repo['created']}">{created}</time></span></div></div>
<strong><span aria-hidden="true">☆</span> {repo['stars']:,}<small>GitHub stars</small></strong></li>""")
    heading = datetime.fromisoformat(edition["date"]).strftime("%d %B %Y") if edition else "First edition"
    detail = f"Updated {stamp(edition['observed'])}" if edition else "Awaiting the first edition"
    chart = ('<figure><figcaption>Top five by stars</figcaption><ol class="bars">' +
             "".join(bars) + '</ol></figure>') if bars else ""
    content = '<ol class="leaderboard">' + "".join(cards) + '</ol>' if cards else '<p>No repositories in this edition.</p>'
    return f"""<!doctype html><html lang="en" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>{THEME_SCRIPT}</script>
<title>{heading} | RepoPulse AI</title><style>{PAGE_STYLES}</style></head>
<body><header><div class="wrap mast"><a class="brand" href="{prefix}"><em aria-hidden="true">∿</em> RepoPulse <b>AI</b></a>
<nav aria-label="Main"><a href="{prefix}">Latest</a><a href="#archive">Archive</a><button id="theme-switch" type="button" hidden>Light theme</button></nav></div></header>
<main class="wrap"><section class="intro"><div><small class="edition">Daily edition · {heading}</small>
<h1>Top new <em>AI</em><br>repositories.</h1>
<p>The most-starred AI projects created in the last 30 days.</p></div>{chart}</section>
<section aria-label="Repository leaderboard"><div class="sectionhead"><h2>Leaderboard <small>{len(repos)}</small></h2><span>{detail}</span></div>{content}</section>
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

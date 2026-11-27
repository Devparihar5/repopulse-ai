# RepoPulse AI

A daily leaderboard of AI repositories gaining stars on GitHub. Browse the latest ranking and permanent dated editions.

## Ranking

At 02:37 UTC (08:07 IST) the scheduled workflow searches six AI topics. For each it takes up to 50 repositories by stars overall and up to 50 created in the last 30 days. It combines those candidates with yesterday’s watchlist by stable repository ID, refreshes counts, and excludes forks, archived projects, and repositories without a matching topic among their first 30 topics. Coverage is limited to the tracked pool.

Projects with two consecutive UTC-day observations qualify. Daily gain equals current stars minus previous stars. Only positive gains appear. Ties favor greater percentage growth (zero baseline first), then repository ID. Editions contain at most 20 entries. Run times may vary. The first collection establishes a baseline. After a missed day the next collection establishes a fresh baseline.

## Run locally

Requires Python 3.10+ and uses the standard library.

    python -m unittest discover -s tests
    python scripts/build.py
    python -m http.server 8000 --directory dist

Open http://localhost:8000. To collect live data locally, set GITHUB_TOKEN to a GitHub API token, then run python scripts/collect.py before building.

## GitHub Pages

In Settings → Pages choose GitHub Actions as the build source. The Daily rankings and Pages workflow runs on pushes to main, on schedule, or manually. Its build job needs permission to commit data to main. It builds the static site, persists the latest snapshot and immutable dated rankings, then uploads the Pages artifact. If a collection fails, the existing live edition stays available.

# RepoPulse AI

A daily leaderboard of newly created, highly starred AI repositories on GitHub. Browse the latest ranking and permanent dated editions.

## Ranking

At 02:37 UTC (08:07 IST), GitHub Actions searches for public, non-fork, unarchived projects with at least one star created during the latest 30 UTC calendar dates, including the edition date. For each configured AI topic it requests the 100 highest-starred matches, merges overlapping results by repository ID, and lists up to 20 by total stars. Ties among retrieved projects use repository ID. Each dated edition freezes its counts and links.

## Run locally

Requires Python 3.10+ and uses the standard library.

    python -m unittest discover -s tests
    python scripts/build.py
    python -m http.server 8000 --directory dist

Open http://localhost:8000. To collect live data locally, set GITHUB_TOKEN to a GitHub API token, then run python scripts/collect.py before building.

## GitHub Pages

In Settings → Pages choose GitHub Actions as the build source. The Daily rankings and Pages workflow runs on pushes to main, on schedule, or manually. Its build job needs permission to commit data to main. It builds the static site, persists the latest snapshot and immutable dated rankings, then uploads the Pages artifact. If a collection fails, the existing live edition stays available.

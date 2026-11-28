import unittest
from datetime import date
from unittest.mock import patch
from urllib.parse import unquote_plus

from scripts import build, collect


class RecentRankingTests(unittest.TestCase):
    def test_window_order_deduplication_and_links(self):
        items = [dict(id=i, full_name=f"ai/model-{i}", html_url=f"https://github.com/ai/model-{i}",
                      description="Text & images", created_at="2026-10-29T00:00:00Z",
                      stargazers_count=i) for i in range(1, 26)]
        items.append(dict(items[-1], id=26, created_at="2026-10-28T23:59:59Z", stargazers_count=999))
        with patch.object(collect, "api", return_value={"items": items, "incomplete_results": False}) as api:
            repos = collect.discover(date(2026, 11, 27))
        self.assertTrue(all("created:2026-10-29..2026-11-27" in unquote_plus(c.args[0])
                            for c in api.call_args_list))
        self.assertEqual([r["stars"] for r in repos], list(range(25, 5, -1)))
        edition = dict(date="2026-11-27", start="2026-10-29", observed="2026-11-27T00:00:00Z", repos=repos)
        html = build.render(edition, [edition["date"]], "./")
        self.assertEqual(html.count('<h2><a href="https://github.com/ai/model-'), 20)
        self.assertIn('datetime="2026-10-29"', html)

    def test_previous_edition_excluded_before_ranking(self):
        items = [dict(id=i, full_name=f"ai/model-{i}", html_url=f"https://github.com/ai/model-{i}",
                      description="", created_at="2026-11-27", stargazers_count=i)
                 for i in range(1, 25)]
        previous = [{"name": "AI/MODEL-24"}, {"name": "ai/old-name", "id": 23}]
        with patch.object(collect, "api", return_value={"items": items, "incomplete_results": False}):
            repos = collect.discover(date(2026, 11, 28), previous)
        self.assertEqual([repo["id"] for repo in repos], list(range(22, 2, -1)))

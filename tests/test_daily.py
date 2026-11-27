import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build, collect


class DailyTests(unittest.TestCase):
    def test_ranking(self):
        previous = {str(i): i for i in range(24)}
        rows = {key: {"stars": old + 2, "id": key} for key, old in previous.items()}
        rows.update(new={"stars": 900}, stale={"stars": 0})
        previous["stale"] = 3
        result = collect.rank(rows, previous)
        self.assertEqual([r["id"] for r in result], [str(i) for i in range(20)])
        self.assertTrue(all(r["gain"] == 2 for r in result))

    def test_collection_and_build(self):
        from datetime import datetime, timezone, timedelta
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp)
            (data / "editions").mkdir()
            (data / "state.json").write_text("{}")
            repo = dict(name="org/example", stars=9, category="rag", url="https://github.com/org/example",
                        description="Read <text>")
            now = datetime(2026, 1, 1, tzinfo=timezone.utc)
            with patch.object(collect, "ROOT", data), patch.object(collect, "datetime") as clock, \
                    patch.object(collect, "discover", return_value={"id"}), \
                    patch.object(collect, "observe", return_value={"id": repo}) as observe:
                clock.now.return_value = now
                collect.main()
                collect.main()
                build.build(data, data / "site")
                html = (data / "site/index.html").read_text()
                self.assertIn('href="https://github.com/org/example"', html)
                self.assertIn("20 most-starred", html)
                self.assertEqual(observe.call_count, 1)
                self.assertFalse(list((data / "editions").glob("*.json")))
                clock.now.return_value = now + timedelta(days=1)
                repo["stars"] += 4
                collect.main()
                clock.now.return_value = now + timedelta(days=3)
                collect.main()
            edition, = (data / "editions").glob("*.json")
            self.assertEqual(json.loads(edition.read_text())["repos"][0]["gain"], 4)
            build.build(data, data / "site")
            for path in ("index.html", "editions/2026-01-02/index.html"):
                self.assertIn("Read &lt;text&gt;", (data / "site" / path).read_text())

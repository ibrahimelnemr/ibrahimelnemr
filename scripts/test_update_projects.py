import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from update_projects import generate, render_card, select_projects, summarize, search_count, languages_panel, fetch_language_bytes


def repo(name, pushed_at="2026-01-01T00:00:00Z", **fields):
    return {"name": name, "pushed_at": pushed_at, **fields}


class ProfileTests(unittest.TestCase):
    def test_excludes_private_forked_archived_and_profile_repositories(self):
        projects = select_projects([
            repo("private", private=True), repo("fork", fork=True),
            repo("archive", archived=True), repo("IbrahimElNemr"),
            repo("ibrahimelnemr.github.io"), repo("empty", pushed_at=None),
            repo("public-project"),
        ])
        self.assertEqual([p["name"] for p in projects], ["public-project"])

    def test_selects_three_most_recent_pushes(self):
        projects = select_projects([
            repo(str(day), f"2026-01-{day:02d}T00:00:00Z") for day in range(1, 9)
        ])
        self.assertEqual([p["name"] for p in projects], ["8", "7", "6"])

    def test_card_escapes_repository_data_in_both_layouts(self):
        project = repo("example", description='A & B <script>"test"</script>', language=None)
        for mobile in (False, True):
            with self.subTest(mobile=mobile):
                card = render_card(project, mobile)
                root = ET.fromstring(card)
                self.assertNotIn("<script>", card)
                self.assertIn("A &amp; B &lt;script&gt;", card)
                self.assertIn("Code", "".join(root.itertext()))

    def test_card_clips_long_content_and_displays_actual_counts(self):
        project = repo("repository-name-" * 8, description="A long description " * 100,
                       language="Python", stargazers_count=12, forks_count=3)
        for mobile in (False, True):
            card = render_card(project, mobile)
            root = ET.fromstring(card)
            texts = [node.text or "" for node in root.iter() if node.tag.endswith('text')]
            self.assertTrue(texts[0].endswith("…"))
            self.assertTrue(texts[2].endswith("…"))
            self.assertIn("12 stars, 3 forks", card)

    def test_public_statistics_exclude_private_data_and_fork_stars(self):
        stats = summarize([
            repo("one", language="Python", stargazers_count=3),
            repo("two", language="Python", stargazers_count=4),
            repo("three", language="Java"),
            repo("fork", fork=True, language="Ruby", stargazers_count=100),
            repo("secret", private=True, language="Secret", stargazers_count=100),
        ], {"followers": 9}, 17, [("Python", 200), ("Java", 100)])
        self.assertEqual(stats, {"repos": 4, "stars": 7, "followers": 9,
                                "prs": 17, "languages": [("Python", 200), ("Java", 100)]})

    def test_generated_assets_are_valid_linked_and_repeatable(self):
        projects = [repo("first", description="A & B"), repo("second")]
        stats = summarize(projects, {"followers": 4}, 12, [])
        markup, assets = generate(projects, stats)
        self.assertEqual(generate(projects, stats), (markup, assets))
        root = ET.fromstring(markup)
        for img in root.findall(".//img"):
            self.assertIn(img.get("src").removeprefix("assets/"), assets)
            self.assertEqual(img.get("align"), "top")
        for source in root.findall(".//source"):
            self.assertIn(source.get("srcset").removeprefix("assets/"), assets)
        links = [a.get("href") for a in root.findall(".//a")]
        self.assertIn("https://ibrahimelnemr.github.io/", links)
        self.assertIn("https://www.linkedin.com/in/ibrahimelnemr/", links)
        self.assertIn("https://github.com/ibrahimelnemr/first", links)
        for svg in assets.values():
            ET.fromstring(svg)
            self.assertNotIn("<script", svg)
            self.assertNotIn("foreignObject", svg)

    def test_empty_languages_and_other_bucket(self):
        self.assertIn("No language data yet", languages_panel({"languages": []}))
        svg = languages_panel({"languages": [(str(i), 1) for i in range(8)]})
        self.assertIn("Other · 37.5%", svg)
        ET.fromstring(svg)

    @patch("update_projects.api")
    def test_languages_aggregate_bytes_including_secondary_languages(self, api):
        api.side_effect = [{"Python": 300, "HTML": 100}, {"Python": 100, "TypeScript": 500}, {}]
        result = fetch_language_bytes([
            repo("first", language="Python"), repo("second", language="TypeScript"),
            repo("empty", language=None), repo("fork", fork=True), repo("secret", private=True),
        ])
        self.assertEqual(result, [("TypeScript", 500), ("Python", 400), ("HTML", 100)])
        self.assertEqual([call.args[0] for call in api.call_args_list], [
            "repos/ibrahimelnemr/first/languages", "repos/ibrahimelnemr/second/languages",
            "repos/ibrahimelnemr/empty/languages",
        ])

    def test_language_percentages_and_bar_are_weighted_by_bytes(self):
        for mobile in (False, True):
            svg = languages_panel({"languages": [("Python", 900), ("HTML", 100)]}, mobile)
            self.assertIn("Python · 90.0%", svg)
            self.assertIn("HTML · 10.0%", svg)
            root = ET.fromstring(svg)
            bars = [n for n in root.iter() if n.tag.endswith("rect") and n.get("height") == "8"]
            self.assertEqual(len(bars), 2)
            self.assertAlmostEqual(float(bars[0].get("width")) / float(bars[1].get("width")), 9)

    @patch("update_projects.api", return_value={"incomplete_results": True, "total_count": 12})
    def test_incomplete_search_fails_instead_of_publishing_inaccurate_statistics(self, api):
        with self.assertRaises(ValueError):
            search_count("is:pr is:public")


if __name__ == "__main__":
    unittest.main()

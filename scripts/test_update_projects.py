import unittest
import xml.etree.ElementTree as ET

from update_projects import END, START, THEMES, render_card, render_projects, select_projects, update_readme


def repo(name, pushed_at="2026-01-01T00:00:00Z", **fields):
    return {"name": name, "pushed_at": pushed_at, **fields}


class ProjectTests(unittest.TestCase):
    def test_excludes_private_forked_archived_and_profile_repositories(self):
        projects = select_projects([
            repo("private", private=True),
            repo("fork", fork=True),
            repo("archive", archived=True),
            repo("IbrahimElNemr"),
            repo("ibrahimelnemr.github.io"),
            repo("empty", pushed_at=None),
            repo("public-project"),
        ])
        self.assertEqual([p["name"] for p in projects], ["public-project"])

    def test_selects_six_most_recent_pushes(self):
        projects = select_projects([
            repo(str(day), f"2026-01-{day:02d}T00:00:00Z") for day in range(1, 9)
        ])
        self.assertEqual([p["name"] for p in projects], ["8", "7", "6", "5", "4", "3"])

    def test_card_escapes_repository_data_and_supports_both_themes(self):
        project = repo("example", description='A & B <script>"test"</script>', language=None)
        for theme in THEMES:
            with self.subTest(theme=theme):
                card = render_card(project, theme)
                root = ET.fromstring(card)
                self.assertNotIn("<script>", card)
                self.assertIn("A &amp; B &lt;script&gt;", card)
                self.assertIn('viewBox="0 0 440 166"', card)
                self.assertIn("Code", "".join(root.itertext()))

    def test_card_limits_long_descriptions_and_displays_actual_counts(self):
        card = render_card(repo(
            "example", description="A long description " * 100,
            language="Python", stargazers_count=12, forks_count=3,
        ), "dark")
        root = ET.fromstring(card)
        body = [node.text for node in root.iter() if node.get("class") == "body"]
        self.assertLessEqual(len(body), 2)
        self.assertTrue(body[-1].endswith("…"))
        self.assertIn("12 stars, 3 forks", card)

    def test_cards_link_to_repositories_with_light_and_dark_images(self):
        markup = render_projects([repo("first"), repo("second"), repo("third")])
        root = ET.fromstring(f"<div>{markup}</div>")
        self.assertEqual(len(root.findall("p")), 2)
        self.assertEqual(len(root.findall(".//a")), 3)
        self.assertEqual(len(root.findall(".//source")), 3)
        self.assertIn('href="https://github.com/ibrahimelnemr/first"', markup)
        self.assertIn('src="assets/projects/first-light.svg"', markup)
        self.assertIn('srcset="assets/projects/first-dark.svg"', markup)

    def test_preserves_other_content_and_is_repeatable(self):
        content = f"Portfolio link\n{START}\nold projects\n{END}\nOther link\n"
        projects = [repo("example")]
        updated = update_readme(content, projects)
        self.assertTrue(updated.startswith(f"Portfolio link\n{START}\n"))
        self.assertTrue(updated.endswith(f"{END}\nOther link\n"))
        self.assertNotIn("old projects", updated)
        self.assertEqual(update_readme(updated, projects), updated)

    def test_missing_duplicate_or_reversed_markers_fail(self):
        for content in ["no markers", f"{START}{START}{END}", f"{END}{START}"]:
            with self.subTest(content=content), self.assertRaises(ValueError):
                update_readme(content, [repo("example")])


if __name__ == "__main__":
    unittest.main()

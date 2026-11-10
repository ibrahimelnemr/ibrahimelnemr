import unittest

from update_projects import END, START, render_projects, select_projects, update_readme


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

    def test_descriptions_cannot_break_the_table_or_insert_html(self):
        table = render_projects([
            repo("example", description="A | B\n<script>[link](url)*_`", language=None)
        ])
        self.assertEqual(len(table.splitlines()), 3)
        self.assertEqual(table.splitlines()[-1].count("|"), 4)
        self.assertNotIn("<script>", table)
        self.assertIn("&lt;script&gt;", table)
        self.assertIn("&#91;link&#93;", table)
        self.assertTrue(table.endswith("| — |"))

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

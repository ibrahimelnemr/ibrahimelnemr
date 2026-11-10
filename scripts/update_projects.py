"""Refresh the profile README: python3 scripts/update_projects.py.

Only public repositories are used. GITHUB_TOKEN is optional for local runs.
"""

import html
import json
import os
from pathlib import Path
import urllib.request


USERNAME = "ibrahimelnemr"
LIMIT = 6
EXCLUDED = {USERNAME, f"{USERNAME}.github.io"}
START = "<!-- RECENT-PROJECTS:START -->"
END = "<!-- RECENT-PROJECTS:END -->"
README = Path(__file__).resolve().parents[1] / "README.md"


def fetch_repositories():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-projects",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    repositories = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?sort=pushed&direction=desc&per_page=100&page={page}"
        )
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=headers), timeout=30
        ) as response:
            batch = json.load(response)
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def select_projects(repositories):
    eligible = [
        repo for repo in repositories
        if not repo.get("private")
        and not repo.get("fork")
        and not repo.get("archived")
        and repo["name"].lower() not in EXCLUDED
        and repo.get("pushed_at")
    ]
    return sorted(eligible, key=lambda repo: repo["pushed_at"], reverse=True)[:LIMIT]


def escape_cell(value):
    # Keep repository descriptions inside one Markdown table cell.
    text = html.escape(" ".join(str(value).split()))
    for char in "|\\[]*_`":
        text = text.replace(char, f"&#{ord(char)};")
    return text


def render_projects(projects):
    lines = [
        "| Project | Description | Language |",
        "| --- | --- | --- |",
    ]
    for repo in projects:
        name = escape_cell(repo["name"])
        url = f"https://github.com/{USERNAME}/{repo['name']}"
        description = escape_cell(repo.get("description") or "—")
        language = escape_cell(repo.get("language") or "—")
        lines.append(f"| [{name}]({url}) | {description} | {language} |")
    return "\n".join(lines)


def update_readme(content, projects):
    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError("README must contain exactly one pair of project markers")
    before, remaining = content.split(START)
    _, after = remaining.split(END)
    return f"{before}{START}\n\n{render_projects(projects)}\n\n{END}{after}"


def main():
    projects = select_projects(fetch_repositories())
    if not projects:
        raise ValueError("No eligible projects returned; leaving README unchanged")
    content = README.read_text(encoding="utf-8")
    updated = update_readme(content, projects)
    if updated != content:
        README.write_text(updated, encoding="utf-8")
        print(f"Updated README with {len(projects)} projects")
    else:
        print("README is already up to date")


if __name__ == "__main__":
    main()

"""Refresh the profile README: python3 scripts/update_projects.py.

Only public repositories are used. GITHUB_TOKEN is optional for local runs.
"""

import html
import json
import os
from pathlib import Path
import textwrap
import urllib.request


USERNAME = "ibrahimelnemr"
LIMIT = 6
EXCLUDED = {USERNAME, f"{USERNAME}.github.io"}
START = "<!-- RECENT-PROJECTS:START -->"
END = "<!-- RECENT-PROJECTS:END -->"
README = Path(__file__).resolve().parents[1] / "README.md"
CARDS = README.parent / "assets" / "projects"
THEMES = {
    "light": {"bg": "#ffffff", "border": "#d1d9e0", "title": "#0969da", "text": "#59636e"},
    "dark": {"bg": "#0d1117", "border": "#30363d", "title": "#58a6ff", "text": "#9198a1"},
}
LANGUAGE_COLORS = {
    "HTML": "#e34c26", "Python": "#3572a5", "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a", "Java": "#b07219", "Dart": "#00b4ab",
    "Swift": "#f05138", "CSS": "#663399", "Jupyter Notebook": "#da5b0b",
}


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


def shorten(text, width):
    return text if len(text) <= width else text[:width - 1] + "…"


def render_card(repo, theme):
    colors = THEMES[theme]
    name = html.escape(shorten(repo["name"], 35))
    description = " ".join((repo.get("description") or "Explore the repository →").split())
    lines = textwrap.wrap(description, width=55, break_long_words=True)[:2]
    if len(description) > len(" ".join(lines)):
        lines[-1] = shorten(lines[-1], 51) + "…"
    description_svg = "".join(
        f'<text x="20" y="{76 + index * 20}" class="body">{html.escape(line)}</text>'
        for index, line in enumerate(lines)
    )
    language = repo.get("language") or "Code"
    language_color = LANGUAGE_COLORS.get(language, "#8b949e")
    stars = int(repo.get("stargazers_count", 0))
    forks = int(repo.get("forks_count", 0))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="440" height="166" viewBox="0 0 440 166" role="img" aria-labelledby="title desc">
  <title id="title">{html.escape(repo["name"])} — {html.escape(language)}</title>
  <desc id="desc">{html.escape(description)}. {stars} stars, {forks} forks.</desc>
  <style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
    .body {{ font-size: 13px; fill: {colors["text"]}; }}
    .meta {{ font-size: 12px; fill: {colors["text"]}; }}
  </style>
  <rect x="0.5" y="0.5" width="439" height="165" rx="7" fill="{colors["bg"]}" stroke="{colors["border"]}"/>
  <g transform="translate(20 23)" fill="none" stroke="{colors["text"]}" stroke-width="1.3" stroke-linejoin="round">
    <path d="M2 1h11v14H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2Zm0 10h11M3 1v10"/>
  </g>
  <text x="43" y="36" fill="{colors["title"]}" font-size="14" font-weight="600">{name}</text>
  <rect x="371" y="21" width="49" height="20" rx="10" fill="none" stroke="{colors["border"]}"/>
  <text x="395.5" y="35" text-anchor="middle" class="meta" font-size="11">Public</text>
  {description_svg}
  <circle cx="25" cy="137" r="6" fill="{language_color}"/>
  <text x="38" y="141" class="meta">{html.escape(language)}</text>
  <g transform="translate(205 129)" fill="none" stroke="{colors["text"]}" stroke-width="1.2">
    <path d="m8 0 2.3 4.8 5.2.7-3.8 3.7.9 5.3L8 12l-4.6 2.5.9-5.3L.5 5.5l5.2-.7Z"/>
  </g>
  <text x="228" y="141" class="meta">{stars}</text>
  <g transform="translate(282 130)" fill="none" stroke="{colors["text"]}" stroke-width="1.3">
    <circle cx="2" cy="2" r="2"/><circle cx="12" cy="2" r="2"/><circle cx="7" cy="13" r="2"/>
    <path d="M2 4v2c0 2 5 1 5 5m5-7v2c0 2-5 1-5 5"/>
  </g>
  <text x="306" y="141" class="meta">{forks}</text>
</svg>
'''


def render_projects(projects):
    lines = []
    for index, repo in enumerate(projects):
        if index % 2 == 0:
            lines.append('<p align="center">')
        name = html.escape(repo["name"], quote=True)
        url = f"https://github.com/{USERNAME}/{repo['name']}"
        lines.extend([
            f'  <a href="{url}">',
            '    <picture>',
            f'      <source media="(prefers-color-scheme: dark)" srcset="assets/projects/{name}-dark.svg" />',
            f'      <img src="assets/projects/{name}-light.svg" width="400" alt="{name}" />',
            '    </picture>',
            '  </a>',
        ])
        if index % 2 == 1 or index == len(projects) - 1:
            lines.append('</p>')
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
    CARDS.mkdir(parents=True, exist_ok=True)
    expected = set()
    for project in projects:
        for theme in THEMES:
            filename = f'{project["name"]}-{theme}.svg'
            expected.add(filename)
            (CARDS / filename).write_text(render_card(project, theme), encoding="utf-8")
    for path in CARDS.glob("*.svg"):
        if path.name not in expected:
            path.unlink()
    if updated != content:
        README.write_text(updated, encoding="utf-8")
        print(f"Updated README with {len(projects)} projects")
    else:
        print("README is already up to date")


if __name__ == "__main__":
    main()

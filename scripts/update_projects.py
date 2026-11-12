"""Generate the space-themed profile from public GitHub data (no dependencies)."""

from collections import Counter
from datetime import datetime
import html
import json
import os
from pathlib import Path
import textwrap
import urllib.parse
import urllib.request

USERNAME = "ibrahimelnemr"
LIMIT = 3
EXCLUDED = {USERNAME, f"{USERNAME}.github.io"}
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LANGUAGE_COLORS = {
    "HTML": "#fb9276", "Python": "#7bb7ec", "TypeScript": "#76a9ff",
    "JavaScript": "#f1da78", "Java": "#dbad92", "Dart": "#65d9d0",
    "Swift": "#fa9a9a", "CSS": "#c0a0fa", "Jupyter Notebook": "#eba3c8",
}
ACCENT = "#72e0cf"
TEXT = "#edf3fb"
MUTED = "#a0b3c9"
LINKEDIN_PATH = "M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854zm4.943 12.248V6.169H2.542v7.225zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248S2.4 3.226 2.4 3.934c0 .694.521 1.248 1.327 1.248zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0-1.845.7-2.165 1.193v.025h-.016l.016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225z"


def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "github-profile"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(
        f"https://api.github.com/{path}", headers=headers
    ), timeout=30) as response:
        return json.load(response)


def fetch_repositories():
    repositories = []
    page = 1
    while True:
        batch = api(f"users/{USERNAME}/repos?sort=pushed&direction=desc&per_page=100&page={page}")
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def search_count(query):
    result = api("search/issues?" + urllib.parse.urlencode({"q": query, "per_page": 1}))
    if result.get("incomplete_results"):
        raise ValueError("GitHub search was incomplete; keeping the previous profile")
    return result["total_count"]


def select_projects(repositories):
    eligible = [repo for repo in repositories
                if not repo.get("private") and not repo.get("fork")
                and not repo.get("archived") and repo["name"].lower() not in EXCLUDED
                and repo.get("pushed_at")]
    return sorted(eligible, key=lambda repo: repo["pushed_at"], reverse=True)[:LIMIT]


def summarize(repositories, user, prs):
    public = [r for r in repositories if not r.get("private")]
    original = [r for r in public if not r.get("fork")]
    languages = Counter(r["language"] for r in original if r.get("language"))
    return {"repos": len(public), "stars": sum(r.get("stargazers_count", 0) for r in original),
            "followers": user["followers"], "prs": prs,
            "languages": languages.most_common()}


def text(x, y, content, size=18, color=TEXT, weight=400, extra=""):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}" {extra}>{html.escape(str(content))}</text>')


def arrow(x, y):
    return (f'<path d="M{x} {y+12}l12-12m-12 0h12v12" fill="none" '
            f'stroke="{ACCENT}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')


def panel(width, height, content, title, description="", offset=0, full_width=None):
    full_width = full_width or width
    # Every image has the same edge color. Top-aligned adjacent images form a single panel.
    stars = "".join(f'<circle cx="{(i*173+73)%width}" cy="{(i*37+13)%height}" r="{.6 if i%3 else 1.1}" fill="#9ac6e9" opacity="{.12 if i%2 else .25}"/>' for i in range(14))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(description or title)}</desc>
<defs><linearGradient id="space" gradientUnits="userSpaceOnUse" x1="{-offset}" x2="{full_width-offset}" y1="0" y2="0"><stop stop-color="#0b1220"/><stop offset=".55" stop-color="#0c1623"/><stop offset="1" stop-color="#10252e"/></linearGradient></defs>
<style>text {{font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;}} .orbit {{transform-origin:0 0;animation:orbit 24s linear infinite}} .twinkle {{animation:twinkle 5s ease-in-out infinite alternate}} @keyframes orbit {{to {{transform:rotate(360deg)}}}} @keyframes twinkle {{to {{opacity:.35}}}} @media(prefers-reduced-motion:reduce) {{.orbit,.twinkle {{animation:none}}}}</style>
<rect width="{width}" height="{height}" fill="url(#space)"/>
<g class="twinkle">{stars}</g>{content}</svg>
'''


def header(mobile=False):
    w = 420 if mobile else 840
    size = 35 if mobile else 52
    x = 26 if mobile else 40
    orbit = f'''<g transform="translate({w-91} 77)" opacity=".65">
<ellipse rx="57" ry="22" fill="none" stroke="#345868" transform="rotate(-28)"/>
<circle r="42" fill="none" stroke="#345868"/><circle r="5" fill="{ACCENT}"/>
<g class="orbit"><circle cx="42" r="3" fill="{ACCENT}"/></g></g>'''
    content = orbit + f'<path d="M{x} 40h32" stroke="{ACCENT}" stroke-width="3" stroke-linecap="round"/>'
    content += text(x, 108 if mobile else 114, "Ibrahim El Nemr", size, weight=650, extra='letter-spacing="-1.5"')
    content += text(x, 146 if mobile else 157, "@ibrahimelnemr", 16, MUTED)
    if mobile:
        # Keep the orbital drawing away from the name on narrow screens.
        content = content.replace('translate(329 77)', 'translate(347 42) scale(.5)')
    return panel(w, 180 if mobile else 194, content, "Ibrahim El Nemr · @ibrahimelnemr")


def button(kind, mobile=False):
    w = 210 if mobile else 420
    x = 26 if kind == "portfolio" else 8
    right = 8 if kind == "portfolio" else (26 if mobile else 40)
    if not mobile and kind == "portfolio":
        x = 40
    rectw = w-x-right
    icon = (f'<g transform="translate({x+17} 22)" stroke="{ACCENT}" stroke-width="1.4" fill="none"><circle cx="8" cy="8" r="8"/><ellipse cx="8" cy="8" rx="3.5" ry="8"/><path d="M0 8h16"/></g>' if kind == "portfolio" else f'<g transform="translate({x+17} 22)" fill="{ACCENT}"><path d="{LINKEDIN_PATH}"/></g>')
    label = "Portfolio" if kind == "portfolio" else "LinkedIn"
    content = f'<rect x="{x}" y="7" width="{rectw}" height="47" rx="9" fill="#11232e" stroke="#2d555e"/>' + icon
    content += text(x+43, 35, label, 15 if mobile else 18, weight=550) + arrow(w-right-29, 24)
    return panel(w, 76, content, label + " ↗", offset=w if kind == "linkedin" else 0, full_width=w*2)


def heading(label, number, mobile=False, subtitle=""):
    w, x = (420, 26) if mobile else (840, 40)
    content = text(x, 38, number, 12, ACCENT, 600, 'letter-spacing="1.5"')
    content += text(x+32, 39, label, 24, weight=600)
    content += f'<path d="M{x} 57H{w-x}" stroke="#263b4e"/>'
    if subtitle:
        content += text(x, 82, subtitle, 13, MUTED)
    return panel(w, 98 if subtitle else 72, content, label)


def shorten(value, width):
    return value if len(value) <= width else value[:width-1] + "…"


def render_card(repo, mobile=False):
    w, x, height = (420, 26, 184) if mobile else (840, 40, 150)
    name = shorten(repo["name"], 28 if mobile else 55)
    desc = " ".join((repo.get("description") or "Explore the code and latest updates.").split())
    width = 43 if mobile else 88
    lines = textwrap.wrap(desc, width=width, break_long_words=True)[:2]
    if len(desc) > len(" ".join(lines)):
        lines[-1] = shorten(lines[-1], width-1) + "…"
    language = repo.get("language") or "Code"
    color = LANGUAGE_COLORS.get(language, "#a0b3c9")
    stars = int(repo.get("stargazers_count", 0))
    forks = int(repo.get("forks_count", 0))
    pushed = datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00")).strftime("%d %b %Y")
    content = f'<rect x="{x}" y="4" width="{w-2*x}" height="{height-14}" rx="12" fill="#101e2d" stroke="#263e50"/>'
    content += text(x+18, 36, name, 18 if mobile else 21, weight=600) + arrow(w-x-32, 22)
    for i, line in enumerate(lines):
        content += text(x+18, 65+i*22, line, 14 if mobile else 16, MUTED)
    y = 119
    content += f'<circle cx="{x+22}" cy="{y-5}" r="4" fill="{color}"/>'
    content += text(x+34, y, language, 13, MUTED)
    content += text(x+(190 if mobile else 220), y, f"☆ {stars}  ·  {forks} forks", 13, MUTED)
    content += text(x+18 if mobile else w-x-18, 151 if mobile else y,
                    f"Pushed {pushed}", 12, MUTED, extra='' if mobile else 'text-anchor="end"')
    return panel(w, height, content, repo["name"], f"{desc} {language}. {stars} stars, {forks} forks. Pushed {pushed}.")


def stats_panel(stats, mobile=False):
    w, x = (420, 26) if mobile else (840, 40)
    height = 174 if mobile else 94
    content = ""
    entries = [(stats['repos'], 'Public repos'), (stats['stars'], 'Stars earned'),
               (stats['prs'], 'PRs opened'), (stats['followers'], 'Followers')]
    for i, (value, label) in enumerate(entries):
        col, row = (i % 2, i // 2) if mobile else (i, 0)
        xx = x + col*((w-2*x)/(2 if mobile else 4))
        yy = 34+row*80
        content += text(xx+14, yy, value, 31, TEXT, 650)
        content += text(xx+14, yy+24, label, 14, MUTED)
    return panel(w, height, content, "GitHub activity", "; ".join(f"{v} {label}" for v, label in entries) + ". Public repositories and activity only; stars exclude forks.")


def languages_panel(stats, mobile=False):
    w, x = (420, 26) if mobile else (840, 40)
    counts = stats["languages"]
    shown = counts[:5]
    other = sum(n for _, n in counts[5:])
    if other:
        shown.append(("Other", other))
    content = text(x, 27, "Languages", 21, weight=600)
    total = sum(n for _, n in counts)
    start = x
    for lang, n in shown:
        size = (w-2*x)*n/total
        color = LANGUAGE_COLORS.get(lang, "#8496ae")
        content += f'<rect x="{start:.2f}" y="50" width="{size:.2f}" height="8" fill="{color}"/>'
        start += size
    for i, (lang, n) in enumerate(shown):
        cols = 2 if mobile else 3
        xx = x + (i % cols)*((w-2*x)/cols)
        yy = 88 + (i//cols)*28
        content += f'<circle cx="{xx+4}" cy="{yy-4}" r="4" fill="{LANGUAGE_COLORS.get(lang, "#8496ae")}"/>'
        content += text(xx+17, yy, f"{lang} · {n}", 13, MUTED)
    if not total:
        content += text(x, 88, "No primary language data yet", 14, MUTED)
    return panel(w, 180 if mobile else 150, content, "Languages · original repositories by primary language", ", ".join(f"{lang}: {n} repositories" for lang,n in counts) or "No language data yet")


def image_tag(name, alt, href=None, width="100%"):
    picture = (f'<picture><source media="(max-width: 600px)" srcset="assets/{name}-mobile.svg" />'
               f'<img src="assets/{name}.svg" width="{width}" align="top" alt="{html.escape(alt, quote=True)}" /></picture>')
    return f'<a href="{html.escape(href, quote=True)}">{picture}</a>' if href else picture


def generate(projects, stats):
    assets = {}
    def add(name, renderer):
        for mobile in [False, True]:
            assets[f"{name}{'-mobile' if mobile else ''}.svg"] = renderer(mobile)
    add("header", header)
    add("portfolio", lambda mobile: button("portfolio", mobile))
    add("linkedin", lambda mobile: button("linkedin", mobile))
    add("projects-heading", lambda mobile: heading("Recent projects", "01", mobile))
    add("activity-heading", lambda mobile: heading("On GitHub", "02", mobile))
    add("activity", lambda mobile: stats_panel(stats, mobile))
    add("languages", lambda mobile: languages_panel(stats, mobile))
    parts = [image_tag("header", "Ibrahim El Nemr · @ibrahimelnemr"),
             image_tag("portfolio", "Portfolio ↗", "https://ibrahimelnemr.github.io/", "50%") +
             image_tag("linkedin", "LinkedIn ↗", "https://www.linkedin.com/in/ibrahimelnemr/", "50%"),
             image_tag("projects-heading", "Recent projects · latest pushes to original public repositories")]
    for i, project in enumerate(projects):
        name = f"projects/{project['name']}"
        add(name, lambda mobile, repo=project: render_card(repo, mobile))
        parts.append(image_tag(name, f"{project['name']} · {project.get('description') or 'Explore the repository'}",
                               f"https://github.com/{USERNAME}/{project['name']}"))
    parts += [image_tag("activity-heading", "On GitHub"),
              image_tag("activity", f"{stats['repos']} public repos · {stats['stars']} stars earned · {stats['prs']} PRs opened · {stats['followers']} followers", f"https://github.com/pulls?q=is%3Apr+author%3A{USERNAME}+is%3Apublic"),
              image_tag("languages", "Primary languages in original public repositories: " + ", ".join(f"{lang} ({n})" for lang,n in stats['languages']), f"https://github.com/{USERNAME}?tab=repositories")]
    # Keep both buttons adjacent, with top-aligned images joining the background.
    readme = '<!-- Generated by scripts/update_projects.py from public GitHub data. -->\n<div align="center">\n' + "\n".join(parts) + '\n</div>\n'
    return readme, assets


def main():
    repositories = fetch_repositories()
    projects = select_projects(repositories)
    if not projects:
        raise ValueError("No eligible projects; keeping the previous profile")
    user = api(f"users/{USERNAME}")
    prs = search_count(f"author:{USERNAME} is:pr is:public")
    readme, assets = generate(projects, summarize(repositories, user, prs))
    # Fetch and render everything before writing: API failures keep the existing profile intact.
    for name, content in assets.items():
        path = ASSETS / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for path in (ASSETS / "projects").glob("*.svg"):
        if str(path.relative_to(ASSETS)) not in assets:
            path.unlink()
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"Refreshed {len(projects)} projects and public GitHub statistics")


if __name__ == "__main__":
    main()

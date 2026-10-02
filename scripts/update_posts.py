"""Rewrite the "Latest writing" list in README.md from loreley.one.

Posts are the sitemap URLs shaped like https://loreley.one/YYYY-MM-slug/; the
newest COUNT are listed with each page's <title>. Standard library only, so the
GitHub Action needs no install step.

Run:  python3 scripts/update_posts.py
"""

import re
import urllib.request
from datetime import date
from html import unescape
from pathlib import Path

SITE = "https://loreley.one"
COUNT = 5
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- BLOG-POST-LIST:START -->", "<!-- BLOG-POST-LIST:END -->"
POST_URL = re.compile(rf"<loc>({re.escape(SITE)}/(\d{{4}})-(\d{{2}})-[^/<]+/)</loc>")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "BasedLukas-readme"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def title_of(url: str) -> str:
    match = re.search(r"<title>(.*?)</title>", fetch(url), re.S)
    title = unescape(match.group(1)).strip() if match else url
    return re.sub(r"\s+[—|-]\s+Loreley$", "", title)


def main() -> None:
    posts = sorted(POST_URL.findall(fetch(f"{SITE}/sitemap.xml")), reverse=True)[:COUNT]
    lines = [
        f"- [{title_of(url)}]({url}) · {date(int(y), int(m), 1):%b %Y}"
        for url, y, m in posts
    ]
    readme = README.read_text()
    block = f"{START}\n" + "\n".join(lines) + f"\n{END}"
    updated = re.sub(rf"{re.escape(START)}.*?{re.escape(END)}", lambda _: block, readme, flags=re.S)
    if updated != readme:
        README.write_text(updated)
        print(f"Updated {len(lines)} posts")
    else:
        print("No change")


if __name__ == "__main__":
    main()

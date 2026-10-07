#!/usr/bin/env python3
"""Rebuild the essay lists from the frontmatter of content/*.md.

Fills the list between the <!-- essays:start --> / <!-- essays:end --> markers
in index.html (home) and writing/index.html (archive).

Each essay needs a title and a date like "February 9, 2026".
Add `draft: true` to the frontmatter to keep an essay off the lists.
"""
import html
import re
import sys
from datetime import datetime
from pathlib import Path

START, END = "<!-- essays:start -->", "<!-- essays:end -->"
PAGES = [Path("index.html"), Path("writing/index.html")]


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip().lower()] = value.strip().strip("\"'")
    return meta


def parse_date(s):
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


items = []
for path in Path("content").glob("*.md"):
    meta = frontmatter(path)
    if meta.get("draft", "").lower() == "true":
        continue
    date = parse_date(meta.get("date", ""))
    if not meta.get("title") or date is None:
        print(f"skipping {path.name}: needs a title and a date like 'February 9, 2026'", file=sys.stderr)
        continue
    items.append((date, path.stem, meta["title"]))

items.sort(reverse=True)

rows = "\n".join(
    f'          <li><a href="/writing/{stem}.html">{html.escape(title)}</a>'
    f'<time datetime="{d:%Y-%m-%d}">{d:%b} {d.day}, {d.year}</time></li>'
    for d, stem, title in items
)

for page_path in PAGES:
    page = page_path.read_text(encoding="utf-8")
    if START not in page or END not in page:
        sys.exit(f"{page_path} is missing the {START} / {END} markers")
    before, rest = page.split(START, 1)
    _, after = rest.split(END, 1)
    page_path.write_text(f"{before}{START}\n{rows}\n          {END}{after}", encoding="utf-8")
    print(f"{page_path}: listed {len(items)} essays")

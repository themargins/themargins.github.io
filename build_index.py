#!/usr/bin/env python3
"""Rebuild the lists that come from the content.

writing/index.html  every essay and poem, newest first (from content/*.md)
index.html          the intro (from home.md) and "Lately": the newest few
                    essays, projects and gallery pieces, mixed together

Each essay needs a title and a date like "February 9, 2026".
Add `draft: true` to the frontmatter to keep a piece off the lists.
"""
import html
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME, ARCHIVE, INTRO = Path("index.html"), Path("writing/index.html"), Path("home.md")
LATELY_COUNT = 6
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".heic", ".heif"}


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
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%B %Y", "%b %Y", "%Y-%m"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def short(d):
    return f"{d:%b} {d.day}, {d.year}"


def fill(path, name, body):
    start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
    page = path.read_text(encoding="utf-8")
    if start not in page or end not in page:
        sys.exit(f"{path} is missing the {start} / {end} markers")
    before, rest = page.split(start, 1)
    _, after = rest.split(end, 1)
    path.write_text(f"{before}{start}\n{body}\n          {end}{after}", encoding="utf-8")


def is_draft(meta):
    return meta.get("draft", "").lower() == "true"


# --- Writing ------------------------------------------------------------------

essays = []
for path in Path("content").glob("*.md"):
    meta = frontmatter(path)
    if is_draft(meta):
        continue
    date = parse_date(meta.get("date", ""))
    if not meta.get("title") or date is None:
        print(f"skipping {path.name}: needs a title and a date like 'February 9, 2026'", file=sys.stderr)
        continue
    essays.append((date, f"/writing/{path.stem}.html", meta["title"], meta.get("category") or "Writing"))
essays.sort(reverse=True)

fill(ARCHIVE, "essays", "\n".join(
    f'          <li><a href="{url}">{html.escape(title)}</a>'
    f'<time datetime="{d:%Y-%m-%d}">{short(d)}</time></li>'
    for d, url, title, _ in essays))
print(f"{ARCHIVE}: listed {len(essays)} pieces")


# --- Lately: newest essays, projects and gallery pieces, mixed ----------------

items = list(essays)

for index_md in Path("projects").glob("*/index.md"):
    meta = frontmatter(index_md)
    date = parse_date(meta.get("updated", "")) or parse_date(meta.get("started", ""))
    if meta.get("title") and date and not is_draft(meta):
        items.append((date, f"/projects/{index_md.parent.name}/", meta["title"], "Project"))

seen = set()
for path in sorted(Path("art/images").glob("*")) if Path("art/images").exists() else []:
    m = re.match(r"(\d{4}-\d{2}-\d{2})[-_ ]*(.*)", path.stem)
    if path.suffix.lower() not in IMAGE_TYPES or not m or path.stem in seen:
        continue
    seen.add(path.stem)
    try:
        date = datetime.strptime(m.group(1), "%Y-%m-%d")
    except ValueError:
        continue
    words = re.sub(r"[-_]+", " ", m.group(2)).strip()
    title = words[:1].upper() + words[1:] if words else "Untitled"
    items.append((date, f"/art/#{path.stem}", title, "Gallery"))

items.sort(key=lambda i: i[0], reverse=True)
fill(HOME, "lately", "\n".join(
    f'          <li><a href="{url}">{html.escape(title)}</a>'
    f'<span class="index-meta">{html.escape(label)} · <time datetime="{d:%Y-%m-%d}">{short(d)}</time></span></li>'
    for d, url, title, label in items[:LATELY_COUNT]))
print(f"{HOME}: {min(len(items), LATELY_COUNT)} items under Lately")


# --- Intro, from home.md ------------------------------------------------------

if INTRO.exists():
    text = re.sub(r"<!--.*?-->", "", INTRO.read_text(encoding="utf-8"), flags=re.S)
    text = re.sub(r"^::: ?todo\s*\n.*?^:::\s*$", "", text, flags=re.S | re.M)  # prompts stay in home.md, off the page
    r = subprocess.run(["pandoc", "-f", "markdown", "-t", "html", "--wrap=none"],
                       input=text, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"couldn't build the intro from {INTRO}: {r.stderr.strip()}", file=sys.stderr)
    else:
        fill(HOME, "intro", "\n".join("        " + line if line else "" for line in r.stdout.strip().splitlines()))

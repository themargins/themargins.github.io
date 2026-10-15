#!/usr/bin/env python3
"""Build the project pages and the list on /projects/.

Each project is a folder: projects/<name>/index.md, with its photos and videos
next to it. `make` turns index.md into index.html in the same folder.

Frontmatter:
    ---
    title: MIMIC
    description: One sentence for the list and the top of the page.
    status: ongoing            (anything; ongoing/active projects are listed first)
    started: September 2026    (optional, shown as written)
    updated: October 15, 2026  (sets the order and the "Updated" date)
    draft: true                (optional: built, but left off the list)
    ---

Media in the folder:
    .heic photos  -> .jpg, 2000px, location removed (original kept out of git)
    .mov videos   -> .mp4 (H.264, 1920px, all metadata removed) + a poster frame
    .mp4 videos   -> published as they are, with any location removed
In the text, write ![Caption](clip.mov) for a video, add {.loop} for a silent
autoplaying loop, or use a YouTube/Vimeo link for an embedded player.
"""
import html
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from media import (PHONE_TYPES, VIDEO_SOURCES, check_mp4, convert_phone_photo,
                   convert_video, poster_for, video_size)

ROOT = Path("projects")
LIST_PAGE = ROOT / "index.html"
TEMPLATE = Path("templates/project.html")
FILTER = Path("templates/media.lua")
START, END = "<!-- projects:start -->", "<!-- projects:end -->"
BIG_IMAGE = 1_500_000
ACTIVE = {"ongoing", "active", "in progress", "wip"}


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


def prepare_media(folder):
    """Convert phone photos and videos; return what the filter needs per video."""
    for path in sorted(folder.iterdir()):
        ext = path.suffix.lower()
        if ext in PHONE_TYPES:
            convert_phone_photo(path)
        elif ext in VIDEO_SOURCES:
            convert_video(path)
        elif ext in {".jpg", ".jpeg", ".png", ".gif", ".webp"} and path.stat().st_size > BIG_IMAGE \
                and not path.name.endswith(".poster.jpg"):
            print(f"note: {folder.name}/{path.name} is {path.stat().st_size / 1e6:.1f} MB; "
                  "about 2000px wide is plenty for the web", file=sys.stderr)
    info = {}
    for mp4 in sorted(folder.glob("*.mp4")):
        if mp4.name.endswith(".part.mp4"):
            continue
        check_mp4(mp4)
        entry = {}
        poster = poster_for(mp4)
        if poster:
            entry["poster"] = poster.name
        dims = video_size(mp4)
        if dims:
            entry["w"], entry["h"] = str(dims[0]), str(dims[1])
        info[mp4.name] = entry
    return info


def build_page(folder, meta, media_info):
    bits = []
    if meta.get("status"):
        bits.append(meta["status"][:1].upper() + meta["status"][1:])
    if meta.get("started"):
        bits.append(f"Started {meta['started']}")
    updated = parse_date(meta.get("updated", ""))
    if updated:
        bits.append(f"Updated {short(updated)}")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"media": media_info, "byline": " · ".join(bits)}, f)
        meta_file = f.name
    src, out = folder / "index.md", folder / "index.html"
    r = subprocess.run(["pandoc", "-s", str(src), "--template", str(TEMPLATE), "--lua-filter", str(FILTER),
                        "--metadata-file", meta_file, "--wrap=none", "-o", str(out)],
                       capture_output=True, text=True)
    Path(meta_file).unlink(missing_ok=True)
    if r.returncode != 0:
        print(f"couldn't build {src}: {r.stderr.strip()}", file=sys.stderr)
    elif r.stderr.strip():
        print(r.stderr.strip(), file=sys.stderr)


items = []
for folder in sorted(p for p in ROOT.iterdir() if p.is_dir()) if ROOT.exists() else []:
    if not (folder / "index.md").exists():
        continue
    meta = frontmatter(folder / "index.md")
    if not meta.get("title"):
        print(f"skipping {folder}/index.md: needs a title", file=sys.stderr)
        continue
    build_page(folder, meta, prepare_media(folder))
    if meta.get("draft", "").lower() == "true":
        continue
    items.append((folder.name, meta))


def order(item):
    name, meta = item
    active = meta.get("status", "").lower() in ACTIVE
    when = parse_date(meta.get("updated", "")) or parse_date(meta.get("started", "")) or datetime.min
    return (not active, -when.toordinal(), meta["title"].lower())


rows = []
for name, meta in sorted(items, key=order):
    side = []
    if meta.get("status"):
        side.append(html.escape(meta["status"].lower()))
    d = parse_date(meta.get("updated", ""))
    if d:
        side.append(f'<time datetime="{d:%Y-%m-%d}">{short(d)}</time>')
    desc = meta.get("description")
    rows.append(
        f'          <li><a href="/projects/{name}/">{html.escape(meta["title"])}</a>'
        f'<span class="index-meta">{" · ".join(side)}</span>'
        + (f'<p class="index-desc">{html.escape(desc)}</p>' if desc else "")
        + "</li>")

body = "\n".join(rows) if rows else '          <li class="empty">Nothing here yet.</li>'
page = LIST_PAGE.read_text(encoding="utf-8")
if START not in page or END not in page:
    sys.exit(f"{LIST_PAGE} is missing the {START} / {END} markers")
before, rest = page.split(START, 1)
_, after = rest.split(END, 1)
LIST_PAGE.write_text(f"{before}{START}\n{body}\n          {END}{after}", encoding="utf-8")
print(f"{LIST_PAGE}: listed {len(rows)} projects")

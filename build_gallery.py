#!/usr/bin/env python3
"""Rebuild the Gallery (art/index.html) from the images in art/images/.

Naming:   2026-10-07-morning-light.jpg  ->  "Morning light", Oct 7, 2026
          The date prefix is optional; it sets the order (newest first).
Caption:  an optional text file with the same name, e.g.
          2026-10-07-morning-light.txt. Blank lines start a new paragraph.

Fills the list between <!-- gallery:start --> / <!-- gallery:end --> in
art/index.html. Needs nothing beyond Python; uses Pillow if it is installed.
"""
import html
import re
import struct
import sys
from datetime import datetime
from pathlib import Path

START, END = "<!-- gallery:start -->", "<!-- gallery:end -->"
IMAGES = Path("art/images")
PAGE = Path("art/index.html")
WEB_TYPES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}
BIG_FILE = 1_500_000  # bytes; warn above this


def size_with_pillow(path):
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as im:
            w, h = im.size
            orientation = im.getexif().get(0x0112, 1)
            return (h, w) if orientation in (5, 6, 7, 8) else (w, h)
    except Exception:
        return None


def size_plain(path):
    """Width and height for PNG, GIF and JPEG without any libraries."""
    with open(path, "rb") as f:
        head = f.read(26)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
        if head[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", head[6:10])
        if head[:2] == b"\xff\xd8":
            f.seek(2)
            while True:
                byte = f.read(1)
                while byte and byte != b"\xff":
                    byte = f.read(1)
                while byte == b"\xff":
                    byte = f.read(1)
                if not byte:
                    return None
                marker = byte[0]
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                    continue
                length = struct.unpack(">H", f.read(2))[0]
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack(">xHH", f.read(5))
                    return w, h
                f.seek(length - 2, 1)
    return None


def nice_title(slug):
    words = re.sub(r"[-_]+", " ", slug).strip()
    return words[:1].upper() + words[1:] if words else ""


def caption_html(path):
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return "".join(f"<p>{html.escape(' '.join(p.split()))}</p>" for p in paras)


plates = []
for path in sorted(IMAGES.glob("*")) if IMAGES.exists() else []:
    ext = path.suffix.lower()
    if ext in (".heic", ".heif", ".tif", ".tiff"):
        print(f"skipping {path.name}: browsers can't show {ext}; export it as .jpg", file=sys.stderr)
        continue
    if ext not in WEB_TYPES:
        continue
    if path.stat().st_size > BIG_FILE:
        mb = path.stat().st_size / 1e6
        print(f"note: {path.name} is {mb:.1f} MB; about 2000px wide is plenty for the web", file=sys.stderr)

    m = re.match(r"(\d{4}-\d{2}-\d{2})[-_ ]*(.*)", path.stem)
    date = None
    slug = path.stem
    if m:
        try:
            date = datetime.strptime(m.group(1), "%Y-%m-%d")
            slug = m.group(2)
        except ValueError:
            pass
    title = nice_title(slug)
    dims = size_with_pillow(path) or (size_plain(path) if ext in (".jpg", ".jpeg", ".png", ".gif") else None)
    plates.append((date, path, title, dims, caption_html(path.with_suffix(".txt"))))

# Newest first; undated images go last, by name
plates.sort(key=lambda p: (p[0] is not None, p[0] or datetime.min, p[1].name), reverse=True)
plates = [p for p in plates if p[0]] + sorted((p for p in plates if not p[0]), key=lambda p: p[1].name)

blocks = []
for date, path, title, dims, caption in plates:
    src = "/" + path.as_posix()
    size = f' width="{dims[0]}" height="{dims[1]}"' if dims else ""
    alt = html.escape(title or "Untitled", quote=True)
    meta = []
    if title:
        meta.append(f'<span class="plate-title">{html.escape(title)}</span>')
    if date:
        meta.append(f'<time datetime="{date:%Y-%m-%d}">{date:%b} {date.day}, {date.year}</time>')
    head = f'<div class="plate-head">{"".join(meta)}</div>' if meta else ""
    figcaption = f"\n            <figcaption>{head}{caption}</figcaption>" if (head or caption) else ""
    blocks.append(
        f'          <figure class="plate">\n'
        f'            <a href="{src}"><img src="{src}" alt="{alt}"{size} loading="lazy" decoding="async"></a>'
        f"{figcaption}\n"
        f"          </figure>"
    )

body = "\n".join(blocks) if blocks else '          <p class="empty">Nothing here yet.</p>'

page = PAGE.read_text(encoding="utf-8")
if START not in page or END not in page:
    sys.exit(f"{PAGE} is missing the {START} / {END} markers")
before, rest = page.split(START, 1)
_, after = rest.split(END, 1)
PAGE.write_text(f"{before}{START}\n{body}\n          {END}{after}", encoding="utf-8")
print(f"{PAGE}: {len(blocks)} images")

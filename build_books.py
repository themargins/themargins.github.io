#!/usr/bin/env python3
"""Build the books section of the home page ("On the shelf").

books.txt  the books, one per line, in the order you want them shown
           (the first 9 are on the shelf; the rest open under "All N books"):

    Khalil Gibran — The Prophet
        An optional note, indented on the next line. [Links](/writing/x.html) work.
    Paulo Coelho — The Alchemist | https://...   (optional: where the title links)
    now: Blake Crouch — Recursion                (what you're reading now: shown first, marked "Reading now")
    early: Eoin Colfer — Artemis Fowl            (childhood books: one line of text under the shelf, no covers)
    early: every Rick Riordan series             (no author: shown as plain words)

The first time a book appears, `make` looks it up on Open Library for its cover, saves the cover in books/covers/ and remembers the rest in
books/books.json, so later builds work offline.

No cover found? `make` leaves a grey placeholder at books/covers/<name>.png: save the
right image over it (same name) and run `make` again. Wrong cover? Save your own image
as books/covers/<name>.png the same way; it wins over the downloaded .jpg. Or add
"recheck": true to the book's entry in books/books.json to look it up again.
"""
import html
import json
import re
import subprocess
import sys
import urllib.parse
import zlib
import struct
from pathlib import Path

BOOKS = Path("books.txt")
HOME = Path("index.html")
COVERS, CACHE = Path("books/covers"), Path("books/books.json")


def fetch(url):
    """Bytes from a URL, using the Mac's curl (which trusts the system certificates)."""
    r = subprocess.run(["curl", "-fsSL", "-m", "20", url], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("&", "and")).strip("-")[:80]


def look_up(author, title):
    query = urllib.parse.urlencode({"title": title, "author": author, "limit": 5,
                                    "fields": "key,title,author_name,first_publish_year,cover_i,edition_count"})
    raw = fetch(f"https://openlibrary.org/search.json?{query}")
    if raw is None:
        return None
    try:
        docs = json.loads(raw).get("docs", [])
    except ValueError:
        return None
    if not docs:
        return {}
    # Prefer the book itself over study guides and graphic novels: exact title, most editions, has a cover
    want = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
    d = max(docs, key=lambda d: (re.sub(r"[^a-z0-9]+", " ", d.get("title", "").lower()).strip() == want,
                                 bool(d.get("cover_i")), d.get("edition_count") or 0))
    return {
        "year": str(d.get("first_publish_year") or ""),
        "url": f"https://openlibrary.org{d['key']}" if d.get("key") else "",
        "art": f"https://covers.openlibrary.org/b/id/{d['cover_i']}-M.jpg" if d.get("cover_i") else "",
        "matched": f"{', '.join(d.get('author_name') or [])} — {d.get('title', '')}",
    }


EARLY = []         # the "Where it started" line: (author, title) pairs, author may be ""


def read_books():
    books = []
    if not BOOKS.exists():
        return books
    for raw in BOOKS.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1] in (" ", "\t"):          # an indented line: a note on the book above
            if books:
                books[-1]["note"] = (books[-1]["note"] + " " + raw.strip()).strip()
            continue
        line, link, now = raw.strip(), "", False
        if line.lower().startswith("early:"):
            parts = re.split(r"\s+[—–-]\s+", line[6:].strip(), maxsplit=1)
            EARLY.append((parts[0].strip(), parts[1].strip()) if len(parts) == 2 else ("", parts[0].strip()))
            continue
        if line.lower().startswith("now:"):
            line, now = line[4:].strip(), True
        if "|" in line:
            line, link = (s.strip() for s in line.split("|", 1))
        parts = re.split(r"\s+[—–-]\s+", line, maxsplit=1)
        if len(parts) != 2:
            print(f"books.txt: skipping '{line}': write it as Author — Title", file=sys.stderr)
            continue
        books.append({"author": parts[0].strip(), "title": parts[1].strip(), "link": link, "note": "", "now": now})
    return sorted(books, key=lambda b: not b["now"])   # what you're reading now comes first


def note_html(text):
    """Escape a note, keeping [text](url) links."""
    out, last = [], 0
    for m in re.finditer(r"\[([^\]]+)\]\(([^)\s]+)\)", text):
        out.append(html.escape(text[last:m.start()]))
        out.append(f'<a href="{html.escape(m.group(2), quote=True)}">{html.escape(m.group(1))}</a>')
        last = m.end()
    out.append(html.escape(text[last:]))
    return "".join(out)


def fill(path, name, body, indent="        "):
    start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
    page = path.read_text(encoding="utf-8")
    if start not in page or end not in page:
        sys.exit(f"{path} is missing the {start} / {end} markers")
    before, rest = page.split(start, 1)
    _, after = rest.split(end, 1)
    path.write_text(f"{before}{start}\n{body}\n{indent}{end}{after}", encoding="utf-8")


def placeholder_png(w=200, h=300, rgb=(0xDC, 0xDD, 0xE0)):
    """A plain grey PNG, made without any image library."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    rows = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


PLACEHOLDER = placeholder_png()


def is_placeholder(path):
    return path.exists() and path.read_bytes() == PLACEHOLDER


cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
COVERS.mkdir(parents=True, exist_ok=True)


def render(b):
    key = f"{b['author']} — {b['title']}"
    slug = slugify(b["title"])
    cover = COVERS / f"{slugify(key)}.jpg"
    info = cache.get(key)
    if not info or info.get("recheck"):            # new, not found last time, or marked to look up again
        found = look_up(b["author"], b["title"])
        if found is None:
            print(f"couldn't reach Open Library for '{key}'; will try again next time", file=sys.stderr)
            info = info or {}
        else:
            if not found:
                print(f"couldn't find '{key}'; you can add a cover as {cover}", file=sys.stderr)
            else:
                print(f"'{key}' matched '{found['matched']}'")
            info = cache[key] = found
    if info.get("art") and (not cover.exists() or info.get("cover_from") != info["art"]):
        data = fetch(info["art"])
        if data and data[:2] == b"\xff\xd8" and len(data) > 1000:   # Open Library sends a tiny blank for missing covers
            cover.write_bytes(data)
            info["cover_from"] = info["art"]
            cache[key] = info
            print(f"saved cover {cover}")

    title, author = html.escape(b["title"]), html.escape(b["author"])
    # Your own image (.png or .webp, e.g. saved over the placeholder) wins over the downloaded .jpg
    holder = cover.with_suffix(".png")
    found = next((c for c in (holder, cover.with_suffix(".webp"), cover)
                  if c.exists() and not is_placeholder(c)), None)
    if found is None:
        if not holder.exists():
            holder.write_bytes(PLACEHOLDER)
        print(f"no cover for '{key}': save one over {holder} and run make again", file=sys.stderr)
        img = '<span class="book-blank"></span>'
    else:
        if is_placeholder(holder):
            holder.unlink()                  # the real cover arrived; the placeholder isn't needed
        img = f'<img src="/{found.as_posix()}" alt="" loading="lazy" decoding="async">'
    # Your link, else the book's Open Library page, else an Open Library search for it
    href = (b["link"] or info.get("url")
            or "https://openlibrary.org/search?" + urllib.parse.urlencode({"q": f"{b['title']} {b['author']}"}))
    name = f'<a class="book-title" href="{html.escape(href, quote=True)}">{title}</a>' if href \
        else f'<span class="book-title">{title}</span>'
    meta = author
    note = f'<span class="book-note">{note_html(b["note"])}</span>' if b["note"] else ""
    now = '<span class="book-now">Reading now</span>' if b["now"] else ""
    return (f'<li class="book{" is-now" if b["now"] else ""}" id="{slug}">{now}<span class="book-cover">{img}</span>'
            f'<span class="book-text">{name}<span class="book-meta">{meta}</span>{note}</span></li>')


SHOWN = 9          # books on the shelf before the rest fold away under "All N books"

books = read_books()
rows = [render(b) for b in books]

# Tidy up: grey placeholders left by books you've renamed or removed
keep = {slugify(f"{b['author']} — {b['title']}") for b in books}
for stale in COVERS.glob("*.png"):
    if stale.stem not in keep and is_placeholder(stale):
        stale.unlink()
CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def shelf(rs):
    return '<ul class="books">\n' + "\n".join("          " + r for r in rs) + "\n        </ul>"


section = ""
if rows:
    section = ('        <h2 class="section-label" id="books">On the shelf</h2>\n        ' + shelf(rows[:SHOWN]))
    if len(rows) > SHOWN:
        section += (f'\n        <details class="shelf-more">\n          <summary>All {len(rows)} books</summary>\n        '
                    + shelf(rows[SHOWN:]) + "\n        </details>")
if EARLY:
    def early(author, title):
        if not author:
            return html.escape(title)
        q = urllib.parse.urlencode({"q": f"{title} {author}"})
        return f'<a href="https://openlibrary.org/search?{q}"><em>{html.escape(title)}</em></a>'
    section += ('\n        <p class="shelf-early"><span class="shelf-early-label">Where it started:</span> '
                + ", ".join(early(a, t) for a, t in EARLY) + ", and many more I can’t remember.</p>")

fill(HOME, "books", section)
print(f"{HOME}: {len(rows)} books under On the shelf")

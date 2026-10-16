#!/usr/bin/env python3
"""Build the music section of the home page ("On repeat").

music.md   a few words above the songs, and where recommendations go
music.txt  the songs, newest at the top:

    Frank Ocean — Nights
        An optional note, indented on the next line.
    Radiohead — Weird Fishes/Arpeggi | https://open.spotify.com/track/...

The first time a song appears, `make` looks it up in Apple's public music
catalogue for its cover, year and 30-second preview, saves the cover in
music/covers/ and remembers the rest in music/songs.json, so later builds work
offline. Songs link to Apple Music, or to the link after a | if you add one.

Wrong song? In music/songs.json, add "recheck": true to its entry (or delete the
entry) to look it up again, or put your own square image at the cover path.
"""
import difflib
import html
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

SONGS, WORDS = Path("music.txt"), Path("music.md")
HOME = Path("index.html")
COVERS, CACHE = Path("music/covers"), Path("music/songs.json")
COVER_PX = 200     # shown at about 56px; 200 keeps it sharp on any screen


def fetch(url):
    """Bytes from a URL, using the Mac's curl (which trusts the system certificates)."""
    r = subprocess.run(["curl", "-fsSL", "-m", "20", url], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("&", "and")).strip("-")[:80]


def norm(text):
    text = re.sub(r"\s*[\(\[][^)\]]*(remaster|version|edit|mono|stereo|live)[^)\]]*[\)\]]", "", text, flags=re.I)
    text = re.sub(r"\s*-\s*(\d{4} )?remaster(ed)?.*$", "", text, flags=re.I)
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def look_up(artist, song):
    query = urllib.parse.urlencode({"term": f"{artist} {song}", "entity": "song", "limit": 25})
    raw = fetch(f"https://itunes.apple.com/search?{query}")
    if raw is None:
        return None
    try:
        results = json.loads(raw).get("results", [])
    except ValueError:
        return None
    best, best_key = None, None
    for r in results:
        a = difflib.SequenceMatcher(None, norm(artist), norm(r.get("artistName", ""))).ratio()
        s = difflib.SequenceMatcher(None, norm(song), norm(r.get("trackName", ""))).ratio()
        if a <= 0.6 or s <= 0.6:
            continue
        # prefer the original album: skip past best-ofs and compilations, then take the earliest release
        album = (r.get("collectionName") or "").lower()
        compilation = bool(re.search(r"best of|greatest|hits|#1|number ones|collection|essential|anthology|"
                                     r"compilation|playlist|now that|the very best|gold|definitive|treasury|"
                                     r"retrospective|introducing|the story of|selected|the years|complete", album))
        title_track = norm(album) == norm(r.get("trackName", ""))  # e.g. Pink Moon on the album Pink Moon
        key = (-round(a + 2 * s, 1), compilation, not title_track, r.get("releaseDate") or "9999")
        if best_key is None or key < best_key:
            best, best_key = r, key
    if not best:
        return {}
    return {
        "year": (best.get("releaseDate") or "")[:4],
        "url": best.get("trackViewUrl", ""),
        "preview": best.get("previewUrl", ""),
        "art": (best.get("artworkUrl100") or "").replace("100x100bb", f"{COVER_PX}x{COVER_PX}bb"),
        "matched": f"{best.get('artistName')} — {best.get('trackName')}",
    }


def read_songs():
    songs = []
    if not SONGS.exists():
        return songs
    for raw in SONGS.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1] in (" ", "\t"):          # an indented line: a note on the song above
            if songs:
                songs[-1]["note"] = (songs[-1]["note"] + " " + raw.strip()).strip()
            continue
        line, link = raw.strip(), ""
        if "|" in line:
            line, link = (s.strip() for s in line.split("|", 1))
        parts = re.split(r"\s+[—–-]\s+", line, maxsplit=1)
        if len(parts) != 2:
            print(f"music.txt: skipping '{line}': write it as Artist — Song", file=sys.stderr)
            continue
        songs.append({"artist": parts[0].strip(), "song": parts[1].strip(), "link": link, "note": ""})
    return songs


def frontmatter_and_body(path):
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    meta, body = {}, text
    m = re.match(r"---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                key, value = line.split(":", 1)
                meta[key.strip().lower()] = value.strip().strip("\"'")
    return meta, re.sub(r"<!--.*?-->", "", body, flags=re.S)


def fill(path, name, body, indent="        "):
    start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
    page = path.read_text(encoding="utf-8")
    if start not in page or end not in page:
        sys.exit(f"{path} is missing the {start} / {end} markers")
    before, rest = page.split(start, 1)
    _, after = rest.split(end, 1)
    path.write_text(f"{before}{start}\n{body}\n{indent}{end}{after}", encoding="utf-8")


# --- Look up and render the songs ---------------------------------------------

cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
COVERS.mkdir(parents=True, exist_ok=True)


def render(s, with_note):
    key = f"{s['artist']} — {s['song']}"
    cover = COVERS / f"{slugify(key)}.jpg"
    info = cache.get(key)
    if info is None or info.get("recheck"):      # new song, or marked to be looked up again
        found = look_up(s["artist"], s["song"])
        if found is None:
            print(f"couldn't reach the music catalogue for '{key}'; will try again next time", file=sys.stderr)
            info = info or {}
        else:
            if not found:
                print(f"couldn't find '{key}'; you can add a cover as {cover}", file=sys.stderr)
            elif norm(found["matched"]) != norm(key):
                print(f"'{key}' matched '{found['matched']}'", file=sys.stderr)
            info = cache[key] = found
    # Download the cover when it's missing, or when the match changed since it was saved
    if info.get("art") and (not cover.exists() or info.get("cover_from") != info["art"]):
        data = fetch(info["art"])
        if data and data[:2] == b"\xff\xd8":
            cover.write_bytes(data)
            info["cover_from"] = info["art"]
            print(f"saved cover {cover}")

    title, artist = html.escape(s["song"]), html.escape(s["artist"])
    img = (f'<img src="/{cover.as_posix()}" alt="" width="{COVER_PX}" height="{COVER_PX}" loading="lazy" decoding="async">'
           if cover.exists() else '<span class="song-blank"></span>')
    if info.get("preview"):
        art = (f'<button class="song-art" type="button" data-preview="{html.escape(info["preview"], quote=True)}" '
               f'aria-label="Play a preview of {title} by {artist}">{img}<span class="song-play" aria-hidden="true"></span></button>')
    else:
        art = f'<span class="song-art">{img}</span>'
    href = s["link"] or info.get("url", "")
    name = f'<a class="song-title" href="{html.escape(href, quote=True)}">{title}</a>' if href \
        else f'<span class="song-title">{title}</span>'
    meta = artist + (f" · {info['year']}" if info.get("year") else "")
    note = f'<span class="song-note">{html.escape(s["note"])}</span>' if with_note and s["note"] else ""
    return f'<li class="song">{art}<span class="song-text">{name}<span class="song-meta">{meta}</span>{note}</span></li>'


TOP = 10
songs = read_songs()
if len(songs) > TOP:
    print(f"music.txt has {len(songs)} songs; only the first {TOP} are shown", file=sys.stderr)
    songs = songs[:TOP]
rows = [render(s, with_note=True).replace('<li class="song">', f'<li class="song"><span class="song-rank">{i}</span>', 1)
        for i, s in enumerate(songs, 1)]
CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

meta, body = frontmatter_and_body(WORDS)
body = re.sub(r"^::: ?todo\s*\n.*?^:::\s*$", "", body, flags=re.S | re.M)  # prompts stay in music.md, off the page
words = ""
if body.strip():
    r = subprocess.run(["pandoc", "-f", "markdown", "-t", "html", "--wrap=none"],
                       input=body, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"couldn't build the music words from {WORDS}: {r.stderr.strip()}", file=sys.stderr)
    else:
        words = '        <div class="music-intro">\n' + r.stdout.strip() + "\n        </div>\n"

to = meta.get("recommend_to", "").strip()
box = ""
if to:
    if "@" in to and not to.startswith("http"):
        attrs = (f'action="mailto:{html.escape(to, quote=True)}" method="post" enctype="text/plain" '
                 f'data-mailto="{html.escape(to, quote=True)}"')
    else:
        attrs = f'action="{html.escape(to, quote=True)}" method="post"'
    # For a form service: a clear subject on the email you get, and a hidden
    # field that only spam bots fill in (the service drops those messages)
    extras = "" if "data-mailto" in attrs else (
        '\n            <input type="hidden" name="_subject" value="A song recommendation from The Margins">'
        '\n            <input type="text" name="_gotcha" class="trap" tabindex="-1" autocomplete="off" aria-hidden="true">')
    box = f'''        <details class="recommend">
          <summary>Recommend me a song</summary>
          <form {attrs}>{extras}
            <div class="recommend-row">
              <label><span>Song</span><input name="song" required autocomplete="off"></label>
              <label><span>Artist</span><input name="artist" required autocomplete="off"></label>
            </div>
            <label><span>Why this one? <span class="optional">(optional)</span></span><textarea name="why" rows="3"></textarea></label>
            <label><span>Your name <span class="optional">(optional)</span></span><input name="name" autocomplete="name"></label>
            <button type="submit">Send</button>
            <p class="recommend-status" role="status"></p>
          </form>
        </details>
'''

section = ""
if rows or words or box:
    section = ('        <h2 class="section-label" id="music">On repeat</h2>\n' + words
               + (f'        <ol class="songs top" style="grid-template-rows: repeat({(len(rows) + 1) // 2}, auto)">\n'
                  + "\n".join("          " + r for r in rows) + "\n        </ol>\n" if rows else "")
               + box + '        <script src="/music/songs.js" defer></script>')
fill(HOME, "music", section)
print(f"{HOME}: {len(rows)} songs under On repeat" + ("" if to else "; recommendation box hidden (set recommend_to in music.md)"))

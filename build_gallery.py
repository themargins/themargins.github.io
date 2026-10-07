#!/usr/bin/env python3
"""Rebuild the Gallery (art/index.html) from the images in art/images/.

Naming:   2026-10-07-morning-light.jpg  ->  "Morning light", Oct 7, 2026
          The date prefix is optional; it sets the order (newest first).
Caption:  an optional text file with the same name, e.g.
          2026-10-07-morning-light.txt. Blank lines start a new paragraph.
Phone photos: a .heic file is converted to a .jpg of the same name
          (2000px on the long side, GPS location removed). The .heic itself
          is kept out of git, so only the .jpg is published.

Fills the list between <!-- gallery:start --> / <!-- gallery:end --> in
art/index.html. Needs nothing beyond Python on a Mac (it uses the built-in
`sips` for .heic); uses Pillow and pillow-heif instead if they are installed.
"""
import html
import re
import shutil
import struct
import subprocess
import sys
from datetime import datetime
from pathlib import Path

START, END = "<!-- gallery:start -->", "<!-- gallery:end -->"
IMAGES = Path("art/images")
PAGE = Path("art/index.html")
WEB_TYPES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}
PHONE_TYPES = {".heic", ".heif"}
LONG_SIDE = 2000  # px, for converted photos
BIG_FILE = 1_500_000  # bytes; warn above this


# --- Converting phone photos -------------------------------------------------

def strip_location(data):
    """Remove GPS data from a JPEG's EXIF block and drop XMP, keeping the rest
    (including orientation). Returns the cleaned bytes."""
    if data[:2] != b"\xff\xd8":
        return data
    out = bytearray(data[:2])
    i = 2
    while i + 4 <= len(data) and data[i] == 0xFF:
        marker = data[i + 1]
        if marker == 0xDA:  # start of image data: copy the rest unchanged
            break
        seg_len = struct.unpack(">H", data[i + 2:i + 4])[0]
        seg = bytearray(data[i:i + 2 + seg_len])
        if marker == 0xE1 and seg[4:10] == b"Exif\0\0":
            _clear_gps(seg, 10)
        elif marker == 0xE1 and b"ns.adobe.com/xap" in seg[:40]:
            i += 2 + seg_len
            continue  # drop XMP, which can repeat the location
        out += seg
        i += 2 + seg_len
    out += data[i:]
    return bytes(out)


def _clear_gps(seg, t):
    """Zero the GPS IFD (entries and their values) inside an Exif segment;
    `t` is where the TIFF header starts."""
    e = "<" if seg[t:t + 2] == b"II" else ">"
    u16 = lambda o: struct.unpack_from(e + "H", seg, t + o)[0]
    u32 = lambda o: struct.unpack_from(e + "I", seg, t + o)[0]
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}
    ifd0 = u32(4)
    for k in range(u16(ifd0)):
        entry = ifd0 + 2 + 12 * k
        if u16(entry) != 0x8825:  # GPSInfo pointer
            continue
        gps = u32(entry + 8)
        count = u16(gps)
        for j in range(count):
            g = gps + 2 + 12 * j
            size = sizes.get(u16(g + 2), 1) * u32(g + 4)
            if size > 4:
                off = u32(g + 8)
                seg[t + off:t + off + size] = bytes(size)
        seg[t + gps:t + gps + 2 + 12 * count] = bytes(2 + 12 * count)


def convert_phone_photo(src):
    """Make src.jpg next to a .heic, unless an up-to-date one is already there."""
    dst = src.with_suffix(".jpg")
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    try:
        from PIL import Image, ImageOps
        import pillow_heif
        pillow_heif.register_heif_opener()
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((LONG_SIDE, LONG_SIDE))
            im.save(dst, "JPEG", quality=85, optimize=True, progressive=True)  # no EXIF kept
    except ImportError:
        if shutil.which("sips"):  # built into every Mac
            cmd = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "85",
                   "-Z", str(LONG_SIDE), str(src), "--out", str(dst)]
        elif shutil.which("magick"):
            cmd = ["magick", str(src), "-auto-orient", "-resize", f"{LONG_SIDE}x{LONG_SIDE}>",
                   "-strip", "-quality", "85", str(dst)]
        else:
            print(f"can't convert {src.name}: no converter found; "
                  "run `pip3 install pillow pillow-heif`", file=sys.stderr)
            return
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not dst.exists():
            print(f"couldn't convert {src.name}: {result.stderr.strip()}", file=sys.stderr)
            return
        try:
            dst.write_bytes(strip_location(dst.read_bytes()))
        except Exception as err:
            dst.unlink(missing_ok=True)  # never publish a photo that may carry a location
            print(f"couldn't remove location data from {src.name} ({err}); skipped it", file=sys.stderr)
            return
    print(f"converted {src.name} -> {dst.name}")


# --- Reading image sizes -------------------------------------------------------

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


# --- Building the page ---------------------------------------------------------

def nice_title(slug):
    words = re.sub(r"[-_]+", " ", slug).strip()
    return words[:1].upper() + words[1:] if words else ""


def caption_html(path):
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return "".join(f"<p>{html.escape(' '.join(p.split()))}</p>" for p in paras)


if IMAGES.exists():
    for path in sorted(IMAGES.iterdir()):
        if path.suffix.lower() in PHONE_TYPES:
            convert_phone_photo(path)

plates = []
for path in sorted(IMAGES.glob("*")) if IMAGES.exists() else []:
    ext = path.suffix.lower()
    if ext in (".tif", ".tiff"):
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
dated = sorted((p for p in plates if p[0]), key=lambda p: (p[0], p[1].name), reverse=True)
undated = sorted((p for p in plates if not p[0]), key=lambda p: p[1].name)

blocks = []
for date, path, title, dims, caption in dated + undated:
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

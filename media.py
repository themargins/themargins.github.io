"""Shared media helpers for the build scripts.

Phone photos (.heic) become web .jpgs with the location removed.
Phone videos (.mov) become small H.264 .mp4s that every browser plays, with
all metadata (including the location) removed, plus a poster frame.
The originals stay in the folder but are kept out of git (.gitignore).
"""
import json
import shutil
import struct
import subprocess
import sys

PHONE_TYPES = {".heic", ".heif"}
LONG_SIDE = 2000  # px, for converted photos


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


# --- Converting phone videos -------------------------------------------------

VIDEO_SOURCES = {".mov", ".m4v", ".hevc"}  # converted to .mp4
VIDEO_LONG_SIDE = 1920   # px
BIG_VIDEO = 10_000_000   # bytes; note above this
HUGE_VIDEO = 45_000_000  # bytes; GitHub warns at 50 MB and refuses 100 MB
HDR_TRANSFERS = {"arib-std-b67", "smpte2084"}  # HLG (iPhone default), PQ
_warned_ffmpeg = False


def have_ffmpeg():
    global _warned_ffmpeg
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return True
    if not _warned_ffmpeg:
        print("videos need ffmpeg: run `brew install ffmpeg`, then `make` again", file=sys.stderr)
        _warned_ffmpeg = True
    return False


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True)
    try:
        return json.loads(out.stdout)
    except ValueError:
        return {}


def _video_stream(info):
    return next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})


def _has_location(info):
    tags = dict(info.get("format", {}).get("tags", {}))
    for s in info.get("streams", []):
        tags.update(s.get("tags", {}))
    return any("location" in k.lower() or k.lower() == "gps" for k in tags)


def _has_filter(name):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return any(line.split()[1:2] == [name] for line in out.splitlines() if line.strip())


def convert_video(src):
    """Make src.mp4 next to a phone video, unless an up-to-date one is already there."""
    dst = src.with_suffix(".mp4")
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    if not have_ffmpeg():
        return
    stream = _video_stream(probe(src))
    n = VIDEO_LONG_SIDE
    filters = [f"scale='if(gte(iw,ih),min({n},iw),-2)':'if(gte(iw,ih),-2,min({n},ih))'"]
    if stream.get("color_transfer") in HDR_TRANSFERS:
        if _has_filter("zscale"):
            filters.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
                           "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv")
        else:
            print(f"note: {src.name} is HDR and this ffmpeg can't tone-map it; colours may look flat",
                  file=sys.stderr)
    filters.append("format=yuv420p")
    tmp = dst.with_name(dst.stem + ".part.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src),
           "-map", "0:v:0", "-map", "0:a:0?",
           "-map_metadata", "-1", "-map_chapters", "-1",   # drops the location and everything else
           "-vf", ",".join(filters),
           "-c:v", "libx264", "-preset", "slow", "-crf", "24",
           "-profile:v", "high", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "128k", "-ac", "2",
           "-movflags", "+faststart", str(tmp)]
    print(f"converting {src.name} -> {dst.name} (this can take a minute)")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not tmp.exists():
        tmp.unlink(missing_ok=True)
        print(f"couldn't convert {src.name}: {result.stderr.strip()[-400:]}", file=sys.stderr)
        return
    if _has_location(probe(tmp)):  # never publish a video that may carry a location
        tmp.unlink()
        print(f"couldn't remove location data from {src.name}; skipped it", file=sys.stderr)
        return
    tmp.replace(dst)


def check_mp4(path):
    """For .mp4s added as they are: remove location data, warn about codecs and size."""
    if not have_ffmpeg():
        return
    info = probe(path)
    if _has_location(info):
        tmp = path.with_name(path.stem + ".part.mp4")
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-map", "0", "-c", "copy",
                            "-map_metadata", "-1", "-map_chapters", "-1", "-movflags", "+faststart", str(tmp)],
                           capture_output=True, text=True)
        if r.returncode == 0 and tmp.exists() and not _has_location(probe(tmp)):
            tmp.replace(path)
            print(f"removed location data from {path.name}")
        else:
            tmp.unlink(missing_ok=True)
            print(f"warning: {path.name} contains a location and it couldn't be removed; "
                  f"rename it to .mov and `make` will convert it", file=sys.stderr)
    codec = _video_stream(info).get("codec_name")
    if codec and codec != "h264":
        print(f"note: {path.name} is {codec}, which some browsers can't play; "
              f"rename it to .mov and `make` will convert it", file=sys.stderr)
    size = path.stat().st_size
    if size > HUGE_VIDEO:
        print(f"warning: {path.name} is {size / 1e6:.0f} MB. GitHub refuses files over 100 MB and every "
              f"version stays in the repo for good; trim it, or put it on YouTube/Vimeo and embed the link",
              file=sys.stderr)
    elif size > BIG_VIDEO:
        print(f"note: {path.name} is {size / 1e6:.0f} MB; a shorter clip keeps the site light", file=sys.stderr)


def poster_for(mp4):
    """A still frame shown before the video plays: name.poster.jpg."""
    poster = mp4.with_name(mp4.stem + ".poster.jpg")
    if poster.exists() and poster.stat().st_mtime >= mp4.stat().st_mtime:
        return poster
    if not have_ffmpeg():
        return poster if poster.exists() else None
    duration = float(probe(mp4).get("format", {}).get("duration") or 0)
    at = "0.5" if duration > 1 else "0"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", at, "-i", str(mp4), "-frames:v", "1",
                        "-map_metadata", "-1", "-q:v", "3", str(poster)], capture_output=True, text=True)
    return poster if r.returncode == 0 and poster.exists() else None


def video_size(mp4):
    if not have_ffmpeg():
        return None
    s = _video_stream(probe(mp4))
    w, h = s.get("width"), s.get("height")
    rotation = abs(int(s.get("tags", {}).get("rotate", 0) or 0))
    for d in s.get("side_data_list", []):
        rotation = abs(int(d.get("rotation", rotation) or 0))
    if w and h and rotation in (90, 270):
        w, h = h, w
    return (w, h) if w and h else None

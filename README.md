# themargins.github.io

Personal site. Static, no framework. Needs `pandoc`, `python3` and `make`.

## Writing a piece

1. Add `content/your_title.md` with frontmatter:

   ```
   ---
   title: Your Title
   description: One sentence.
   date: February 9, 2026
   category: Essay
   ---
   ```

   Add `draft: true` to keep it off the site's lists while you work on it.

2. Run `make`. Each `content/*.md` becomes `writing/*.html`, and the lists on the
   home page and on `/writing/` are rebuilt from the dates, newest first.

For poems, start each line with `| ` to keep the line breaks.

## Margin notes

Inside a paragraph, write `<span class="marginnote">A side remark.</span>`. On wide screens it sits in the margin; on narrow ones it drops below the paragraph.

## Adding to the Gallery

1. Drop an image into `art/images/`, named with the date and a title:
   `2026-10-07-morning-light.jpg` shows as *Morning light*, Oct 7, 2026.
   The date is optional; it sets the order, newest first.
2. Optional caption: a text file with the same name,
   `2026-10-07-morning-light.txt`. A blank line starts a new paragraph.
3. Run `make`.

Use .jpg, .png, .gif or .webp. Photos straight from an iPhone (.heic) are fine:
`make` turns each one into a .jpg of the same name, 2000px on the long side, with
the GPS location removed. The .heic stays in the folder but is never committed.
It uses the Mac's built-in `sips`; `pip3 install pillow pillow-heif` is optional.

Other images are published as they are, so export them at about 2000px on the
long side; `make` warns about files over 1.5 MB.

## Projects

Each project is a folder: `projects/mimic/index.md`, with its photos and videos
next to it. `make` builds `index.html` in the same folder and lists every project
on `/projects/` (ongoing ones first, then by `updated`). Frontmatter:

   ```
   ---
   title: MIMIC
   description: One sentence.
   status: ongoing
   started: September 2026
   updated: October 15, 2026
   ---
   ```

Add `draft: true` to keep it off the list. To update a project, add a dated
line under its `## Updates` heading and change `updated:`.

In the text:

- `![Caption](photo.jpg)` is a photo (.heic is converted, like the Gallery).
- `![Caption](clip.mov)` is a video. `make` converts .mov to a small .mp4 that
  every browser plays, removes the location and other metadata, and grabs a
  poster frame. The .mov stays in the folder but is never committed.
  Needs ffmpeg: `brew install ffmpeg`.
- `![Caption](clip.mov){.loop}` is a silent, autoplaying loop.
- `![Caption](https://youtu.be/...)` embeds a YouTube (or Vimeo) video. Use this
  for anything long; `make` warns when a clip gets big.
- `::: todo` ... `:::` makes a dashed reminder box, and `[text]{.tbd}` greys out
  a note to fill in later. Handy while drafting.

## Preview

`make serve`, then open http://localhost:8000. Paths start with `/`, so opening files directly from disk won't load the styles.

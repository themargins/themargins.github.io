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

## Preview

`make serve`, then open http://localhost:8000. Paths start with `/`, so opening files directly from disk won't load the styles.

# themargins.github.io

Personal essays. Static site, no framework.

## Writing an essay

1. Add `content/your_title.md` with frontmatter:

   ```
   ---
   title: Your Title
   description: One sentence.
   date: February 9, 2026
   ---
   ```

2. Run `make`. Each `content/*.md` becomes `writing/*.html` through `templates/post.html`.
3. Add a line for it to the list in `index.html`.

## Margin notes

Inside a paragraph, write `<span class="marginnote">A side remark.</span>`. On wide screens it sits in the margin; on narrow ones it drops below the paragraph.

## Preview

`make serve`, then open http://localhost:8000. Paths start with `/`, so opening files directly from disk won't load the styles.

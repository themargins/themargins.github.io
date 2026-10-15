SRC := $(wildcard content/*.md)
OUT := $(patsubst content/%.md,writing/%.html,$(SRC))

all: $(OUT) home gallery projects

# Always rebuilt (it's quick), so no page is left on an old template
writing/%.html: content/%.md templates/post.html FORCE
	@mkdir -p writing
	pandoc -s $< --template=templates/post.html --wrap=none -o $@

# Rebuild the essay list on the home page from the frontmatter
home:
	python3 build_index.py

# Rebuild the Gallery from the images in art/images/
gallery:
	python3 build_gallery.py

# Build each projects/<name>/index.md, convert its photos and videos, rebuild /projects/
projects:
	python3 build_projects.py

serve:
	python3 -m http.server 8000

clean:
	rm -f $(OUT)

.PHONY: all home gallery projects serve clean FORCE
FORCE:

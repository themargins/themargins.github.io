SRC := $(wildcard content/*.md)
OUT := $(patsubst content/%.md,writing/%.html,$(SRC))

all: $(OUT) home

writing/%.html: content/%.md templates/post.html
	@mkdir -p writing
	pandoc -s $< --template=templates/post.html --wrap=none -o $@

# Rebuild the essay list on the home page from the frontmatter
home:
	python3 build_index.py

serve:
	python3 -m http.server 8000

clean:
	rm -f $(OUT)

.PHONY: all home serve clean

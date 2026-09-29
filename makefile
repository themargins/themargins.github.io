SRC := $(wildcard content/*.md)
OUT := $(patsubst content/%.md,writing/%.html,$(SRC))

all: $(OUT)

writing/%.html: content/%.md templates/post.html
	@mkdir -p writing
	pandoc -s $< --template=templates/post.html --wrap=none -o $@

serve:
	python3 -m http.server 8000

clean:
	rm -f $(OUT)

.PHONY: all serve clean

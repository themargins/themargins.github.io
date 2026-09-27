build:
	@mkdir -p posts
	@for f in content/*.md; do \
		filename=$$(basename "$$f" .md); \
		echo "Processing $$f -> writing/$$filename.html"; \
		pandoc "$$f" \
			--template=templates/post.html \
			-o "writing/$$filename.html"; \
	done

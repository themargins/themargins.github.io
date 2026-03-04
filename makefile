build:
	@mkdir -p posts
	@for f in content/*.md; do \
		filename=$$(basename "$$f" .md); \
		echo "Processing $$f -> posts/$$filename.html"; \
		pandoc "$$f" \
			--template=templates/post.html \
			-o "posts/$$filename.html"; \
	done

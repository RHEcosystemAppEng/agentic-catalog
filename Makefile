.PHONY: help install generate serve test test-full clean check-uv

help:
	@echo "agentic-collections-catalog"
	@echo ""
	@echo "Available targets:"
	@echo "  install    - Install Python dependencies (requires uv)"
	@echo "  generate   - Generate docs/data.json from pack data"
	@echo "  serve      - Start local server on http://localhost:8000"
	@echo "  test       - Generate + verify site"
	@echo "  test-full  - Generate + serve with browser open"
	@echo "  clean      - Remove generated files"
	@echo ""
	@echo "Requirements:"
	@echo "  uv - Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"

check-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Error: uv is not installed"; \
		echo ""; \
		echo "Install uv with:"; \
		echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		echo ""; \
		echo "Or visit: https://github.com/astral-sh/uv"; \
		exit 1; \
	}

install: check-uv
	@echo "Installing Python dependencies with uv..."
	@uv sync
	@echo "Dependencies installed!"

generate: check-uv
	@echo "Generating documentation..."
	@uv run python scripts/build_website.py
	@echo "Documentation generated in docs/"

serve:
	@echo "Starting local server on http://localhost:8000"
	@echo "Press Ctrl+C to stop the server"
	@cd docs && python3 -m http.server 8000

test: generate
	@echo ""
	@echo "Running site verification..."
	@./scripts/test_local.sh
	@echo ""
	@echo "To view the site locally, run: make serve"

test-full: test
	@echo ""
	@echo "Opening browser and starting server..."
	@(sleep 2 && open http://localhost:8000) &
	@make serve

clean:
	@echo "Cleaning generated files..."
	@rm -f docs/data.json
	@rm -rf docs/collections/*.html
	@echo "Cleaned!"

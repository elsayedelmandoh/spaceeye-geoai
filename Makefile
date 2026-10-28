.PHONY: install run data current quality-report test lint format clean

# --- Environment ---
install:
	uv sync
	uv run nbstripout --install

# Full cached-source Track A + current Track B diagnostics. Includes model fitting.
run:
	uv run --locked --offline python -m src.pipeline.team_run --full

# Current prepared-data/model exports without fitting Track A again.
current:
	uv run --locked --offline python -m src.pipeline.team_run

# Prepared data only; no model fitting or image downloads.
data:
	uv run --locked --offline python -m src.pipeline.complete_data
	uv run --locked --offline python -m src.pipeline.component_data
	uv run --locked --offline python -m src.pipeline.source_catalog
	uv run --locked --offline python -m src.pipeline.quality_report

quality-report:
	uv run --locked --offline python -m src.pipeline.quality_report

# --- Quality ---
lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

test:
	uv run pytest tests/ -v

# --- Cleanup ---
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -type f -name '*.pyc' -delete; \
	rm -rf .pytest_cache

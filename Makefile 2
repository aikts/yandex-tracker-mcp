.PHONY: all check format format-check mypy test test-unit test-integration test-cov

all: lock format check

check: ruff-check format-check mypy

mypy:
	mypy .

ruff-check:
	ruff check .

format:
	ruff format .
	ruff check --select I,F401 --fix .

format-check:
	ruff format --check .

lock:
	uv lock && uv sync --dev

test:
	uv run pytest

test-unit:
	uv run pytest -m unit

test-integration:
	uv run pytest -m integration

test-cov:
	uv run pytest --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

dxt:
	mkdir -p dxt-lib
	uv export > requirements.txt
	uv pip install -r requirements.txt --target=dxt-lib
	cp images/tracker-logo.png .
	dxt pack . yandex-tracker-mcp.dxt

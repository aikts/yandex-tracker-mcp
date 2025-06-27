.PHONY: all check format format-check mypy

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

dxt:
	cp images/tracker-logo.png .
	dxt pack . yandex-tracker-mcp.dxt

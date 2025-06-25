.PHONY: all check format format-check mypy

all: lock format check

check: ruff-check format-check mypy

mypy:
	mypy .

ruff-check:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

lock:
	uv lock && uv sync --dev

.PHONY: install test lint web docs docs-serve clean

install:
	python -m pip install --index-url https://pypi.org/simple -e ".[web,docs,dev]"

test:
	pytest

lint:
	ruff check src tests

web:
	zymepage web

docs:
	mkdocs build --strict

docs-serve:
	mkdocs serve

clean:
	find src tests -type d -name __pycache__ -prune -exec rm -r {} +
	rm -rf .pytest_cache .ruff_cache site dist build

# Makefile
.PHONY: install check test cov run seed semantic-validate eval up down clean

install:
	uv sync

check:
	uv run ruff check src tests
	uv run ruff format --check src tests
	uv run mypy src

test:
	uv run pytest

cov:
	uv run pytest --cov --cov-report=term-missing

run:
	uv run uvicorn querypilot.service_boundary.app:app --reload

seed:
	uv run querypilot-seed generate

semantic-validate:
	uv run querypilot-semantic validate demo

# Consume el modelo real. NO forma parte del CI.
eval:
	uv run querypilot-eval run demo

up:
	docker compose up -d --build

down:
	docker compose down

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

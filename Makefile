.PHONY: help install dev test lint format clean docker-up docker-down docker-logs migrate seed docs-pdf

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies with Poetry"
	@echo "  make dev         - Run development server"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo "  make docker-up   - Start Docker services"
	@echo "  make docker-down - Stop Docker services"
	@echo "  make docker-logs - View Docker logs"
	@echo "  make migrate     - Run database migrations"
	@echo "  make seed        - Seed development data"
	@echo "  make docs-pdf    - Generate PDF documentation"
	@echo "  make clean       - Clean cache files"

install:
	poetry install

dev:
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest

lint:
	poetry run ruff check src tests
	poetry run mypy src

format:
	poetry run black src tests
	poetry run ruff check --fix src tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

docker-build:
	docker-compose build

migrate:
	docker-compose exec api alembic upgrade head

migrate-create:
	docker-compose exec api alembic revision --autogenerate -m "$(msg)"

seed:
	docker-compose exec api python scripts/seed_dev_data.py

psql:
	docker-compose exec postgres psql -U postgres -d agentic_platform

redis-cli:
	docker-compose exec redis redis-cli

docs-pdf:
	@echo "Generating PDF documentation..."
	@./scripts/generate_docs_pdf.sh

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Which entry from ingestion/sources.yml `make land` uses.
SOURCE ?= contoso_100k

.PHONY: help setup up down reset logs land lint format

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

.env:
	cp .env.example .env
	@echo "Created .env from .env.example - change the passwords before sharing anything."

setup: .env ## Install Python dependencies and git hooks
	uv sync
	uv run pre-commit install

up: .env ## Start Postgres and Metabase (http://localhost:3000)
	docker compose up -d

down: ## Stop the containers (data is kept)
	docker compose down

reset: ## Stop the containers and DELETE the Postgres volume
	docker compose down -v

logs: ## Follow container logs
	docker compose logs -f

land: ## Download a source into the landing zone (SOURCE=contoso_100k|contoso_10k)
	uv run python -m ingestion.land_source $(SOURCE)

lint: ## Check code style
	uv run ruff check .
	uv run ruff format --check .

format: ## Auto-fix code style
	uv run ruff check --fix .
	uv run ruff format .

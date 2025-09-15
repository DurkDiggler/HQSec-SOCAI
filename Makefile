.PHONY: setup run test fmt build up down schema

setup:
	pip install -r requirements.txt && pre-commit install

run:
	docker compose up --build

test:
	@if [ "$(docker)" = "1" ]; then \
		docker build --target dev -t soc-agent:dev . && \
		docker run --rm -v $$(pwd):/app -w /app soc-agent:dev pytest -q --cov soc_agent --cov-report=term-missing; \
	else \
		PYTHONPATH=src pytest -q --cov soc_agent --cov-report=term-missing; \
	fi

fmt:
	ruff check --fix && ruff format

build:
	docker build -t soc-agent:latest .

up:
	docker compose up -d --build

down:
	docker compose down

schema:
	python scripts/gen_schema.py > schema.json

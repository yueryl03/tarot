.PHONY: install migrate seed api test simulation docker-up docker-db

PYTHON ?= python3.12

install:
	$(PYTHON) -m pip install -e ".[dev]"

migrate:
	alembic upgrade head

seed:
	$(PYTHON) -m app.db.seed

api:
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(PYTHON) -m pytest

simulation:
	$(PYTHON) -m scripts.shuffle_simulation

docker-db:
	docker compose up -d db

docker-up:
	docker compose up --build

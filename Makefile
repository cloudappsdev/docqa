.PHONY: up down ingest run test lint
up:
	docker compose up --build -d
down:
	docker compose down
ingest:
	python -m docqa.ingest data/raw
run:
	uvicorn docqa.api.main:app --reload
test:
	pytest -q
lint:
	ruff check .

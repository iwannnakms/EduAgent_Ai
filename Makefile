SHELL := /bin/bash

.PHONY: bootstrap frontend-bootstrap start up down logs restart ps worker api frontend clean dev-local

dev-local: bootstrap
	./start-dev.sh

bootstrap:
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@mkdir -p data/uploads data/tmp data/chroma data/chroma-server

frontend-bootstrap:
	cd frontend && npm install

start: bootstrap
	docker compose up --build

up: bootstrap
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=150

restart:
	docker compose down && docker compose up --build -d

ps:
	docker compose ps

api:
	docker compose logs -f api

worker:
	docker compose logs -f worker

frontend:
	docker compose logs -f frontend

clean:
	docker compose down -v --remove-orphans

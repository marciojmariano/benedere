# Variáveis
APP_NAME = benedere
DOCKER_COMPOSE = docker-compose
APP_SERVICE = app

.PHONY: dev migrate test lint clean shell

# --- Comandos de Desenvolvimento Local ---

dev: ## Executa o servidor FastAPI com Hot-Reload (Local)
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate: ## Aplica as migrações no banco de dados (Local)
	poetry run alembic upgrade head

makemigrations: ## Gera nova migração (Ex: make makemigrations m="descrição")
	poetry run alembic revision --autogenerate -m "$(m)"

# --- Comandos via Docker (Padronização de Equipe/CI) ---

up: ## Sobe toda a infraestrutura (DB, Redis, App) no Docker
	$(DOCKER_COMPOSE) up -d --build

test: ## Roda a bateria de testes com cobertura (Garante Isolamento)
	$(DOCKER_COMPOSE) exec $(APP_SERVICE) pytest tests/ -vv --cov=app

lint: ## Verifica a qualidade do código (Ruff)
	$(DOCKER_COMPOSE) exec $(APP_SERVICE) ruff check app/

# --- Utilitários ---

shell: ## Abre um terminal interativo dentro do container da aplicação
	$(DOCKER_COMPOSE) exec $(APP_SERVICE) /bin/bash

clean: ## Remove lixo de compilação do Python
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

help: ## Lista todos os comandos do Makefile
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
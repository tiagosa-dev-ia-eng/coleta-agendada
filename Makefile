# Coleta Agendada — comandos padrão (M0). Fonte: PLANO_DE_IMPLEMENTACAO.md
SHELL := /bin/bash
BACKEND := backend
FRONTEND := frontend
COMPOSE := infra/docker-compose.yml

# Ferramentas do backend: preferem .venv; usam .pylibs quando o ambiente não
# oferece ensurepip/venv (caso desta máquina — ver AGENTS.md §8).
# PYTHONPATH é relativo ao backend porque as receitas fazem cd para lá.
ifeq ("$(wildcard $(BACKEND)/.venv/bin/python)","")
  BEPY := python3
  RUFF := .pylibs/bin/ruff
  PYTHONPATH := .pylibs
else
  BEPY := .venv/bin/python
  RUFF := .venv/bin/ruff
  PYTHONPATH :=
endif
export PYTHONPATH

.PHONY: help backend-install backend-check backend-test backend-lint backend-run backend-migrate         frontend-install frontend-dev frontend-build frontend-lint         infra-up infra-up-full infra-down infra-logs smoke

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

# ---------- backend (Django + DRF) ----------
backend-install: ## Instala dependências do backend (usa .pylibs quando não há venv)
	python3 -m pip install --quiet --target $(BACKEND)/.pylibs -r $(BACKEND)/requirements-dev.txt

backend-check: ## django system check
	cd $(BACKEND) && $(BEPY) manage.py check

backend-test: ## roda a suíte pytest
	cd $(BACKEND) && $(BEPY) -m pytest

backend-lint: ## ruff (apps, config, manage.py)
	cd $(BACKEND) && $(RUFF) check apps config manage.py

backend-migrate: ## aplica migrações no banco ativo
	cd $(BACKEND) && $(BEPY) manage.py migrate --noinput

backend-run: ## sobe o servidor de dev em :8000
	cd $(BACKEND) && $(BEPY) manage.py runserver 0.0.0.0:8000

# ---------- frontend (Next.js) ----------
frontend-install: ## instala dependências do frontend (pnpm)
	cd $(FRONTEND) && pnpm install

frontend-dev: ## sobe o Next.js em :3000
	cd $(FRONTEND) && pnpm dev

frontend-build: ## build de produção
	cd $(FRONTEND) && pnpm build

frontend-lint: ## eslint
	cd $(FRONTEND) && pnpm lint

# ---------- infra (docker compose) ----------
infra-up: ## sobe apenas banco + redis
	docker compose -f $(COMPOSE) up -d db redis

infra-up-full: ## sobe a stack completa (backend + frontend também)
	docker compose -f $(COMPOSE) --profile full up -d --build

infra-down: ## derruba a stack
	docker compose -f $(COMPOSE) down

infra-logs: ## logs da stack
	docker compose -f $(COMPOSE) logs -f

# ---------- smoke ----------
smoke: ## verifica health checks do backend (dev na porta 8000)
	curl -s http://localhost:8000/health && echo && curl -s http://localhost:8000/ready && echo

# ---------- versão interna (REGRA GERAL: bump a cada mudança e publicar) ----------
version: ## mostra a versão atual do projeto
	@cat VERSION

version-patch: ## bump patch (correções) — rode e envie VERSION/CHANGELOG ao GitHub
	@bash scripts/bump-version.sh patch

version-minor: ## bump minor (novas funcionalidades)
	@bash scripts/bump-version.sh minor

version-major: ## bump major (mudanças que quebram contrato/domínio)
	@bash scripts/bump-version.sh major

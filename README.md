# Coleta Agendada

Plataforma que digitaliza o processo de solicitação, orçamento, aprovação, agendamento e realização de **coletas de exames laboratoriais**, conectando laboratórios, revendedores, farmácias, técnicos de enfermagem e pacientes — via **Web App** e **WhatsApp + IA**.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Django + Django REST Framework |
| Frontend | Next.js + Tailwind CSS |
| Banco | PostgreSQL |
| Cache | Redis |
| IA | DeepSeek |
| WhatsApp | Webhook próprio |
| Auth | JWT + refresh token |
| Autorização | RBAC (5 perfis) |

## Estrutura

```text
├── AGENTS.md                        # guia para agentes de codificação
├── PLANO_DE_IMPLEMENTACAO.md        # plano em marcos M0–M11
├── backend/                         # API Django + DRF
├── frontend/                        # Web app Next.js
├── infra/                           # docker-compose, nginx, CI
└── docs/
    ├── Coleta_Agendada_Documentacao_Tecnica_v1.0/   # documentação-fonte (docs 01–18)
    ├── demandas.md                      # demandas do alinhamento (D-01/D-02)
    └── BACKEND_GUIA_IA.md               # guia vivo do backend p/ IAs de código
```

## Documentação

- **Fonte da verdade:** `docs/Coleta_Agendada_Documentacao_Tecnica_v1.0/` (docs 01–18).
- **Demandas do alinhamento:** `docs/demandas.md` (D-01/D-02).
- **Demandas de FRONTEND (handoff):** `docs/demandas-frontend.md`.
- **Guia vivo do backend (IAs de código):** `docs/BACKEND_GUIA_IA.md` — atualizar a cada mudança no backend.
- **Como trabalhar:** leia `AGENTS.md` antes de codificar.
- **Roteiro de execução:** `PLANO_DE_IMPLEMENTACAO.md`.
- **Versão interna:** `VERSION` (semver) + `CHANGELOG.md` — **a cada mudança** incremente e publique no GitHub; consultar via `GET /api/v1/version`.

## Como rodar (M0 — bootstrap)

Requisitos: Docker + Compose, Python 3.12, Node 22+ com pnpm. Comandos via `make` (veja `make help`).

```bash
# 1) banco + redis (Postgres em :5433, Redis em :6380)
make infra-up

# 2) dependências do backend e do frontend
make backend-install
cd frontend && pnpm install && cd ..

# 3) backend (Django, :8000)
make backend-run            # health: http://localhost:8000/health e /ready

# 4) frontend (Next.js, :3000) — exige NEXT_PUBLIC_API_URL (frontend/.env)
make frontend-dev
```

Alternativa em containers: `make infra-up-full` sobe toda a stack.

Qualidade: `make backend-test backend-lint frontend-lint frontend-build`.

> Nota desta máquina: Python sem `ensurepip`/sudo → deps do backend em `backend/.pylibs`
> (auto-detectado pelo Makefile). pnpm exige XDG dirs no workspace (ver AGENTS.md §8).
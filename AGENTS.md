# AGENTS.md — Coleta Agendada

Guia de trabalho para agentes de codificação (IA ou humanos) atuando neste repositório.

## 1. O projeto em uma frase

**Coleta Agendada** é uma plataforma que digitaliza o processo de solicitação, orçamento, aprovação,
agendamento e realização de **coletas de exames laboratoriais**, conectando **laboratórios,
revendedores, farmácias, técnicos de enfermagem e pacientes** via Web App e WhatsApp + IA.

## 2. Fonte da verdade — LEIA ANTES DE CODIFICAR

A definição do produto e da implementação vive em:

```text
docs/Coleta_Agendada_Documentacao_Tecnica_v1.0/
```

Esse pacote contém 18 documentos numerados (`01-…` a `18-…`), o consolidado
`DOCUMENTACAO_TECNICA_COLETA_AGENDADA_v1.0.md` e o `README.md` do pacote, que define a
**regra de interpretação** de toda decisão documentada:

| Marcação | Significado | Ação do agente |
|---|---|---|
| **CONFIRMADO** | Aparece explicitamente no material original | Implementar conforme documentado |
| **INFERIDO** | Decorreu dos fluxos/telas fornecidos | Implementar, mas validar com o usuário quando tocar regra de domínio |
| **PROPOSTO** | Recomendação técnica para completude | Implementar somente com confirmação do usuário (afeta escopo/domínio) |
| **PENDENTE** | Necessita decisão de PO/equipe | **NÃO implementar.** Perguntar ao usuário antes |

### Mapa rápido de documentos

| Área / tarefa | Documento de referência |
|---|---|
| Visão, escopo, canais, fora de escopo | `01-visao-produto-e-escopo.md` |
| Requisitos funcionais (RF-xxx) e prioridades | `02-requisitos-funcionais.md` |
| Stack, arquitetura lógica, módulos, responsabilidades | `03-arquitetura-tecnica.md` |
| Perfis e matriz RBAC | `04-perfis-rbac.md` |
| Fluxo e máquina de estados | `05-fluxo-agendamento-e-estados.md` |
| Modelo de dados / entidades | `06-modelo-de-dados.md` |
| Contrato REST (base `/api/v1/`) | `07-api-rest.md` |
| WhatsApp + IA (DeepSeek) | `08-whatsapp-e-ia.md` |
| Orçamentos e validação humana (RN-ORC) | `09-orcamentos-e-validacao-humana.md` |
| Pagamentos e comissões | `10-pagamentos-e-comissoes.md` |
| Segurança, privacidade, auditoria | `11-seguranca-privacidade-e-auditoria.md` |
| Logs, correlação, métricas, KPIs | `12-observabilidade-e-logs.md` |
| Infraestrutura, ambientes, CI/CD, backup | `13-infraestrutura-e-deploy.md` |
| Testes e critérios de aceite (CT-INT) | `14-testes-e-criterios-de-aceite.md` |
| Roadmap, riscos, pendências de decisão | `15-roadmap-riscos-e-pendencias.md` |
| **Regras obrigatórias para IA de codificação** | `16-guia-para-ia-de-codificacao.md` |
| User stories e backlog inicial (US-xxx) | `17-user-stories-e-backlog-inicial.md` |
| Decisões arquiteturais (ADR-001..010) | `18-decisoes-arquiteturais-adr.md` |
| **Demandas do alinhamento (D-xx)** | `docs/demandas.md` — registro vivo das demandas do cliente |
| **Guia vivo do backend p/ IAs de código** | `docs/BACKEND_GUIA_IA.md` — REGRA GERAL: atualizar a cada mudança no backend |

O plano de implementação do projeto está em `PLANO_DE_IMPLEMENTACAO.md` (raiz).

## 3. Stack e arquitetura alvo

| Camada | Tecnologia | Fonte |
|---|---|---|
| Backend | Django + Django REST Framework | CONFIRMADO (ADR-001) |
| Frontend | Next.js (+ Tailwind CSS) | CONFIRMADO (ADR-002) |
| Banco de dados | PostgreSQL (containers Docker) | CONFIRMADO (ADR-003) |
| Cache / rate limiting | Redis | CONFIRMADO (ADR-004) |
| IA | DeepSeek (API externa) | CONFIRMADO (ADR-005) |
| WhatsApp | Webhook próprio | CONFIRMADO (ADR-006) |
| Autenticação | JWT + refresh token | CONFIRMADO |
| Autorização | RBAC com 5 perfis | CONFIRMADO |

Regras arquiteturais (doc 03 §5 e ADRs):
1. A IA **não** escreve o orçamento final (ADR-007 — human-in-the-loop).
2. Toda transição crítica acontece no **backend** (ADR-009).
3. O **frontend nunca é fonte de verdade** para estados.
4. O banco mantém histórico de transições (auditoria).
5. Comissão é calculada por regra **persistida e versionada** (ADR-010).
6. Integrações externas ficam desacopladas por serviços/adapters (R-006).

## 4. Estrutura de diretórios alvo

```text
coleta-agendada/
├── AGENTS.md
├── PLANO_DE_IMPLEMENTACAO.md
├── backend/                  # Django + DRF (monolito modular, um app por domínio)
│   ├── config/               # settings, urls, wsgi/asgi
│   ├── apps/
│   │   ├── accounts/         # User, Role, Permission, auth JWT
│   │   ├── organizations/    # Laboratory, Reseller, Pharmacy
│   │   ├── patients/
│   │   ├── technicians/
│   │   ├── requests/         # CollectionRequest + estados + histórico
│   │   ├── quotations/       # rascunho x final, versões, validação humana
│   │   ├── scheduling/       # Appointment, agenda, check-in/out
│   │   ├── payments/         # links, webhook idempotente
│   │   ├── commissions/      # CommissionRule + lançamentos
│   │   ├── whatsapp/         # webhook, conversas, mensagens
│   │   ├── ai/               # adapter DeepSeek + validação de saída
│   │   └── audit/            # AuditLog
├── frontend/                 # Next.js (áreas por perfil)
│   ├── paciente/
│   ├── farmacia/
│   ├── tecnico/
│   ├── revendedor/
│   └── laboratorio/
├── infra/                    # docker compose, nginx, CI/CD, scripts
└── docs/
    └── Coleta_Agendada_Documentacao_Tecnica_v1.0/
```

## 5. Regras de negócio inegociáveis

Fonte: doc 16 (regras obrigatórias), docs 05/09/10 e ADRs. Violar qualquer item abaixo
**quebra o domínio** — o agente deve recusar/avisar em vez de "resolver" criativamente.

1. **Não inventar regra de negócio.** Tudo que não estiver documentado é pergunta ao usuário.
2. **Rascunho ≠ orçamento final** (RN-ORC-001). Existem dois objetos distintos no domínio.
3. **Orçamento final exige validação humana** (RN-ORC-002/003): só pode ser enviado com
   `validated_by` e `validated_at` preenchidos. `/send` rejeita orçamento não validado.
4. **Pagamento não bloqueia a realização da coleta** (ADR-008, RN-ORC/CT-INT-005): `COMPLETED`
   não depende de `PAYMENT_CONFIRMED`.
5. **Estados só mudam via serviços de domínio** (ex.: `RequestStateService.transition()`) —
   nunca diretamente em views ou pelo frontend.
6. **Toda transição crítica é auditada** (linha em histórico/audit: anterior, novo, responsável, data, origem, motivo).
7. **RBAC aplicado no backend.** Frontend não decide permissão (menor privilégio, doc 04 §4).
8. **Webhooks idempotentes** (CT-INT-008): mensagem duplicada não duplica operação.
9. **Comissão** usa regra persistida/versionada (ADR-010): gravar regra usada + base de cálculo no lançamento; sem recálculo silencioso; estorno explícito.
10. **IA nunca confirma:** preço sem base confiável; pagamento; disponibilidade inexistente; coleta realizada.
11. **Saída do LLM é entrada não confiável:** validar via schema antes de persistir (doc 16 §segurança).
12. **Rascunho gerado por IA não é enviado automaticamente** (RF-005); validar confiança e encaminhar a humano quando baixa (doc 08 §6).

## 6. Domínio central — perfis e estados

Perfis (doc 04): Laboratório, Revendedor, Farmácia, Técnico de enfermagem, Paciente.

Máquina de estados principal (doc 05): `REQUESTED → QUOTE_DRAFT → WAITING_HUMAN_VALIDATION →
QUOTE_SENT → APPROVED → SCHEDULED → (IN_PROGRESS) → COMPLETED`; `QUOTE_SENT → CANCELED`;
após coleta: `PAYMENT_PENDING/PAYMENT_CONFIRMED` e `COMMISSION_PENDING/COMMISSION_GENERATED`.

Cadeia crítica: **IA → rascunho → validação humana → orçamento final → paciente** (doc 05 §3).

## 7. Definition of Done — uma feature só está pronta com (doc 16 + doc 14)

- [ ] Leitura do(s) documento(s) de referência; itens PENDENTES/PROPOSTOS confirmados com o usuário;
- [ ] unit test do serviço/regra;
- [ ] permission/RBAC test;
- [ ] happy path completo;
- [ ] teste de transição de estado inválida;
- [ ] registro de audit log verificado;
- [ ] teste de idempotência (quando aplicável);
- [ ] migrations revisadas (sem dados sensíveis; sem secrets no código);
- [ ] sem lógica de domínio em views/controllers (vai para serviço de domínio).

## 8. Convenções de trabalho

- Sempre responder em **português (pt-BR)** com o usuário.
- Antes de implementar uma tarefa: localize RF/US/ADR correspondente na documentação e informe a fonte.
- Itens **PENDENTE** = pergunta ao usuário; nunca implementar silenciosamente.
- Itens **PROPOSTO** que alterem escopo/domínio = confirmar antes.
- Commits pequenos e descritivos (Conventional Commits recomendado: `feat:`, `fix:`, `test:`, `docs:`, `chore:`).
- Secrets nunca no repositório: usar variáveis de ambiente (doc 13 §4 lista as esperadas).
- Mudanças estruturais relevantes devem atualizar este AGENTS.md e/ou o `PLANO_DE_IMPLEMENTACAO.md`.
- Toda mudança/melhoria no **backend** DEVE atualizar o `docs/BACKEND_GUIA_IA.md` (seções afetadas + histórico) — REGRA GERAL.
- Demandas do cliente são registradas em `docs/demandas.md` e implementadas em **commit separado** documentando a demanda.

### Comandos padrão (registrados no M0)

Tudo via `make` na raiz (`make help` lista os alvos):

| Comando | Efeito |
|---|---|
| `make infra-up` | sobe banco+redis (Postgres :5433, Redis :6380 — ver infra/docker-compose.yml) |
| `make infra-up-full` | sobe a stack completa em containers |
| `make backend-install` | instala deps do backend |
| `make backend-check` | `backend-test` | `backend-lint` | Django check / pytest / ruff |
| `make backend-run` | servidor Django dev em :8000 |
| `make frontend-dev` | Next.js dev em :3000 (variáveis em `frontend/.env`, ver .env.example) |
| `make frontend-build` | `frontend-lint` | build / eslint |
| `make smoke` | curl nos health checks do backend |

Notas de ambiente desta máquina: (1) o Python do sistema não tem `ensurepip` e o sudo está
indisponível, então o backend usa `backend/.pylibs` (pip `--target`) em vez de `.venv` —
o Makefile detecta `.venv` automaticamente se existir; (2) pnpm precisa de
`XDG_CACHE_HOME`/`XDG_DATA_HOME`/`XDG_CONFIG_HOME` apontando para dentro do workspace
(dirs `.cache/.data/.config`, gitignorados) para gravar caches.
Versões: Backend Django 5.2 + DRF (py3.12); Frontend Next.js 16 + React 19 + Tailwind v4.

## 9. Pendências conhecidas — NÃO implementar sem decisão

Lista consolidada em `PLANO_DE_IMPLEMENTACAO.md` (§ Gate de decisões) e doc 15 §3. As principais:

- **Produto:** política de reagendamento/cancelamento; validade do orçamento; catálogo de exames; origem oficial dos preços; modalidades finais de coleta.
- **Financeiro:** gateway de pagamento; gatilho exato da comissão "a pagar"; estorno; taxas; conciliação.
- **WhatsApp:** provedor/payload do webhook; templates; autenticação.
- **IA:** modelo DeepSeek exato; prompt; temperatura; confiança mínima; fallback; custo.
- **Infra:** provedor cloud; domínio; storage de anexos; worker assíncrono; monitoração.
- **Privacidade/LGPD:** retenção; consentimento; política de acesso; exclusão/correção.
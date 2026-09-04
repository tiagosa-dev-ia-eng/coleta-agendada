# BACKEND_GUIA_IA.md — Guia vivo do backend (Coleta Agendada)

Documentação **operacional e de arquitetura do backend** para **análises futuras
por outras IAs de codificação** (e humanos). É um documento **vivo**: descreve o
código como ele **está**, não como foi planejado.

> ## 🚨 REGRA GERAL
> **Toda mudança ou melhoria no backend DEVE atualizar este documento** — nas
> seções afetadas **e** no *Histórico de mudanças* (§10). Se uma mudança tornar
> uma afirmação aqui obsoleta, corrija-a no mesmo commit. (Regra também gravada
> no AGENTS.md §8.)

Fontes de verdade complementares: `docs/Coleta_Agendada_Documentacao_Tecnica_v1.0/`
(docs 01–18; marcações CONFIRMADO/INFERIDO/PROPOSTO/PENDENTE), `docs/demandas.md`
(demandas do cliente) e `AGENTS.md` (regras de domínio e DoD).

---

## 1. Stack e ambiente de execução

| Item | Valor |
|---|---|
| Framework | Django 5.2 + Django REST Framework (Python 3.12) |
| Banco | PostgreSQL via Docker (dev: `infra/docker-compose.yml`, porta 5433) |
| Cache/rate limit | Redis (dev: porta 6380) |
| Auth | JWT (`rest_framework_simplejwt`) + refresh token |
| Autorização | RBAC com 5 perfis (doc 04) — catálogo em `apps.accounts.rbac` |
| IA | DeepSeek (API externa via `urllib`, sem dependência extra) em `apps.ai.client` |
| Lint/teste | ruff (line-length 100) + pytest (`config.settings.test`) |

### Rodar (Makefile na raiz)
```bash
make backend-install      # deps (nesta máquina: backend/.pylibs via pip --target)
make backend-check        # django check
make backend-lint         # ruff apps config manage.py
make backend-test         # pytest completo
make backend-run          # runserver :8000
```

**Notas de ambiente desta máquina:** Python do sistema sem `ensurepip`/sudo →
deps em `backend/.pylibs` (o Makefile prefere `.venv` se existir); rodar pytest
com `cd backend && PYTHONPATH=.pylibs python3 -m pytest`.

---

## 2. Arquitetura

Monolito modular Django — **um app por domínio** (ADR-001). Regras arquiteturais
que **valem sempre** (AGENTS.md §3/§5):

1. Toda transição crítica de estado ocorre **no backend**, em serviço de domínio (nunca em views).
2. **Frontend nunca é fonte de verdade** para estados.
3. LLM/IA **nunca** escreve orçamento final, confirma preço/pagamento/disponibilidade/coleta, nem inventa exame.
4. Saída do LLM é **entrada não confiável**: validar via schema antes de persistir (`apps.ai.schema`).
5. Webhooks e integrações são **idempotentes**; integrações externas ficam atrás de **adapters**.
6. Toda transição crítica é **auditada** (`apps.audit.models.record`).

### Mapa de apps

| App | Responsabilidade | Models principais | Serviços/chaves |
|---|---|---|---|
| `accounts` | User, Role, Permission, RBAC, auth JWT | `User`, `Role` | `rbac.py` (códigos/permissões), `services` |
| `organizations` | Laboratório, revendedor, farmácia; escopo por organização; **geolocalização de locais de coleta (D-01)** | `Laboratory`, `Reseller`, `Pharmacy` | `scope.laboratory_of()`, `geolocation.py` (Haversine, `nearest_collection_points`) |
| `patients` | Paciente (titular das solicitações) | `Patient` | — |
| `technicians` | Técnico de enfermagem | `Technician` | — |
| `requests` | Solicitação + pedido médico + máquina de estados + histórico | `CollectionRequest`, `MedicalOrder`, `RequestStatusHistory` | `statuses.py` (estados/modalidades), `RequestStateService` |
| `quotations` | Rascunho × final, versões, validação humana | `Quotation` | `QuotationService` |
| `scheduling` | Agendamento, check-in/out, conclusão | `Appointment` | `services.py` |
| `payments` | Link/webhook idempotente (adapter fake até G-02) | `Payment*` | `services.py` |
| `commissions` | Regra persistida/versionada (ADR-010) + lançamentos | `CommissionRule`, lançamentos | `services.py` |
| `whatsapp` | Webhook próprio, conversas, mensagens, **pipeline do chatbot** | `WhatsAppConversation`, `WhatsAppMessage` | `services.WhatsAppService` |
| `ai` | Adapter DeepSeek + validação de saída | — | `client.call_deepseek`, `mock.mock_analyze`, `schema.normalize_extraction` |
| `audit` | Trilha de auditoria | `AuditLog` | `record()` |
| `catalog` | Catálogo global de exames + preço manual por laboratório (G-01) | `Exam`, preços | `seed_catalog` (management command) |
| `core` | Health checks etc. | — | — |

---

## 3. Domínio central — estados (resumo)

Fluxo: `REQUESTED → QUOTE_DRAFT → WAITING_HUMAN_VALIDATION → QUOTE_SENT →
APPROVED → SCHEDULED → (IN_PROGRESS) → COMPLETED`; `QUOTE_SENT → CANCELED`.
Pós-coleta: `PAYMENT_PENDING/PAYMENT_CONFIRMED`, `COMMISSION_PENDING/COMMISSION_GENERATED`.

Proibições de domínio quebram a aplicação se violadas — **nunca "resolver
criativamente"**: rascunho ≠ orçamento final; envio exige validação humana
(`validated_by`/`validated_at`); pagamento **não** bloqueia conclusão da coleta;
comissão por regra versionada sem recálculo silencioso (detalhes no AGENTS.md §5).

---

## 4. Local de coleta (CollectionPoint) e geolocalização (D-01/D-03)

Ponto de coleta é **entidade de 1º nível** em `apps.collection_points`
(decisão D-03): hospedada por farmácia OU laboratório (cada um pode ou não ser
ponto). A **localização pertence ao ponto** — Pharmacy/Laboratory não carregam
coordenadas (migração organizations 0004).

- `CollectionPoint`: kind `pharmacy|laboratory`, laboratory da rede,
  pharmacy anfitriã (kind pharmacy), endereço/CEP/coordenadas próprios,
  `is_open`, status.
- `OpeningWindow`: grade semanal de janelas (weekday 0=seg..6=dom,
  open_time/close_time).
- `TechnicianAssignment`: designação de técnico FEITA PELO LABORATÓRIO.
- `CollectionPointSession`: check-in (abrir)/check-out (fechar) pelo técnico
  designado — estado `is_open` + auditoria.
- `apps/collection_points/services.py`: `check_schedule_availability`
  (janela + fechado hoje), `open_point`/`close_point`, `schedule_summary`
  (grade agrupada p/ texto) e `open_state_label`.
- `apps/collection_points/geolocation.py`: `haversine_km`,
  `valid_coordinates`, `parse_coordinates` e
  `nearest_collection_points(lab_id, lat, lon, limit)` → pontos ATIVOS com
  coordenadas; retorna `[(dist_km, kind, point)]`.
- **Agendamento em ponto** (AppointmentService): exige ponto ativo e
  disponibilidade (D-03). Domiciliar não usa ponto.
- **Chatbot (D-01):** responde o ponto mais próximo com endereço, distância,
  **horário** e estado (aberto/fechado), sem LLM; sem ponto georreferenciado →
  humano.
- Cadastro/operação via API `/api/v1/collection-points…` (ver §6).
  Geocodificação por CEP e mapas: **evolução futura**.

---

## 5. Pipeline do chatbot (WhatsApp + IA)

Caminho: `POST /api/v1/webhooks/whatsapp` → `whatsapp.views.InboundWhatsAppView`
→ `WhatsAppService.handle_inbound(payload)`:

1. Resolve/vincula conversa (`phone` único), paciente (pelo usuário autenticado ou telefone) e laboratório do canal.
2. **Idempotência:** `provider_message_id` repetido não reprocessa (CT-INT-008).
3. Grava mensagem inbound.
4. Decisão do caminho:
   - **Localização presente** (payload `location: {latitude, longitude}` ou texto "lat, lon") → extração determinística `intent=nearest_pharmacy` **sem LLM** (resolve via `nearest_collection_points` — CollectionPoint);
   - pergunta por local de coleta sem localização (heurística de termos) → pede compartilhamento;
   - senão → `DeepSeek` (ou `mock_analyze` sem chave) + `normalize_extraction` (schema) → `_act`.
5. Responde com mensagem outbound e audita (`whatsapp.message_processed`).

Intenções tratadas em `_act`: `create_collection_request`, `check_status`,
`nearest_pharmacy`, `help` (baixa confiança/`requires_human` → status `human`).

Regras do pipeline (AGENTS.md regras 10–12): IA nunca envia orçamento final nem
confirma dados; rascunho gerado por IA sempre passa por validação humana.

---

## 6. API REST — convenções (doc 07 + implementação)

- Base `/api/v1/`; erros em envelope `{"error": {"code", "message", "details"}}`.
- Auth: `Authorization: Bearer <access>` (JWT). RBAC no backend (`accounts.rbac.has_permission`, `organizations.scope`).
- CRUD por domínio em `urls.py`/`views.py` de cada app (list/create/retrieve/partial_update).
- Cadastros organizacionais criam **usuário + perfil** juntos (`_EntityBaseSerializer`),
  com escopo imposto pelo contexto da view (lab/revendedor nunca vêm do cliente).
- Webhook WhatsApp: `POST /api/v1/webhooks/whatsapp` aceita `from` + `body`
  **ou** `from` + `location`; `GET/DELETE /api/v1/whatsapp/conversations/by-phone/{phone}`.
- Locais de coleta: `/api/v1/collection-points` (CRUD, `windows`, `technicians`,
  `open`/`close`); contatos WhatsApp: `/api/v1/whatsapp/contacts` (D-04).

---

## 7. Testes e lint — convenções

```bash
cd backend && PYTHONPATH=.pylibs python3 -m pytest      # suíte completa
cd backend && PYTHONPATH=.pylibs .pylibs/bin/ruff check apps config manage.py
```

- Fixtures globais em `backend/conftest.py`: `seeded_roles` (autouse), `make_user(role_code=..., email=..., phone=...)`, `auth_client`, `anon_client`.
- Testes de domínio usam os serviços reais; IA usa `mock` quando não há `DEEPSEEK_API_KEY`.
- `settings` de teste em `config/settings/test.py` (base `config/settings/base.py`).
- DoD de backend (AGENTS.md §7): unit + RBAC + happy path + transição inválida +
  audit + idempotência + migrations revisadas + sem lógica de domínio em views.

---

## 8. Variáveis de ambiente importantes

`backend/.env` (gitignored; exemplo em `.env.example`): `DEEPSEEK_API_KEY`,
`DEEPSEEK_MODEL`, `DEEPSEEK_TEMPERATURE`, `AI_MIN_CONFIDENCE`, `WHATSAPP_PROVIDER`,
`WHATSAPP_WEBHOOK_SECRET`, `CORS_ALLOW_ALL_ORIGINS` (true só na demo). Nunca
versionar segredos.

---

## 9. Estrutura de diretórios backend (referência)

```text
backend/
├── manage.py
├── config/                  # settings/{base,development,production,test}.py, urls, api_urls
├── apps/
│   ├── accounts/            # auth JWT + RBAC
│   ├── audit/               # AuditLog (record)
│   ├── ai/                  # DeepSeek adapter + schema
│   ├── catalog/             # exames globais + preços
│   ├── commissions/         # regras/versionamento + lançamentos
│   ├── core/                # health/ready
│   ├── organizations/       # Laboratory/Reseller/Pharmacy + geolocation
│   ├── patients/
│   ├── payments/
│   ├── quotations/
│   ├── requests/            # estados/transições
│   ├── scheduling/
│   ├── technicians/
│   └── whatsapp/            # webhook + chatbot
```

---

## 10. Histórico de mudanças (REGRA GERAL — manter atualizado)

| Data | Mudança | Onde |
|---|---|---|
| 04/09/2026 | **D-01:** local de coleta mais próximo no chatbot (farmácia OU laboratório). Pharmacy e Laboratory ganham endereço/CEP/coordenadas (migrações 0002/0003); novo `organizations/geolocation.py` (`nearest_collection_points`); webhook aceita `location`; pipeline responde sem LLM; perguntas sem localização pedem compartilhamento; sem ponto georreferenciado → humano. Backend: 96 testes verdes. Commits `557fa23`, `bff0235`, `353d8a5`. | §4, §5, §6; docs/demandas.md |
| 04/09/2026 | Criação deste guia vivo + atualização de AGENTS.md/README/PLANO/docs (02, 06, 07, 08 + adendo no consolidado) conforme D-01. | este arquivo |
| 04/09/2026 | **D-03 (base):** app `collection_points` criado — `CollectionPoint` (kind pharmacy/laboratory, localização própria, `is_open`), `OpeningWindow` (grade semanal), `TechnicianAssignment` (designação pelo laboratório), `CollectionPointSession` (check-in/out); serviços de disponibilidade e abertura/fechamento. Integração (agendamento/chatbot) em andamento. | §2 |
| 04/09/2026 | **D-04:** `WhatsAppContact` (número + nome + BSUID Meta `@handle`) por perfil — técnico/revenda máx. 1; farmácia/laboratório lista; validators `normalize_phone_digits`/`validate_meta_bsuid`. | §2 (whatsapp) |
| 04/09/2026 | **D-03 (API/operação):** `collection-points` CRUD + janelas + designação + open/close (`8648461`). | §4, §6 |
| 04/09/2026 | **D-03 (agendamento):** AppointmentService exige ponto ativo e disponibilidade — janela + fechado hoje (`38fe807`). | §4 |
| 04/09/2026 | **D-03 (geoloc/chatbot):** geolocalização migra p/ CollectionPoint; Pharmacy/Laboratory sem coordenadas (migração orgs 0004); chatbot responde ponto + horário + estado (`02d96c4`). | §4, §5 |
| 04/09/2026 | **D-04 (API):** `/api/v1/whatsapp/contacts` com escopo por papel e regra 1 contato p/ técnico/revenda (`f98647a`). | §6 |
| 04/09/2026 | Documentação (docs 06/07/08, demandas, guia) consolidada para D-03/D-04. | este arquivo |
| 1.1.0 | 04/09/2026 | Controle de versão interna (VERSION/bump/endpoint /version) + regra geral de validação no backend. | §10/§11 |
| 1.1.1–1.1.5 | 04/09/2026 | Cobertura de endpoints: exames (CRUD), pagamentos (cancel/refund), auditoria (GET /audit, superusuário), contatos WhatsApp (PATCH) e revenda (GET/PATCH). | §6 |
| 1.1.6 | 04/09/2026 | Documentação desta entrega (endpoints listados acima). | este arquivo |

---

## 11. Controle de versão interna (REGRA GERAL)

- Arquivo-fonte: `VERSION` (raiz, semver MAJOR.MINOR.PATCH) + `CHANGELOG.md`.
- A cada mudança: `bash scripts/bump-version.sh [patch|minor|major]` (ou
  `make version-patch|version-minor|version-major`; default patch), atualize
  o CHANGELOG e **publique no GitHub** (mesmo commit/push da mudança).
- Endpoint: `GET /api/v1/version` → `{"name", "version"}` (lê VERSION).
- Histórico completo: tabela da §10 abaixo.
# Plano de Implementação — Coleta Agendada

**Versão:** 1.1
**Status:** M0, M1 e M2 executados em 03/09/2026 — revisão do usuário pendente; próximos marcos aguardando validação
**Fonte de definição:** pacote `docs/Coleta_Agendada_Documentacao_Tecnica_v1.0/` (docs 01–18 + consolidado)

Este plano organiza a implementação do projeto em **marcos (M0–M11)**, cada um com escopo, documentos de referência, entregáveis e critérios de saída. Ele **não substitui** a documentação técnica: para detalhes de cada área, consulte os documentos numerados (ver mapa no `AGENTS.md`).

---

## 1. Objetivo

Entregar o **MVP** (agendamentos, perfis, comissões, WhatsApp — doc 01 §5 e doc 15) sobre a stack recuperada (Django + DRF, Next.js + Tailwind, PostgreSQL, Redis, DeepSeek, webhook próprio de WhatsApp, JWT + RBAC), seguindo o roadmap V1.1/V1.2/V1.3 (doc 15 §1).

## 2. Princípios que regem o plano (fonte: doc 16, ADR-001..010)

1. Rascunho de orçamento **≠** orçamento final; validação humana é obrigatória antes do envio.
2. Pagamento **não bloqueia** a realização da coleta.
3. Estados mudam apenas por **serviços de domínio** no backend; frontend nunca é fonte de verdade.
4. Toda transição crítica é **auditada**; webhooks são **idempotentes**.
5. Comissão usa **regra persistida e versionada**; saída de IA é **entrada não confiável** (schema).
6. Itens **PENDENTE** na documentação exigem decisão antes de implementar (§ 9 — gates).

## 3. Estrutura alvo do repositório (monorepo)

```text
coleta-agendada/
├── AGENTS.md
├── PLANO_DE_IMPLEMENTACAO.md
├── README.md                        # visão + como rodar (M0)
├── backend/                         # Django + DRF — um app por domínio (doc 03)
│   ├── config/                      # settings (dev/staging/prod), urls, asgi/wsgi
│   ├── apps/                        # accounts, organizations, patients, technicians,
│   │                                # requests, quotations, scheduling, payments,
│   │                                # commissions, whatsapp, ai, audit, core
│   ├── manage.py
│   ├── pyproject.toml / requirements
│   └── tests/  (ou testes por app)
├── frontend/                        # Next.js + Tailwind — áreas por perfil (doc 04)
│   ├── app/  (rotas: paciente, farmacia, tecnico, revendedor, laboratorio, auth)
│   ├── components/, lib/ (api client, auth), styles/
│   └── package.json
├── infra/
│   ├── docker-compose.yml           # postgres + redis + backend + frontend (volumes externos)
│   ├── nginx/                       # reverse proxy / TLS (ambientes)
│   └── ci/                          # pipeline (M10)
└── docs/
    └── Coleta_Agendada_Documentacao_Tecnica_v1.0/
```

## 4. Marcos e sequência de execução

> Ordem recomendada por dependência: domínio primeiro (backend), depois canais (WhatsApp) e UI. Entre marcos, rodar a suíte de testes do marco anterior (regressão).

### M0 — Fundação e bootstrap do projeto
**Referências:** docs 03, 13; README do pacote.

- [ ] Inicializar monorepo e `git`; criar `README.md` raiz apontando para docs e plano.
- [ ] Criar `infra/docker-compose.yml`: PostgreSQL, Redis, backend Django e frontend Next.js com volumes externos mapeados para fontes e dados (conforme README do pacote).
- [ ] Bootstrap `backend/` (Django + DRF) com `config/`, apps base (`core`, `audit`), health checks (`GET /health`, `GET /ready` — doc 13 §8).
- [ ] Bootstrap `frontend/` (Next.js + Tailwind) com cliente de API e estrutura por perfil.
- [ ] Configuração 12-factors: variáveis de ambiente (doc 13 §4), settings por ambiente, secrets fora do repositório, `.env.example`.
- [ ] Ferramentas de qualidade: lint, formatador, testes, `migrations --check` (doc 13 §7).
- [x] Definição e registro dos **comandos padrão** (make/docker) no `AGENTS.md` §8.
- [ ] Revisão e aceite do plano de estrutura com o usuário. *(pendente)*

**Critério de saída:** ambiente sobe localmente com `docker compose up`; health checks respondem;
lint/testes passam; comandos registrados. **Resultado (03/09/2026):** `/health` e `/ready` OK;
pytest 2/2; ruff e eslint limpos; `frontend-build` compilando; compose validado. Nota de ambiente:
Python do host sem `ensurepip`/sudo → deps em `backend/.pylibs` (pip --target); pnpm requer XDG
dirs locais (gitignorados).

### M1 — Contas, autenticação e RBAC  ✅ (03/09/2026)
**Referências:** docs 02 (backlog P0), 03 §4 (`accounts`), 04, 06 (User/Role/Permission), 07 §2, 11; ADR-009; US do backlog técnico P0.
**Decisões:** `AUTH_USER_MODEL` = `accounts.User` customizado (login por e-mail) definido antes da primeira migração (dev DB regenerado no M1); escopo organizacional refinado no M2.

- [x] Modelos `User`, `Role`, `Permission` + seed dos **5 perfis** (Laboratório, Revendedor, Farmácia, Técnico, Paciente — doc 04).
- [x] JWT com access + refresh (login/refresh/logout/me); rotação e revogação de refresh (doc 11).
- [x] Bloqueio após tentativas inválidas (`MAX_LOGIN_ATTEMPTS=5`) e rate limit (`RATE_LIMIT_PER_HOUR=100`) parametrizados (doc 11 §2).
- [x] Framework de RBAC no backend (permissões por perfil + escopo organizacional, doc 04 §3-4); base para evitar IDOR.
- [x] Auditoria mínima de segurança: login, falha de login, bloqueio, criação/edição de usuário, alteração de permissão (doc 11 §5).
- [x] Testes RBAC (doc 14 §3): acesso cruzado entre perfis retorna 403.


**Resultado (03/09/2026):** pytest **23/23** (auth, rotação/blacklist, lockout, RBAC, seed idempotente); ruff limpo; smoke HTTP OK (login lab 200 com permissões; paciente → /users 403; lab cria técnico 201; lockout 401x4 → 423). Usuários demo de dev: lab@coleta.local, paciente@coleta.local, admin@coleta.local (senha SenhaForte123!). Nota DRF 3.16: AuthenticationFailed é tratado como 403 — usar exceções próprias com status_code explícito (services.InvalidCredentials / AccountLocked).
**Critério de saída:** CRUD de usuários restrito por perfil; todos os testes RBAC verdes; DoD completo.

### M2 — Cadastros organizacionais (Laboratório, Revendedor, Farmácia, Técnico, Paciente)  ✅ (03/09/2026)
**Referências:** docs 04, 06, 07 §9; US-014, US-015, US-017, US-018.
**Decisões:** vínculos laboratório/revendedor definidos **apenas pelo backend via contexto** da view (nunca aceitos do cliente); criação de perfil cria usuário+entidade juntos (auditado); farmácia/técnico enxergam somente o próprio registro (menor privilégio).

- [x] Apps `organizations`, `patients`, `technicians` com modelos e relacionamentos do doc 06 §2-3 (Laboratory, Reseller, Pharmacy, Technician, Patient).
- [x] Endpoints `/api/v1/laboratories|resellers|pharmacies|technicians|patients` com escopo de visão por perfil (menor privilégio).
- [x] Regras de vínculo: revendedor cadastra farmácia/técnico da própria rede; farmácia vinculada ao laboratório (doc 04).

**Resultado (03/09/2026):** pytest **40/40**; ruff limpo; smoke HTTP OK (lab cria revendedor/farmácia/técnico/paciente; revendedor cria farmácia da própria rede e lista só as suas; escopo entre laboratórios isolado). Apps: organizations, technicians, patients (migrações 0001).

**Critério de saída:** cadastros operacionais por perfil conforme matriz do doc 04 §2, com testes de permissão.

### M3 — Solicitações, pedido médico e máquina de estados
**Referências:** docs 02 (RF-001..003, RF-022), 05, 06 (CollectionRequest, MedicalOrder, CollectionRequestExam), 07 §3-4; US-001, US-003, US-005.

- [ ] Modelo `CollectionRequest` com `protocol` e dados de coleta (data/período/modalidade/local).
- [ ] Máquina de estados central (doc 05 §2) implementada como **serviço de domínio** (`RequestStateService`) com mapa de transições válidas; frontend não altera estados.
- [ ] Histórico de transições (`request_status_history`: anterior, novo, responsável, data/hora, origem, motivo, metadados — doc 05 §5).
- [ ] Upload/armazenamento de pedido médico com validação de tipo/tamanho (doc 11 §3).
- [ ] Endpoints `/api/v1/requests...` (doc 07 §3-4), incluindo `GET history` e `POST cancel`.

**Critério de saída:** CT-INT-001 parcial até `QUOTE_DRAFT`; transições inválidas rejeitadas; histórico auditável. *(Pende decisão de storage/validação de anexos — ver gate G-07.)*

### M4 — Orçamentos e validação humana
**Referências:** docs 02 (RF-004..009), 09 (RN-ORC-001..005), 07 §5; US-004, US-006, US-007; CT-INT-001/002/007; ADR-007.

- [ ] Domínio de orçamento com **dois objetos**: rascunho (IA ou manual) e orçamento final.
- [ ] Versionamento de orçamento (v1 rascunho → v2 corrigido → v3 enviado — doc 09 §4).
- [ ] Regras RN-ORC-001..003 no backend: orçamento final exige `validated_by`/`validated_at`; `/send` bloqueia orçamento não validado.
- [ ] RN-ORC-004 (PROPOSTO) e RN-ORC-005 (PROPOSTO): confirmar com o usuário antes de implementar (invalidação de validação pós-edição; registro da versão aprovada pelo paciente).
- [ ] Fluxo de aprovação/rejeição/cancelamento pelo paciente (estados do doc 05).
- [ ] Endpoints `quotations` (draft/validate/send/approve/reject — doc 07 §5).

**Critério de saída:** CT-INT-001, CT-INT-002 e CT-INT-007 verdes; rascunho nunca é enviável.

### M5 — Agendamento e realização da coleta
**Referências:** docs 02 (RF-010..013), 05, 06 (Appointment), 07 §6; US-008, US-010..012; CT-INT-003/004/005; doc 04 §2 (agenda por perfil).

- [ ] `Appointment` com modalidades: farmácia/ponto de coleta, domiciliar, laboratório (RF-010).
- [ ] Confirmação com protocolo, data, horário e local (RF-011); transições `APPROVED → SCHEDULED`.
- [ ] Agenda por perfil (farmácia e técnico — doc 04 §2) e atribuição de técnico.
- [ ] Check-in / check-out do técnico (RF-013, P1) e conclusão da coleta (RF-012), com o fluxo **`COMPLETED` independente de pagamento** (ADR-008 — testar CT-INT-005).
- [ ] Endpoints `appointments` (doc 07 §6). `reschedule` = PROPOSTO → confirmar antes.

**Critério de saída:** CT-INT-003/004/005 verdes; conclusão com pagamento pendente permitida.

### M6 — Pagamentos (não bloqueante)
**Referências:** docs 02 (RF-014..016), 10, 07 §7; CT-INT-005/006; doc 15 (gate financeiro).

- [ ] Modelos/estados de pagamento (doc 10 §2) e integração com a solicitação.
- [ ] **Adapter de gateway** (interface desacoplada — R-006) + link de pagamento opcional (RF-014) e registro de pagamento presencial (RF-015). *(Gateway real = gate G-02; MVP roda com adapter fake/sandbox.)*
- [ ] Webhook de pagamento **idempotente** com chave de idempotência (doc 07 §12; CT-INT-008).
- [ ] Endpoints `payments/link`, `payments/webhook`, `payments/{id}/confirm` (doc 07 §7).

**Critério de saída:** CT-INT-005 e CT-INT-006 verdes; duplicidade de webhook não duplica operação.

### M7 — Comissões
**Referências:** docs 02 (RF-017..019), 10, 06 (CommissionRule/Commission), 07 §8; US-009, US-013, US-016, US-019; ADR-010; CT-INT-006.

- [ ] `CommissionRule` persistida/versionada: beneficiary_type/id, `PERCENTAGE`/FIXED, trigger, vigência (`valid_from`/`valid_until`), `active` (doc 10 §7, doc 06).
- [ ] Cálculo via serviço `CommissionService.calculate()` gravando **regra usada + base de cálculo** no lançamento; sem recálculo silencioso (doc 16).
- [ ] Gatilho de geração e estado `COMMISSION_PENDING/GENERATED` (doc 05 §2) — *decisão exata do gatilho = gate G-03; manter coleta ≠ geração definitiva (doc 10 §5).*
- [ ] Estorno explícito, marcação de pago, extrato por beneficiário; endpoints do doc 07 §8.

**Critério de saída:** exemplos do doc 10 §3 (10%/15% percentual e valores fixos) cobertos por testes unitários; lançamentos imutáveis após geração.

### M8 — WhatsApp + IA (DeepSeek)
**Referências:** docs 02 (RF-020..022), 08, 06 (WhatsAppConversation/WhatsAppMessage), 07 §10; US-002; CT-INT-008; doc 15 §3 (WhatsApp/IA).

- [ ] Webhook próprio `/api/v1/webhooks/whatsapp` **idempotente** (doc 07 §10/§12); autenticação do webhook por secret (doc 13 §4). *(Provedor/payload = gate G-05.)*
- [ ] Modelos de conversa e mensagens com persistência de mensagem recebida, resposta enviada, interpretação da IA, modelo/versão, timestamps e erro (doc 08 §7).
- [ ] Adapter DeepSeek (desacoplado); extração estruturada com **validação por schema** antes de persistir (doc 16 §segurança); intenção, confiança, `missing_fields`, `requires_human` (doc 08 §5).
- [ ] Encaminhamento para humano quando a confiança for baixa (doc 08 §6).
- [ ] IA **proibida** de enviar orçamento final, confirmar preço/pagamento/disponibilidade/coleta (doc 08 §4) — garantido por regras no backend, não no prompt.

**Critério de saída:** conversa gera solicitação/protocolo válido (RF-022); saída de IA inválida é rejeitada pelo schema; duplicidade tratada (CT-INT-008).

### M9 — Frontend por perfil e dashboards
**Referências:** docs 01 §4, 04, 12 §5, 17 (US-001..019); RF-025/026 (P1).

- [ ] Fluxos do **paciente**: solicitar (site), anexar pedido, receber/enviar orçamento, aprovar, acompanhar status (US-001, US-003..005).
- [ ] Áreas **atendente/operação**: fila de validação humana e envio do orçamento (US-006/007).
- [ ] Agenda **farmácia** e **técnico** (+ check-in/out e conclusão) (US-008..013).
- [ ] **Revendedor**: cadastro de farmácia/técnico e acompanhamento de comissões (US-014..016).
- [ ] **Laboratório**: dashboard geral e relatórios financeiros/comissões (RF-025/026; US-017..019) — P1, após MVP.
- [ ] Login/refresh no cliente; rotas protegidas refletem RBAC **sem confiar nele** (regra 7 do AGENTS.md).

**Critério de saída:** jornadas completas por perfil contra API real; nenhuma permissão decidida só no frontend.

### M10 — Segurança, observabilidade e conformidade
**Referências:** docs 11, 12, 13, 14 §5-6.

- [ ] Headers de segurança, CORS restritivo, proteção CSRF quando aplicável, validação de upload e scan de anexos (doc 11 §3).
- [ ] `X-Request-ID` por requisição com correlação API/worker/IA/webhook/pagamento/logs (doc 12 §3).
- [ ] Logs estruturados com campos mínimos (doc 12 §2) e métricas de produto/infra (doc 12 §4).
- [ ] Trilha de auditoria imutável para eventos críticos (doc 11 §5).
- [ ] Revisão LGPD/privacidade: retenção, consentimento, acesso, exclusão/correção (doc 11 §4) — *depende do gate G-06.*
- [ ] Testes de segurança: brute force, JWT expirado, refresh revogado, IDOR, upload inválido, SQLi, XSS, CORS, rate limiting (doc 14 §5). Testes de carga com metas definidas (doc 14 §6).

**Critério de saída:** checklist de segurança verde; correlação ponta-a-ponta demonstrada; alertas básicos (doc 12 §6).

### M11 — Infraestrutura, CI/CD e deploy
**Referências:** doc 13; ADR; doc 15 §3 (infra).

- [ ] Ambientes dev/staging/prod com secrets segregados (doc 13 §3-4).
- [ ] CI/CD: lint → testes → build → scan de dependências → migrations check → deploy staging → smoke test → deploy produção → health check (doc 13 §7).
- [ ] Backup diário PostgreSQL + teste de restore + cópia fora do host + backup de anexos (doc 13 §6).
- [ ] Worker assíncrono para IA/mensagens/notificações/anexos/conciliação (doc 13 §5) — tecnologia a decidir (gate G-04).
- [ ] Proxy reverso/TLS para Next.js e Django (produção).
- [ ] Definir provedor cloud, domínio, object storage, monitoração, SLA, RPO/RTO (doc 13 §9 / gate G-04).

**Critério de saída:** pipeline verde end-to-end; restore testado; health checks em produção.

---

## 5. Mapeamento do backlog (doc 17) e roadmap (doc 15)

| Prioridade | Conteúdo | Marcos |
|---|---|---|
| P0 | autenticação, RBAC, solicitação, anexos, rascunho, validação humana, orçamento final, aprovação, agendamento, conclusão, comissão, WhatsApp | M1–M8 (MVP) |
| P1 | pagamento automático, relatórios avançados, notificações, conciliação, observabilidade, dashboards | M6, M9, M10 |
| P2 | app mobile, integração laboratorial, automações avançadas | pós-M11 (V1.2/V1.3) |

V1.1 (link de pagamento automático) = M6 completo. V1.2 (app mobile) e V1.3 (integração LIS) ficam fora do escopo atual (doc 01 §6).

## 6. Ordem de criação dos apps backend (dependências)

`core`/`audit` → `accounts` → `organizations` → `patients`/`technicians` → `requests` → `quotations` → `scheduling` → `payments` → `commissions` → `whatsapp`/`ai` (paralelos).

## 7. Estratégia de testes por marco

- Unitários por serviço de domínio (doc 14 §1): comissão, estados, RBAC, validação de orçamento, parser de IA, webhook.
- Integração CT-INT-001..008 (doc 14 §2) distribuídas: M3 (001 parcial), M4 (001/002/007), M5 (003/004/005), M6–M8 (005/006/008).
- RBAC (doc 14 §3) em M1 e reforçado em cada app.
- IA (doc 14 §4) em M8.
- Segurança (doc 14 §5) em M10.
- Regressão completa a cada marco.

## 8. Riscos e mitigações (doc 15 §2)

| Risco | Mitigação | Marco |
|---|---|---|
| R-001 IA gera informação incorreta | rascunho + validação humana obrigatória | M4/M8 |
| R-002 preço sem fonte de verdade | definir catálogo/origem de preço (gate G-01) | M4 |
| R-003 comissão inconsistente | regra versionada + lançamento imutável | M7 |
| R-004 vazamento de dados | RBAC, auditoria, HTTPS, LGPD (gate G-06) | M1/M10 |
| R-005 webhook duplicado | idempotência | M6/M8 |
| R-006 dependência de integração externa | adapters e retry | M6/M8 |

## 9. Gate de decisões — itens que **travam** ou condicionam marcos

Cada decisão deve ser registrada no doc 15 e marcada como CONFIRMADO/INFERIDO/PROPOSTO/PENDENTE.

| # | Decisão | Bloqueia | Status atual |
|---|---|---|---|
| G-01 | Catálogo de exames + **origem oficial dos preços** (tabela por laboratório/farmácia/unidade/integração?) | M4 (orçamento com valores) | PENDENTE |
| G-02 | Gateway de pagamento (provedor, sandbox, fluxo do link) | M6 (link real) | PENDENTE |
| G-03 | Gatilho exato da comissão "a pagar" (evento que gera) e regra de estorno | M7 | PENDENTE |
| G-04 | Infra: provedor cloud, domínio, object storage, worker assíncrono (tecnologia), RPO/RTO | M11 | PENDENTE |
| G-05 | WhatsApp: provedor, payload do webhook, autenticação, templates, mídias | M8 (produção) | PENDENTE |
| G-06 | Privacidade/LGPD: retenção, consentimento, política de acesso, exclusão/correção | M10 | PENDENTE |
| G-07 | Storage e política de anexos (pedido médico) | M3 | PENDENTE |
| G-08 | RN-ORC-004 (invalidação pós-edição) e RN-ORC-005 (versão aprovada) | M4 (regras) | PROPOSTO |
| G-09 | Reagendamento (`reschedule`), política de cancelamento, validade do orçamento | M5 | PENDENTE |
| G-10 | Parâmetros de IA: modelo DeepSeek, prompt, temperatura, confiança mínima, fallback, custo | M8 | PENDENTE |

> Enquanto um gate PENDENTE não for decidido, o marco correspondente avança com a parte **não bloqueada** (ex.: domínio de orçamento antes da origem de preços) ou com **adapter fake** (pagamento, WhatsApp, IA), conforme regra 6 do AGENTS.md.

## 10. Próximos passos imediatos

1. Validar este plano e o `AGENTS.md` com o usuário/PO.
2. Definir G-01, G-02, G-05 e G-07 (necessários no caminho do MVP) e marcar como CONFIRMADO/PROPOSTO.
3. Executar **M0** (bootstrap do monorepo e ambiente Docker) e registrar comandos padrão.
4. Iniciar **M1** (contas + RBAC) após bootstrap.
5. Registrar cada decisão nova no doc 15 (§3) para manter a documentação viva.
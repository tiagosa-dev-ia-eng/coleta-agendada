| 1.1.13 | docs: relatório técnico de análise de UX, ergonomia e PWA para coleta domiciliar e pontos parceiros |
# Demandas do alinhamento — organizadas por área

Registro vivo das demandas do cliente (origem: alinhamento; `docs/anotacao.txt` não é versionado).
Cada demanda é implementada em **commit separado** que documenta a demanda.
Versão interna: `VERSION`/`CHANGELOG.md` (bump a cada mudança e publicar no GitHub).
Validações de regra de negócio: **sempre no backend** (AGENTS.md §8).

## Responsabilidades

- **Backend (agente de código atual):** todas as pendências BACKEND abaixo.
- **Frontend (outro programador):** documentação dedicada em **`docs/demandas-frontend.md`** (handoff).

## 1. Visão geral

| ID | Área | Demanda | Status (04/09/2026) |
|---|---|---|---|
| D-01 | Backend ✅ | Local de coleta mais próximo no chatbot (geolocalização) | Implementada |
| D-02 | Frontend 🎨 | Publicidade de farmácias/fornecedores no perfil paciente | Pendente (definição) |
| D-03 | Backend ✅ | Ponto de coleta = entidade própria (farmácia OU laboratório) + agenda/disponibilidade | Implementada |
| D-04 | Backend ✅ | Contatos WhatsApp por perfil (BSUID Meta) | Implementada |
| F-01…F-08 | Frontend 🎨 | Telas/operações de frontend — ver handoff | Pendentes |

## 2. Backend — concluído (resumo por versão)

| Versão | Entrega backend |
|---|---|
| 1.1.0 | D-01/D-03/D-04 + geolocalização em `CollectionPoint` + guia vivo + controle de versão |
| 1.1.1–1.1.5 | Cobertura de endpoints: exames CRUD, pagamentos cancel/refund, GET /audit, contatos PATCH, revenda GET/PATCH |
| 1.1.7 | Chatbot sem gasto de tokens (`DEEPSEEK_MOCK`; protocolo CA- determinístico) |
| 1.1.9 | Auditoria por laboratório (`AuditLog.laboratory`; GET /audit escopado) |
| 1.1.10 | Agenda sem conflito (janela `APPOINTMENT_SLOT_MINUTES`, 30 min) |

## 3. Backend — pendentes (dependem de DECISÃO para finalizar)

| # | Pendência | Decisão necessária | Gate |
|---|---|---|---|
| B-01 | Gateway de pagamento real (link/sandbox/webhook) | Provedor e fluxo | G-02 |
| B-02 | Infra cloud/deploy (provedor, domínio, storage, worker) | Escolhas de infra | G-04 |
| B-03 | Provedor WhatsApp real (payload/templates/mídias; contatos D-04 prontos) | Provedor | G-05 |
| B-04 | LGPD: consentimento, retenção, exclusão/correção | Política | G-06 |
| B-05 | Validade/invalidação do orçamento pós-edição; versão aprovada | RN-ORC-004/005 implementados (v1.1.12); prazo de validade do orçamento ainda exige decisão | G-08 |
| B-06 | Reagendamento/cancelamento de agendamento | Política | G-09 |
| B-07 | Parâmetros de IA (modelo/prompt/temperatura/confiança/fallback) | Config | G-10 |
| B-08 | Origem oficial de preços; preço por região/parceiro | Origem/regra | G-01 evolução |

## 4. Frontend — documento dedicado

`docs/demandas-frontend.md` — D-02 + F-01…F-08, endpoints prontos, convenções e ambiente.

## 5. Detalhe por demanda (decisões registradas)

### D-01 — Local de coleta mais próximo (chatbot) — ✅ backend
Paciente envia localização pelo chat; chatbot devolve o **local de coleta mais próximo** com horário/estado (dúvida pré-agendamento). Ponto = farmácia OU laboratório. Resolução determinística SEM LLM (payload location ou "lat, lon"); sem localização → pede compartilhamento; sem ponto georreferenciado → humano; protocolo CA- sem IA; `DEEPSEEK_MOCK=1` valida sem tokens.

### D-03 — Ponto de coleta como entidade — ✅ backend
Ponto recebe agendamento; grade semanal de janelas; técnico designado PELO LABORATÓRIO faz check-in (abrir)/check-out (fechar); aberto/fechado controlado pelo técnico. Laboratório opcional como ponto. Entidade `CollectionPoint`; agendamento respeita disponibilidade e conflito de horário.

### D-04 — Contatos WhatsApp por perfil (BSUID Meta) — ✅ backend
Técnico/revenda: 1 contato; farmácia/laboratório: lista. `WhatsAppContact` (número, nome, `meta_bsuid` "@nome.usuario", is_main) + CRUD `/api/v1/whatsapp/contacts` (dono imutável). Base do G-05.

### D-02 — Publicidade no perfil do paciente — 🎨 FRONTEND (aguarda definição)
Exibição no perfil paciente; backend expõe fonte/regra quando definida (recomendação: parceiros = farmácias/pontos ativos do laboratório mais recente do paciente). Detalhes no doc de frontend.
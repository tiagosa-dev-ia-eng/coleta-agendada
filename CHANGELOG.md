# Changelog

Controle de versão INTERNO do projeto (REGRA GERAL: incrementar a cada mudança
e manter SEMPRE atualizado/publicado no GitHub — ver AGENTS.md e
docs/BACKEND_GUIA_IA.md).

| Versão | Data | Resumo |
|---|---|---|
| 1.1.19 | 04/09/2026 | feat(resellers-audit): gestão completa de revendedores (F-05) e trilha de auditoria e conformidade (F-06). |
| 1.1.18 | 04/09/2026 | feat(calendar-f04): calendário interativo multi-formato (semana/dia/WhatsApp) e CRUD completo de exames no laboratório (F-04). |
| 1.1.17 | 04/09/2026 | feat(laboratorio): gestão de pontos de coleta (F-02/D-03: criação, janelas e técnicos) e pagamentos (F-03: cancel/refund). |
| 1.1.16 | 04/09/2026 | feat(tecnico): gestão de pontos de coleta D-03 (abrir/fechar turno) e atalhos rápidos de campo (GPS/WhatsApp) no /tecnico (F-02). |
| 1.1.15 | 04/09/2026 | feat(pwa-ui): base PWA (manifest.ts, viewport safe-area) e ergonomia de botões 48px + ConfirmModal. |
| 1.1.14 | 04/09/2026 | feat(version): endpoint GET /api/v1/version e indicador dinâmico de versão no rodapé global (F-08). |
| 1.1.13 | 04/09/2026 | docs(ux-pwa): relatório de análise técnica de UX, ergonomia para técnicos de campo e diretrizes PWA (docs/RELATORIO_ANALISE_TECNICA_UX_PWA.md). |
| 1.1.0 | 04/09/2026 | Controle de versão interna (VERSION, scripts/bump-version.sh, targets make version-*, endpoint GET /api/v1/version). REGRA GERAL registrada: toda mudança incrementa a versão; validações de regra de negócio sempre no backend. |
| 1.0.0 | 04/09/2026 | Baseline: M0–M9, D-01 (local de coleta mais próximo), D-03 (entidade CollectionPoint: agendamento/disponibilidade/técnico/aberto-fechado), D-04 (contatos WhatsApp/BSUID) e documentação viva (até commit bdf0e94). |
| 1.1.1 | 04/09/2026 | CRUD de exames completo: retrieve, PATCH (name/active; código imutável) e DELETE soft (desativação) em /api/v1/exams/{pk} + testes. |
| 1.1.2 | 04/09/2026 | Pagamentos: POST /api/v1/payments/{id}/cancel (pendente/link) e /refund (confirmado -> REFUNDED; comissões não revertem silenciosamente) + testes. |
| 1.1.3 | 04/09/2026 | Auditoria: GET /api/v1/audit (superusuário) com filtros (action/entity_type/entity_id/user_id/start/end/limit) + testes. Escopo por laboratório: evolução (exige laboratório no AuditLog). |
| 1.1.4 | 04/09/2026 | Contatos WhatsApp: PATCH /api/v1/whatsapp/contacts/{id} (nome/número/bsuid/principal; dono imutável; escopo por perfil) + teste. |
| 1.1.5 | 04/09/2026 | Revenda: GET e PATCH /api/v1/resellers/{id} (status; laboratório) + testes. |
| 1.1.6 | 04/09/2026 | docs: guia vivo do backend — endpoints novos de cobertura (exames/pagamentos/auditoria/contatos/revenda) no §6 e histórico. |
| 1.1.7 | 04/09/2026 | Chatbot: economia de tokens — DEEPSEEK_MOCK=1 força mock mesmo com chave (validar respostas sem custo); consulta com protocolo CA- resolvida sem IA (determinística); testes (2). |
| 1.1.8 | 04/09/2026 | docs: README com referência à versão interna (VERSION/CHANGELOG/GET /api/v1/version). |
| 1.1.9 | 04/09/2026 | Auditoria escopada por laboratório: AuditLog.laboratory (migração 0002, derivação automática do usuário; explícito no WhatsApp/CollectionPoints); GET /audit — superusuário tudo, laboratório só o próprio (permissão audit.view) + testes (3). |
| 1.1.10 | 04/09/2026 | Agenda sem conflito: coleta ocupa janela padrão (APPOINTMENT_SLOT_MINUTES, default 30 min, configurável); agendamento rejeita sobreposição no mesmo ponto (farmácia/laboratório) ou com o mesmo técnico (domiciliar) + testes (2). |
| 1.1.11 | 04/09/2026 | docs: demandas reorganizadas por área — BACKEND (finaliza o agente atual) × FRONTEND (outro programador; novo docs/demandas-frontend.md com tarefas F-01…F-09 e endpoints prontos). AGENTS.md/README atualizados. |
| 1.1.12 | 04/09/2026 | Orçamentos (B-05/G-08): RN-ORC-004/005 — revisão após validação/envio cria NOVA versão (rascunho; retorna a QUOTE_DRAFT via transições novas); versão APROVADA é imutável (409). Testes +3. |
| 1.1.13 | 04/09/2026 | Gateway Pagar.me (B-01): adapter PagarMeGateway (Core v5, HTTP Basic com PAGARME_SECRET_KEY, POST {base}/orders, valores em centavos; endpoints via env) + seleção por PAYMENT_GATEWAY=pagarme + testes (3). Link/checkout e mapeamento de webhook a validar em sandbox. |
| 1.1.14 | 04/09/2026 | Provedor WhatsApp Z-PRO/Dorislabs (B-03): apps/whatsapp/gateway.py (SimulatorProvider + ZProGateway env ZPRO_BASE_URL/ZPRO_TOKEN/ZPRO_SEND_PATH) e hook de envio outbound pós-resposta (erro não derruba o pipeline). Validação dos endpoints/payload com a coleção Z-PRO pendente de credenciais. Testes (3). |
| 1.1.15 | 04/09/2026 | LGPD MVP (B-04): PatientConsent (migração 0002) + endpoints /patients/me/consent (GET/POST), /export e /anonymize (exclusão lógica, confirma DELETE) com auditoria + testes (4). Retenção/política de guarda: decisão pendente. |
| 1.1.16 | 04/09/2026 | docs: status de B-01/B-03/B-04 e histórico no guia vivo. |
| 1.1.20 | 04/09/2026 | Merge das linhas backend (1.1.13–1.1.16: Pagar.me, Z-PRO, LGPD, docs) e frontend (1.1.15–1.1.19: F-02/F-03/F-04/F-05/F-06, UX PWA). |
| 1.1.21 | 04/09/2026 | chore: ajustes de estilo (ruff) pós-merge das linhas backend/frontend. |
| 1.1.22 | 04/09/2026 | B-05: validade do orçamento final = 15 dias (QUOTATION_VALIDITY_DAYS, decisão usuário). Aprovação após expiração bloqueada (409 quote_expired); is_expired exposto na leitura. Testes +2. |

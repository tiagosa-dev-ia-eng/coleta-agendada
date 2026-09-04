# Changelog

Controle de versão INTERNO do projeto (REGRA GERAL: incrementar a cada mudança
e manter SEMPRE atualizado/publicado no GitHub — ver AGENTS.md e
docs/BACKEND_GUIA_IA.md).

| Versão | Data | Resumo |
|---|---|---|
| 1.1.0 | 04/09/2026 | Controle de versão interna (VERSION, scripts/bump-version.sh, targets make version-*, endpoint GET /api/v1/version). REGRA GERAL registrada: toda mudança incrementa a versão; validações de regra de negócio sempre no backend. |
| 1.0.0 | 04/09/2026 | Baseline: M0–M9, D-01 (local de coleta mais próximo), D-03 (entidade CollectionPoint: agendamento/disponibilidade/técnico/aberto-fechado), D-04 (contatos WhatsApp/BSUID) e documentação viva (até commit bdf0e94). |
| 1.1.1 | 04/09/2026 | CRUD de exames completo: retrieve, PATCH (name/active; código imutável) e DELETE soft (desativação) em /api/v1/exams/{pk} + testes. |
| 1.1.2 | 04/09/2026 | Pagamentos: POST /api/v1/payments/{id}/cancel (pendente/link) e /refund (confirmado -> REFUNDED; comissões não revertem silenciosamente) + testes. |
| 1.1.3 | 04/09/2026 | Auditoria: GET /api/v1/audit (superusuário) com filtros (action/entity_type/entity_id/user_id/start/end/limit) + testes. Escopo por laboratório: evolução (exige laboratório no AuditLog). |
| 1.1.4 | 04/09/2026 | Contatos WhatsApp: PATCH /api/v1/whatsapp/contacts/{id} (nome/número/bsuid/principal; dono imutável; escopo por perfil) + teste. |
| 1.1.5 | 04/09/2026 | Revenda: GET e PATCH /api/v1/resellers/{id} (status; laboratório) + testes. |
| 1.1.6 | 04/09/2026 | docs: guia vivo do backend — endpoints novos de cobertura (exames/pagamentos/auditoria/contatos/revenda) no §6 e histórico. |

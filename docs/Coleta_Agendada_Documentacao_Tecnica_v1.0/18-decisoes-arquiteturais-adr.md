# 18 — Decisões Arquiteturais (ADR)

## ADR-001 — Backend Django + DRF
**Status:** ACEITA / recuperada do material.

**Motivo registrado:** maturidade, segurança e ORM robusto.

## ADR-002 — Frontend Next.js
**Status:** ACEITA / recuperada do material.

**Motivo registrado:** performance, SEO e SSR.

## ADR-003 — PostgreSQL
**Status:** ACEITA / recuperada do material.

**Motivo registrado:** confiabilidade e índices complexos.

## ADR-004 — Redis
**Status:** ACEITA / recuperada do material.

**Motivo registrado:** performance e rate limiting.

## ADR-005 — DeepSeek
**Status:** ACEITA / recuperada do material.

**Uso:** análise/organização do orçamento e conversação inteligente.

## ADR-006 — Webhook próprio de WhatsApp
**Status:** ACEITA / recuperada do material.

**Motivo registrado:** independência de plataformas terceiras.

## ADR-007 — Human-in-the-loop para orçamento
**Status:** ACEITA / confirmada nos diagramas mais recentes.

**Decisão:** IA gera rascunho; humano valida e envia orçamento final.

## ADR-008 — Pagamento não bloqueante
**Status:** ACEITA / confirmada nos diagramas.

**Decisão:** coleta pode ser realizada sem pagamento antecipado.

## ADR-009 — Estado de domínio no backend
**Status:** PROPOSTA.

**Decisão:** frontend não pode alterar estados diretamente sem validação de regras.

## ADR-010 — Comissão baseada em regra persistida
**Status:** PROPOSTA.

**Decisão:** regras de comissão devem ser versionadas e aplicadas pelo backend.

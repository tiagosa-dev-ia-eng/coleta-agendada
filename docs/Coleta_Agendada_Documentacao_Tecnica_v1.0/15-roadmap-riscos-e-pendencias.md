# 15 — Roadmap, Riscos e Pendências

## 1. Roadmap original recuperado

| Marco | Entregável |
|---|---|
| MVP | Agendamentos, perfis, comissões, WhatsApp |
| V1.1 | Link de pagamento automático |
| V1.2 | App mobile do paciente |
| V1.3 | Integração com sistemas de laboratório |

As datas relativas originais eram +2, +4 e +6 semanas após o MVP.

## 2. Riscos principais

### R-001 — IA gerar informação incorreta
Mitigação: rascunho + validação humana.

### R-002 — Preço sem fonte de verdade
Mitigação: definir catálogo e origem do preço.

### R-003 — Comissão inconsistente
Mitigação: regra versionada e lançamento imutável.

### R-004 — Vazamento de dados
Mitigação: RBAC, auditoria, HTTPS, políticas de acesso.

### R-005 — Webhook duplicado
Mitigação: idempotência.

### R-006 — Dependência de integração externa
Mitigação: adapters e retry.

## 3. Pendências que precisam de decisão

### Produto
- reagendamento;
- cancelamento;
- validade do orçamento;
- modalidades finais de coleta;
- catálogo de exames.

### Financeiro
- gateway;
- comissão;
- estorno;
- taxas;
- conciliação.

### WhatsApp
- provedor;
- templates;
- autenticação;
- limites;
- mídias.

### IA
- modelo exato DeepSeek;
- prompt;
- temperatura;
- fallback;
- confiança mínima;
- custo máximo.

### Infra
- hospedagem;
- domínio;
- storage;
- worker;
- monitoração.

### Privacidade
- retenção;
- consentimento;
- política de acesso;
- exclusão/correção.

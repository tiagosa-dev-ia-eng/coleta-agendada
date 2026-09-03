# 16 — Guia para IA de Codificação

## Objetivo

Use este documento como instrução-base para um agente de codificação.

## Regras obrigatórias

1. Não inventar regras de negócio.
2. Quando a documentação marcar um ponto como PENDENTE, implementar apenas após confirmação.
3. Diferenciar:
   - rascunho de orçamento;
   - orçamento final.
4. Orçamento final exige validação humana.
5. Pagamento não pode impedir conclusão da coleta.
6. Estados só podem mudar através de serviços de domínio.
7. Toda transição crítica deve ser auditada.
8. Aplicar RBAC no backend.
9. Não confiar em permissões do frontend.
10. Webhooks devem ser idempotentes.
11. Comissão deve usar regra persistida e versionada.
12. Nunca permitir que a IA confirme:
    - preço sem base;
    - pagamento;
    - disponibilidade inexistente;
    - coleta realizada.

## Estrutura sugerida

```text
backend/
  apps/
    accounts/
    organizations/
    patients/
    requests/
    quotations/
    scheduling/
    payments/
    commissions/
    whatsapp/
    ai/
    audit/
```

## Padrão de serviços

Evitar colocar regras complexas diretamente em views/controllers.

Exemplo:

```text
QuotationService.generate_draft()
QuotationService.validate()
QuotationService.send()
RequestStateService.transition()
CommissionService.calculate()
PaymentService.confirm()
```

## Testes obrigatórios

Antes de considerar uma feature pronta:

- unit test;
- permission test;
- happy path;
- invalid state transition;
- audit log;
- idempotency, quando aplicável.

## Regra de segurança para IA

Sempre tratar saída do LLM como entrada não confiável.

Validar via schema antes de persistir.

# 12 — Observabilidade e Logs

## 1. Objetivo

Permitir suporte, auditoria e diagnóstico sem depender de acesso direto ao banco.

## 2. Logs de aplicação

Cada log deve conter, quando aplicável:

- timestamp;
- level;
- request_id;
- user_id;
- role;
- entity;
- entity_id;
- action;
- latency_ms;
- status_code;
- error_code.

## 3. Correlação

**PROPOSTO:** toda requisição deve receber `X-Request-ID`.

O mesmo identificador deve acompanhar:

- API;
- workers;
- chamada à IA;
- webhook;
- pagamento;
- logs.

## 4. Métricas recomendadas

### Produto
- solicitações criadas;
- orçamento enviado;
- taxa de aprovação;
- cancelamentos;
- coletas realizadas;
- tempo até orçamento;
- tempo até agendamento;
- comissão total.

### Infra
- latência API;
- taxa 4xx/5xx;
- uso de CPU;
- memória;
- conexões PostgreSQL;
- hit rate Redis;
- jobs pendentes;
- erros de webhook;
- erros da IA.

## 5. KPIs originais

O documento original define metas:

- 500+ agendamentos/mês;
- 20+ farmácias ativas;
- 50+ técnicos cadastrados;
- tempo médio de agendamento < 3 minutos;
- satisfação 4,5/5.

## 6. Alertas recomendados

- erro 5xx acima do limiar;
- webhook falhando;
- banco indisponível;
- fila crescendo;
- taxa de erro da IA;
- falha em pagamento;
- falha na geração de comissão.

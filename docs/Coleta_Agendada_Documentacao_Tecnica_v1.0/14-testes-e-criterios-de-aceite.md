# 14 — Testes e Critérios de Aceite

## 1. Testes unitários

Cobrir:

- cálculo de comissão;
- regras de estados;
- autorização RBAC;
- validação de orçamento;
- parser de IA;
- validação de webhook.

## 2. Testes de integração

### CT-INT-001
Criar solicitação → gerar rascunho → validar → enviar → aprovar.

### CT-INT-002
Garantir que rascunho não validado não seja enviado.

### CT-INT-003
Aprovar e gerar agendamento em farmácia.

### CT-INT-004
Aprovar e gerar coleta domiciliar.

### CT-INT-005
Concluir coleta com pagamento pendente.

Resultado esperado: permitido.

### CT-INT-006
Confirmar pagamento e gerar comissão.

### CT-INT-007
Cancelar orçamento.

### CT-INT-008
Receber mensagem duplicada de webhook.

Resultado esperado: não duplicar operação.

## 3. Testes RBAC

- paciente tentando acessar outro paciente → 403;
- técnico tentando ver agenda de outro técnico → 403;
- farmácia fora do escopo → 403;
- revendedor fora da rede → 403;
- laboratório conforme escopo administrativo → permitido.

## 4. Critérios de aceite da IA

A IA deve:

- extrair dados sem alterar o original;
- informar campos ausentes;
- produzir estrutura válida;
- não enviar orçamento final;
- encaminhar para humano quando necessário.

## 5. Testes de segurança

- brute force;
- JWT expirado;
- refresh revogado;
- IDOR;
- upload inválido;
- SQL injection;
- XSS;
- CORS;
- rate limiting.

## 6. Testes de carga

Metas técnicas não foram informadas no material.

Definir antes da produção:

- req/s esperado;
- usuários simultâneos;
- mensagens/minuto;
- p95 de latência;
- volume mensal.

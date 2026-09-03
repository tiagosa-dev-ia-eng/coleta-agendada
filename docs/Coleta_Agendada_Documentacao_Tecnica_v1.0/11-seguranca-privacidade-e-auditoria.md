# 11 — Segurança, Privacidade e Auditoria

## 1. Controles confirmados

O material original lista:

- JWT com refresh token;
- RBAC;
- bloqueio após 5 tentativas;
- rate limiting de 100 requisições/hora;
- HTTPS obrigatório;
- auditoria de todas as ações.

## 2. Recomendação de parametrização

Os valores abaixo devem ser configuráveis:

```text
MAX_LOGIN_ATTEMPTS=5
RATE_LIMIT_PER_HOUR=100
```

## 3. Controles propostos

- senha com hash robusto;
- rotação de refresh token;
- revogação de sessão;
- MFA para perfis administrativos;
- headers de segurança;
- CORS restritivo;
- proteção CSRF quando aplicável;
- validação de upload;
- antivírus/scan de anexos;
- criptografia de backups;
- segregação de ambientes;
- secrets fora do repositório;
- trilha de auditoria imutável para eventos críticos.

## 4. Dados sensíveis

O sistema lida com:

- identificação de pacientes;
- pedido médico;
- exames;
- histórico de solicitação.

Por isso é recomendável realizar revisão de privacidade/LGPD antes da produção.

**Status:** recomendação técnica/jurídica; o material original não define uma política de privacidade.

## 5. Auditoria mínima

Registrar:

- login;
- falha de login;
- bloqueio;
- criação/edição de usuário;
- alteração de permissão;
- leitura/download de pedido médico quando necessário;
- criação/edição/validação/envio de orçamento;
- aprovação;
- cancelamento;
- check-in/out;
- conclusão da coleta;
- pagamento;
- comissão;
- alterações de regra de comissão.

## 6. Retenção

Política de retenção e descarte de dados está **PENDENTE**.

# 13 — Infraestrutura e Deploy

## 1. Limitação

A infraestrutura original de produção não consta no material recuperado.

O desenho abaixo é uma referência **PROPOSTA**.

## 2. Componentes

```text
Internet
   │
   ▼
Reverse Proxy / TLS
   │
   ├── Next.js
   │
   └── Django/DRF
          │
          ├── PostgreSQL
          ├── Redis
          ├── Worker assíncrono
          ├── DeepSeek API
          └── WhatsApp Webhook
```

## 3. Ambientes

Recomendado:

- development;
- staging;
- production.

## 4. Variáveis

```text
DJANGO_SECRET_KEY=
DATABASE_URL=
REDIS_URL=
DEEPSEEK_API_KEY=
WHATSAPP_WEBHOOK_SECRET=
WHATSAPP_ACCESS_TOKEN=
FRONTEND_URL=
BACKEND_URL=
ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=
```

Nomes exatos são PROPOSTOS.

## 5. Worker

**PROPOSTO:** usar processamento assíncrono para:

- IA;
- envio de mensagens;
- notificações;
- processamento de anexos;
- cálculos demorados;
- tarefas de conciliação.

Tecnologia do worker está PENDENTE.

## 6. Backup

Recomendado:

- backup diário PostgreSQL;
- retenção definida;
- teste de restore;
- cópia fora do host primário;
- anexos com backup separado.

## 7. CI/CD

Pipeline recomendado:

1. lint;
2. testes;
3. build;
4. scan de dependências;
5. migrations check;
6. deploy staging;
7. smoke test;
8. deploy produção;
9. health check.

## 8. Health endpoints

```http
GET /health
GET /ready
```

## 9. Pendências

- Docker ou não;
- provedor cloud;
- balanceamento;
- CDN;
- object storage;
- domínio;
- SLA;
- RPO/RTO;
- estratégia de migrations.

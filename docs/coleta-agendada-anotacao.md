### O que já conseguimos recuperar

A arquitetura conceitual pode ser reconstruída inicialmente assim:

```text
                        COLETA AGENDADA
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
       Web App           WhatsApp + IA        Backoffice
          │                   │                   │
          └─────────────── API REST ──────────────┘
                              │
                         Django + DRF
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         PostgreSQL         Redis          DeepSeek
              │               │               │
          Dados/RBAC     Cache/limites    Interpretação
                                         e rascunhos
```

O documento original confirma que a plataforma conecta **laboratórios, revendedores, farmácias, técnicos e pacientes**, oferecendo acesso pelo Web App e também por WhatsApp + IA. 

### Perfis do sistema

Podemos reconstruir cinco perfis principais:

| Perfil                    | Responsabilidade                                                         |
| ------------------------- | ------------------------------------------------------------------------ |
| **Laboratório**           | Administração geral, acompanhamento das coletas, dashboards e relatórios |
| **Revendedor**            | Cadastro/indicação de farmácias e técnicos, acompanhamento e comissões   |
| **Farmácia**              | Ponto físico de coleta, agenda, acompanhamento e comissões               |
| **Técnico de enfermagem** | Coleta domiciliar/presencial, agenda, check-in/check-out e comissão      |
| **Paciente**              | Solicitação, orçamento, aprovação e acompanhamento                       |

O material original já previa permissões distintas para os cinco perfis por meio de **RBAC**. 

---

## Fluxo funcional que considero hoje o mais correto

Combinando o PDF com os diagramas mais recentes que você anexou, eu documentaria o fluxo principal assim:

```text
INÍCIO
  │
  ▼
SOLICITADO
Paciente cria uma solicitação
  │
  ▼
RASCUNHO DO ORÇAMENTO
IA interpreta:
- pedido médico
- exames
- local
- data
- informações do paciente
- possíveis valores

IMPORTANTE:
Rascunho ainda NÃO é enviado ao paciente
  │
  ▼
VALIDAÇÃO HUMANA
Atendente confere:
- exames
- valores
- condições
- disponibilidade
  │
  ▼
ORÇAMENTO FINAL ENVIADO
Atendente envia ao paciente
  │
  ├──────────────────────► CANCELADO
  │
  ▼
APROVADO
  │
  ├──────────────┬───────────────┐
  ▼              ▼               ▼
Farmácia       Domiciliar     Laboratório
  │              │               │
  └──────────────┴───────────────┘
                 │
                 ▼
         AGENDAMENTO CONFIRMADO
                 │
                 ▼
             REALIZADO
        Técnico conclui coleta
                 │
                 ▼
            PAGAMENTO
                 │
                 ▼
            COMISSÕES
```

Essa versão é particularmente importante porque estabelece uma regra de negócio:

> **A IA pode montar o rascunho, mas não deve determinar e enviar autonomamente o orçamento final.**

Isso está coerente com o material mais novo das apresentações.

O PDF anterior descrevia o fluxo geral como **Solicitação → Orçamento → Aprovação → Coleta → Comissão** e já indicava que o pagamento poderia ocorrer no orçamento ou presencialmente. 

---

## WhatsApp + IA

Outro módulo que conseguimos reconstruir quase completamente é o atendimento conversacional:

```text
Paciente
   │
   ▼
WhatsApp
   │
   ▼
Webhook Coleta Agendada
   │
   ▼
Backend
   │
   ├── identifica usuário/conversa
   ├── interpreta mensagem
   ├── recebe documentos
   └── consulta estado da solicitação
             │
             ▼
          DeepSeek
             │
     ┌───────┼────────┐
     │       │        │
 intenção  dados   organização
     │       │        │
     └───────┼────────┘
             ▼
      Solicitação/Rascunho
             │
             ▼
      Validação humana
```

O objetivo da IA seria principalmente:

* identificar a intenção;
* conduzir o diálogo;
* extrair informações estruturadas;
* interpretar informações do pedido médico;
* organizar a solicitação;
* ajudar a montar o rascunho do orçamento;
* consultar status;
* responder perguntas operacionais.

E não:

* aprovar preços autonomamente;
* enviar orçamento final sem validação;
* concluir coleta;
* confirmar manualmente informações que dependam de um operador.

A documentação original define o **DeepSeek** justamente para análise de orçamento e conversação inteligente. 

---

# Arquitetura técnica inicial

Eu sugiro reconstruirmos o projeto em módulos:

```text
coleta-agendada/
│
├── backend/
│   ├── accounts/
│   ├── patients/
│   ├── laboratories/
│   ├── pharmacies/
│   ├── technicians/
│   ├── resellers/
│   ├── scheduling/
│   ├── quotations/
│   ├── payments/
│   ├── commissions/
│   ├── whatsapp/
│   ├── ai/
│   ├── notifications/
│   ├── audit/
│   └── core/
│
├── frontend/
│   ├── paciente/
│   ├── farmacia/
│   ├── tecnico/
│   ├── revendedor/
│   └── laboratorio/
│
└── docs/
    ├── arquitetura.md
    ├── regras-de-negocio.md
    ├── perfis-e-permissoes.md
    ├── fluxo-agendamento.md
    ├── modelo-de-dados.md
    ├── api.md
    ├── whatsapp.md
    ├── inteligencia-artificial.md
    ├── comissoes.md
    ├── seguranca.md
    └── deploy.md
```

## Banco de dados

Pelas funcionalidades recuperadas, o modelo provavelmente precisará pelo menos destas entidades:

```text
User
Role
Permission

Patient
Laboratory
Reseller
Pharmacy
Technician

CollectionRequest
MedicalOrder
MedicalOrderItem / Exam

Quotation
QuotationItem
QuotationRevision

Appointment
AppointmentStatusHistory

Payment

Commission
CommissionRule

WhatsAppConversation
WhatsAppMessage

Attachment

AuditLog
```

E eu acrescentaria entidades intermediárias onde necessário para manter as relações N:N.

---

# Máquina de estados

Essa provavelmente será uma das partes mais importantes da documentação.

```text
DRAFT
   ↓
REQUESTED
   ↓
QUOTE_DRAFT
   ↓
WAITING_HUMAN_VALIDATION
   ↓
QUOTE_SENT
   ├──────────→ CANCELED
   ↓
APPROVED
   ↓
SCHEDULED
   ↓
IN_PROGRESS
   ↓
COMPLETED
   ↓
PAYMENT_CONFIRMED
   ↓
COMMISSION_GENERATED
```

Uma observação importante dos seus diagramas:

```text
COMPLETED
   │
   └── não depende obrigatoriamente de PAYMENT_CONFIRMED
```

Ou seja:

> **o pagamento não deve bloquear a realização da coleta.**

Isso precisa virar uma regra explícita de domínio.

---

# Comissões

O sistema possui pelo menos dois mecanismos:

### Percentual

```text
Orçamento: R$ 100,00

Farmácia:
10% → R$ 10,00

Técnico:
15% → R$ 15,00
```

### Valor fixo

```text
Farmácia:
R$ 15,00 / coleta

Técnico:
R$ 25,00 / coleta

Revendedor:
R$ 5,00 / agendamento
```

O PDF original confirma os dois modelos e esses exemplos de valores. 

Eu criaria tecnicamente algo como:

```text
CommissionRule

id
beneficiary_type
beneficiary_id

calculation_type:
    PERCENTAGE
    FIXED

value

trigger:
    PAYMENT_CONFIRMED
    COLLECTION_COMPLETED

active
valid_from
valid_until
```

Isso evita colocar regras financeiras fixas no código.

---

# Segurança

Já temos um bom ponto de partida recuperado:

```text
Autenticação
├── JWT Access Token
└── JWT Refresh Token

Autorização
└── RBAC
    ├── Laboratório
    ├── Revendedor
    ├── Farmácia
    ├── Técnico
    └── Paciente

Proteções
├── HTTPS
├── Rate Limiting
├── Bloqueio após tentativas inválidas
└── Audit Log
```

O documento anterior especificava inclusive **bloqueio após 5 tentativas**, **100 requisições/hora**, HTTPS obrigatório e auditoria das ações. 

Esses valores eu marcaria inicialmente como **configuráveis**, em vez de hard-coded.

---

## Há também alguns pontos que precisamos reconstruir

Os materiais enviados não esclarecem totalmente, por exemplo:

* modelo exato das tabelas;
* endpoints REST;
* regra completa de cálculo do orçamento;
* como preços de exames são cadastrados;
* relacionamento laboratório × farmácia;
* relacionamento revendedor × farmácia;
* regras de disponibilidade do técnico;
* definição de região/CEP para coleta domiciliar;
* provedor do WhatsApp;
* armazenamento de pedido médico;
* gateway de pagamento;
* política de cancelamento;
* política de reagendamento;
* quando exatamente a comissão se torna devida;
* regras para estorno;
* infraestrutura/deploy.

Nesses pontos, não precisamos inventar. Podemos reconstruí-los juntos e marcar no documento:

```text
[DEFINIDO]
[INFERIDO PELO FLUXO]
[PENDENTE DE DEFINIÇÃO]
```

Isso é muito útil para não misturarmos decisões antigas com novas.

### Minha sugestão de próximo passo

Eu reconstruiria agora um documento principal chamado:

**`DOCUMENTACAO_TECNICA_COLETA_AGENDADA_v1.0.md`**

com aproximadamente esta estrutura:

```text
1. Visão do produto
2. Objetivos
3. Arquitetura
4. Stack tecnológica
5. Perfis e RBAC
6. Modelo de domínio
7. Modelo de dados
8. Fluxo de agendamento
9. Máquina de estados
10. Orçamentos
11. Validação humana
12. IA / DeepSeek
13. WhatsApp
14. Farmácias
15. Técnicos
16. Laboratórios
17. Revendedores
18. Pacientes
19. Pagamentos
20. Comissões
21. Notificações
22. API REST
23. Auditoria
24. Segurança
25. Logs e observabilidade
26. Infraestrutura
27. Regras de negócio
28. Casos de erro
29. Roadmap
30. Pendências de definição
```


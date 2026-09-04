# 07 — API REST

## 1. Status

Os endpoints originais não estavam presentes no material recuperado.  
Esta especificação é **PROPOSTA**.

Base sugerida:

```text
/api/v1/
```

## 2. Autenticação

```http
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

## 3. Solicitações

```http
POST /api/v1/requests
GET  /api/v1/requests
GET  /api/v1/requests/{id}
PATCH /api/v1/requests/{id}
POST /api/v1/requests/{id}/cancel
GET  /api/v1/requests/{id}/history
```

## 4. Pedido médico

```http
POST /api/v1/requests/{id}/medical-orders
GET  /api/v1/requests/{id}/medical-orders
```

## 5. Orçamentos

```http
POST /api/v1/requests/{id}/quotation-draft
GET  /api/v1/requests/{id}/quotations
GET  /api/v1/quotations/{id}
POST /api/v1/quotations/{id}/validate
POST /api/v1/quotations/{id}/send
POST /api/v1/quotations/{id}/approve
POST /api/v1/quotations/{id}/reject
```

### Regra
`/send` deve rejeitar orçamento que não possua validação humana.

## 6. Agendamento

```http
POST /api/v1/requests/{id}/appointments
GET  /api/v1/appointments
GET  /api/v1/appointments/{id}
POST /api/v1/appointments/{id}/check-in
POST /api/v1/appointments/{id}/check-out
POST /api/v1/appointments/{id}/complete
POST /api/v1/appointments/{id}/reschedule
```

`reschedule` é PROPOSTO e necessita confirmação funcional.

## 7. Pagamentos

```http
POST /api/v1/requests/{id}/payments/link
POST /api/v1/payments/webhook
GET  /api/v1/requests/{id}/payments
POST /api/v1/payments/{id}/confirm
```

## 8. Comissões

```http
GET  /api/v1/commission-rules
POST /api/v1/commission-rules
PATCH /api/v1/commission-rules/{id}

GET  /api/v1/commissions
GET  /api/v1/commissions/{id}
POST /api/v1/commissions/{id}/mark-paid
```

## 9. Cadastros

```http
/api/v1/laboratories
/api/v1/resellers
/api/v1/pharmacies
/api/v1/technicians
/api/v1/patients
```

**Locais de coleta (D-01):** `Laboratory` e `Pharmacy` aceitam (GET/POST/PATCH)
`address`, `city`, `state`, `zip_code`, `latitude` e `longitude` — dados usados
pelo chatbot para indicar o local de coleta mais próximo (ver §10).

## 10. WhatsApp

```http
POST /api/v1/webhooks/whatsapp
GET  /api/v1/whatsapp/conversations
GET  /api/v1/whatsapp/conversations/by-phone/{phone}
DELETE /api/v1/whatsapp/conversations/by-phone/{phone}   // limpa memória (homologação)
```

**Localização (D-01):** `POST /webhooks/whatsapp` aceita, além de `body`,
um objeto `location` (`{"latitude": ..., "longitude": ...}`, como o WhatsApp
envia) ou texto com o par "lat, lon". Com localização válida, o pipeline
responde o **local de coleta mais próximo** (farmácia ou laboratório) de forma
determinística — ver `docs/demandas.md` D-01 e `docs/BACKEND_GUIA_IA.md`.

## 11. Padrão de erro

```json
{
  "error": {
    "code": "QUOTE_NOT_VALIDATED",
    "message": "O orçamento final precisa de validação humana antes do envio.",
    "details": {}
  }
}
```

## 12. Idempotência

**PROPOSTO:** operações de webhook, pagamento e criação de eventos críticos devem aceitar chave de idempotência.

## 13. Locais de coleta e contatos WhatsApp (D-03/D-04)

### Locais de coleta (D-03) — base `/api/v1/collection-points`

```http
POST   /api/v1/collection-points                 # criar (laboratório/revendedor)
GET    /api/v1/collection-points                 # lista escopada por perfil
GET    /api/v1/collection-points/{id}
PATCH  /api/v1/collection-points/{id}
POST   /api/v1/collection-points/{id}/windows            # janela (weekday, open_time, close_time)
DELETE /api/v1/collection-points/{id}/windows/{window_id}
POST   /api/v1/collection-points/{id}/technicians        # {technician_id} — somente laboratório
DELETE /api/v1/collection-points/{id}/technicians/{tech_id}
POST   /api/v1/collection-points/{id}/open               # check-in do técnico designado (abre)
POST   /api/v1/collection-points/{id}/close              # check-out do técnico designado (fecha)
```

Ponto de coleta: kind `pharmacy` (exige pharmacy_id da rede) ou
`laboratory`; cada farmácia/laboratório pode ou não ser ponto. Localização/
coordenadas pertencem ao ponto. Agendamento em ponto exige ponto ativo e
disponibilidade (janela semanal e ponto não fechado hoje).

### Contatos WhatsApp (D-04) — base `/api/v1/whatsapp/contacts`

```http
POST   /api/v1/whatsapp/contacts                 # dono: pharmacy|laboratory|technician|reseller
GET    /api/v1/whatsapp/contacts
GET    /api/v1/whatsapp/contacts/{id}
DELETE /api/v1/whatsapp/contacts/{id}
```

Técnico e revenda: 1 contato; farmácia e laboratório: lista. Campos:
`number` (normalizado), `name`, `meta_bsuid` ("@nome.usuario").

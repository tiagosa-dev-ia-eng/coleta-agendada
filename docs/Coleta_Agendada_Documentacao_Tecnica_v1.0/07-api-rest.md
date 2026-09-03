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

## 10. WhatsApp

```http
POST /api/v1/webhooks/whatsapp
GET  /api/v1/whatsapp/conversations
GET  /api/v1/whatsapp/conversations/{id}
GET  /api/v1/whatsapp/conversations/{id}/messages
```

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

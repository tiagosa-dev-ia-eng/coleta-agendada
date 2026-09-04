# DOCUMENTAÇÃO TÉCNICA — COLETA AGENDADA v1.0

## 1. Resumo executivo

O Coleta Agendada é uma plataforma para digitalizar o processo de solicitação e realização de coletas de exames. Conecta laboratórios, revendedores, farmácias, técnicos e pacientes, com atendimento por Web App e WhatsApp + IA.

A arquitetura recuperada utiliza Django + DRF, Next.js, PostgreSQL, Redis, DeepSeek e webhook próprio para WhatsApp.

## 2. Princípios centrais

1. Um único processo digital do pedido à realização.
2. IA acelera o atendimento, mas não substitui a validação humana do orçamento.
3. Perfis distintos possuem acessos e funcionalidades próprias.
4. Pagamento é flexível e não bloqueia a coleta.
5. Comissões podem ser percentuais ou fixas.
6. Todas as transições críticas devem ser controladas pelo backend.

## 3. Perfis

- Laboratório
- Revendedor
- Farmácia
- Técnico de enfermagem
- Paciente

## 4. Fluxo principal

```text
Solicitado
  ↓
Rascunho do orçamento
  ↓
Validação humana
  ↓
Orçamento final enviado
  ↓
Aprovado ──────→ Cancelado
  ↓
Agendado
  ↓
Realizado
  ↓
Pagamento / Conciliação
  ↓
Comissões
```

## 5. Stack

| Componente | Tecnologia |
|---|---|
| Backend | Django + DRF |
| Frontend | Next.js |
| Banco | PostgreSQL |
| Cache | Redis |
| IA | DeepSeek |
| WhatsApp | Webhook próprio |
| Auth | JWT + refresh token |
| Autorização | RBAC |

## 6. Regras críticas

### Orçamento
A IA gera somente o rascunho. Um atendente revisa e envia o orçamento final.

### Pagamento
Pagamento antecipado é opcional. Pode existir pagamento presencial.

### Coleta
A realização não deve ser bloqueada por pagamento pendente.

### Comissão
Suporta percentual ou valor fixo.

### Segurança
JWT, RBAC, bloqueio de login, rate limiting, HTTPS e auditoria estão registrados no material original.

## 7. Dados principais

- usuários;
- pacientes;
- laboratórios;
- revendedores;
- farmácias;
- técnicos;
- solicitações;
- pedidos médicos;
- exames;
- orçamentos;
- agendamentos;
- pagamentos;
- comissões;
- conversas WhatsApp;
- auditoria.

## 8. API

A documentação detalhada de endpoints está em `07-api-rest.md`.  
Os endpoints são uma proposta de reconstrução, porque o contrato original da API não foi recuperado.

## 9. Inteligência Artificial

A IA deve:

- identificar intenção;
- extrair dados;
- organizar solicitação;
- estruturar o rascunho.

A IA não deve:

- enviar orçamento final;
- inventar preços;
- confirmar pagamento;
- marcar coleta como realizada.

## 10. Segurança e privacidade

O sistema manipula dados de pacientes e pedidos médicos. Além dos controles técnicos já previstos, recomenda-se análise formal de privacidade/LGPD antes da produção.

## 11. Testes

O fluxo mínimo de aceite é:

```text
criar solicitação
→ gerar rascunho
→ validar por humano
→ enviar orçamento
→ aprovar
→ agendar
→ realizar
→ registrar pagamento
→ gerar comissão
```

Deve existir teste específico garantindo que orçamento não validado não possa ser enviado.

## 12. Pendências

Ainda precisam ser confirmados:

- catálogo e fonte de preços;
- política de reagendamento;
- política de cancelamento;
- gateway de pagamento;
- provedor e payload do WhatsApp;
- regras de estorno;
- infraestrutura de produção;
- retenção de dados;
- regras finais de comissão;
- integração com laboratórios.

## 13. Documentos complementares

Este arquivo é um consolidado. O pacote inclui documentos separados para requisitos, arquitetura, RBAC, fluxo, banco, API, IA, comissões, segurança, observabilidade, deploy, testes, backlog e ADRs.


---

# Adendo v1.1 — Demandas do alinhamento (04/09/2026)

Este adendo registra as decisões posteriores ao pacote original (docs 01–18). O
registro vivo completo fica em `docs/demandas.md` (raiz do projeto).

## D-01 — Local de coleta mais próximo (implementado)

- Ponto de coleta pode ser **uma farmácia ou um laboratório** (decisão do usuário).
- O paciente envia a localização pelo chat (WhatsApp + IA); o chatbot devolve o
  local de coleta mais próximo, identificando o tipo ("é a farmácia X…" / "é o
  laboratório Y…"), com endereço e distância aproximada.
- Candidatos: laboratório do canal + farmácias ativas da rede, ambos com
  latitude/longitude cadastradas (novos campos em Laboratory e Pharmacy);
  distância Haversine, resolução determinística SEM LLM.
- Sem localização válida → chatbot pede o compartilhamento; sem ponto
  georreferenciado → encaminha a humano.

## D-02 — Publicidade de farmácias/fornecedores no perfil do paciente

PENDENTE — aguarda definição de conteúdo/fonte/regra de exibição.

> Guia vivo do backend para outras IAs de codificação: `docs/BACKEND_GUIA_IA.md`.

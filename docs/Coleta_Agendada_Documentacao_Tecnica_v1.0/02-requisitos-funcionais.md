# 02 — Requisitos Funcionais

## Convenção

- RF = requisito funcional.
- Prioridade P0 = obrigatório para operação básica.
- Prioridade P1 = importante.
- Prioridade P2 = evolução.

## Solicitações

### RF-001 — Criar solicitação
O paciente deve poder criar uma solicitação de coleta.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-002 — Informar dados da coleta
A solicitação deve suportar, no mínimo:

- dados do paciente;
- pedido médico;
- local desejado;
- data/período desejado.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-003 — Anexar pedido médico
A plataforma deve permitir o envio do pedido médico no processo.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-004 — Criar rascunho de orçamento
A IA deve organizar exames e informações para formar um rascunho.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-005 — Impedir envio automático do rascunho
O rascunho gerado pela IA não deve ser enviado ao paciente como orçamento final.

**Prioridade:** P0  
**Status:** CONFIRMADO pelos diagramas mais recentes.

### RF-006 — Validação humana
Um atendente deve revisar exames, valores e condições antes do envio do orçamento.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-007 — Enviar orçamento final
Somente após validação humana o orçamento final deve ser enviado.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-008 — Aprovar orçamento
O paciente deve poder aprovar o orçamento.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-009 — Cancelar solicitação
A solicitação/orçamento pode seguir para o estado cancelado.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-010 — Definir modalidade/local
Após aprovação, o processo deve suportar:

- farmácia/ponto de coleta;
- domiciliar;
- laboratório/unidade laboratorial.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-011 — Confirmar agendamento
A plataforma deve gerar confirmação contendo protocolo, data, horário e local.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-012 — Registrar realização da coleta
O técnico deve poder concluir a coleta.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-013 — Check-in/check-out
O perfil técnico deve possuir mecanismo de check-in e check-out.

**Prioridade:** P1  
**Status:** CONFIRMADO no material original.

## Pagamentos

### RF-014 — Pagamento opcional antecipado
A plataforma deve suportar link de pagamento opcional.

**Prioridade:** P1  
**Status:** CONFIRMADO.

### RF-015 — Pagamento na coleta
A plataforma deve suportar pagamento presencial.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-016 — Não bloquear realização por falta de pagamento
O pagamento não deve bloquear a realização da coleta.

**Prioridade:** P0  
**Status:** CONFIRMADO pelos diagramas.

## Comissões

### RF-017 — Comissão percentual
Permitir regra de comissão por percentual.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-018 — Comissão fixa
Permitir regra de comissão com valor fixo por coleta/agendamento.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-019 — Perfis com comissão
O material mostra comissões para farmácia, técnico e revendedor.

**Prioridade:** P0  
**Status:** CONFIRMADO.

## WhatsApp

### RF-020 — Conversação via WhatsApp
O paciente deve conseguir solicitar coleta via WhatsApp.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-021 — Interpretação por IA
A IA deve:

- identificar intenção;
- extrair informações;
- organizar a solicitação.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-022 — Registrar protocolo
O atendimento deve gerar registro/protocolo de solicitação.

**Prioridade:** P0  
**Status:** CONFIRMADO.

## Administração

### RF-023 — Gestão de farmácias
Laboratório/revendedor devem possuir funções de gestão/cadastro conforme permissão.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-024 — Gestão de técnicos
Laboratório/revendedor devem possuir funções de gestão/cadastro conforme permissão.

**Prioridade:** P0  
**Status:** CONFIRMADO.

### RF-025 — Dashboard
Laboratório deve possuir dashboard geral.

**Prioridade:** P1  
**Status:** CONFIRMADO.

### RF-026 — Relatórios
Laboratório deve possuir relatórios financeiros e de comissões.

**Prioridade:** P1  
**Status:** CONFIRMADO.

## Demandas do alinhamento com o cliente (registro vivo: `docs/demandas.md`)

### D-01 — Devolver o local de coleta mais próximo (chatbot)
Quando o paciente envia a localização pelo chat (WhatsApp + IA), o chatbot
devolve o **local de coleta mais próximo**. **Ponto de coleta pode ser:
uma farmácia ou um laboratório** (decisão do usuário, 04/09/2026).

**Status:** CONFIRMADO (implementado 04/09/2026; regras e detalhes em
`docs/demandas.md` D-01 e no `docs/BACKEND_GUIA_IA.md`). A implementação
resolve de forma determinística (sem LLM) entre o laboratório do canal e as
farmácias ativas da rede com coordenadas cadastradas (Haversine).

### D-02 — Publicidade de farmácias/fornecedores no perfil do paciente
Ainda sem definição de conteúdo/fonte/regra de exibição.

**Status:** PENDENTE.

## Requisitos ainda sem definição suficiente

- política de reagendamento;
- política de cancelamento;
- prazo de validade do orçamento;
- regra para devolução/estorno;
- catálogo de exames;
- origem oficial dos preços;
- disponibilidade de agenda;
- notificações por e-mail/SMS;
- política de anexos.

**Status:** PENDENTE.
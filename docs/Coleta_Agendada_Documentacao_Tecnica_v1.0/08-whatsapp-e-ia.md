# 08 — WhatsApp e IA

## 1. Objetivo

Permitir que o paciente realize o processo inicial de solicitação pelo WhatsApp, utilizando linguagem natural.

## 2. Fluxo confirmado

```text
Mensagem do paciente
        ↓
WhatsApp
        ↓
Backend / webhook
        ↓
DeepSeek
        ↓
Identificação da intenção
Extração de informações
Organização da solicitação
        ↓
Registro no Coleta Agendada
        ↓
Validação humana do orçamento
```

## 3. Responsabilidades permitidas à IA

- identificar intenção;
- extrair dados da conversa;
- organizar informações;
- identificar informações faltantes;
- auxiliar leitura lógica do pedido;
- estruturar exames;
- sugerir rascunho de valores quando houver base confiável;
- criar rascunho;
- responder sobre andamento quando houver dados no sistema.

## 4. Responsabilidades proibidas ou condicionadas

A IA não deve:

- enviar orçamento final sem validação humana;
- confirmar preço sem fonte válida;
- inventar exame;
- inventar disponibilidade;
- concluir coleta;
- confirmar pagamento sem evento do financeiro;
- gerar comissão fora das regras registradas.

## 5. Estrutura sugerida da saída da IA

```json
{
  "intent": "create_collection_request",
  "confidence": 0.97,
  "patient_data": {},
  "collection": {
    "mode": "pharmacy",
    "desired_date": "2026-09-15",
    "desired_period": "morning",
    "preferred_location": "Farmácia Saúde"
  },
  "medical_order": {
    "received": true
  },
  "missing_fields": [],
  "requires_human": false
}
```

## 5.1 Local de coleta mais próximo (D-01 — implementado 04/09/2026)

Quando o paciente **compartilha a localização** (payload `location` com
`latitude`/`longitude`, como o WhatsApp envia, ou texto "lat, lon"), o
pipeline resolve o **local de coleta mais próximo de forma determinística
(SEM chamada de LLM)**: candidatos = laboratório do canal (com coordenadas)
e farmácias ativas da rede com coordenadas; vence o de menor distância
(Haversine). A resposta identifica o tipo ("é a farmácia X…" / "é o
laboratório Y…"), endereço e distância aproximada.

- Sem localização válida: o chatbot **pede o compartilhamento**.
- Sem ponto georreferenciado na rede: **encaminha a humano** (não inventa local).
- Pergunta "qual o local de coleta mais próximo?" sem localização: pede o
  compartilhamento (não escala a humano).

Detalhes e regras: `docs/demandas.md` D-01 + `docs/BACKEND_GUIA_IA.md`.

## 6. Regra de confiança

**PROPOSTO:** qualquer extração que possa alterar preço, exame ou agenda deve permitir encaminhamento para validação humana quando a confiança for baixa.

## 7. Persistência

Guardar:

- mensagem recebida;
- resposta enviada;
- interpretação da IA;
- versão/modelo utilizado;
- timestamps;
- request relacionado;
- erro, quando houver.

## 8. Webhook

O documento original indica **webhook próprio** para WhatsApp.

O provedor exato, formato do payload e mecanismo de autenticação do webhook permanecem **PENDENTES**.
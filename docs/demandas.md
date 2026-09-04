# Demandas do alinhamento

Registro das demandas levantadas no alinhamento com o cliente
(fonte original: anotação local `docs/anotacao.txt`, não versionada).
Cada demanda é implementada em **commit separado** que documenta a demanda atendida.

| ID | Demanda | Fonte documental | Status |
|---|---|---|---|
| D-01 | Mandar localização para farmácia/laboratório (local de coleta) mais próxima | Alinhamento com cliente; toca item PENDENTE "geolocalização" (doc 02) | Implementada (04/09/2026) — chatbot devolve a farmácia mais próxima |
| D-02 | No perfil paciente, mostrar publicidade das farmácias ou fornecedores | Alinhamento com cliente | Aguardando definição de regra de domínio |

## D-01 — Mandar localização para farmácia/laboratório (local de coleta) mais próxima

Texto original: *"Mandar localização para farmacia/laboratior (local de coleta) mas proxima"*.

Contexto no sistema atual:

- Nenhuma geolocalização implementada (item PENDENTE no doc 02).
- `organizations.Pharmacy` tem `address`, `city`, `state`, `zip_code` (texto) — sem coordenadas.
- `patients.Patient` não possui endereço/localização.
- `requests.CollectionRequest.preferred_location` e `scheduling.Appointment.location_label` são texto livre.

### Perguntas de domínio (respondidas pelo usuário — 04/09/2026)

- **Fluxo:** o paciente manda a localização e **o chatbot devolve a farmácia
  mais próxima** (resposta direta no chat; interação pelo canal WhatsApp + IA /
  simulador do M8).
- **Cálculo de "mais próxima":** farmácias **ativas da rede do laboratório do
  canal** ("conv.laboratory") com latitude/longitude cadastradas; distância
  Haversine (km). Cadastro das coordenadas via API/admin/"Pharmacy.latitude"
  e "Pharmacy.longitude" (novos campos). CEP como fallback/geocodificação:
  evolução futura.

### Regra implementada

1. O webhook aceita mensagem de **localização estruturada**
   ("location": {"latitude": ..., "longitude": ...} — como o WhatsApp envia)
   ou texto com par "lat, lon".
2. Com localização válida, o pipeline resolve a farmácia mais próxima de forma
   **determinística (sem LLM)** — sem custo e sem risco de alucinação.
3. Paciente pergunta pela farmácia mais próxima **sem enviar localização**:
   o chatbot pede para compartilhar a localização (não escala a humano).
4. Sem farmácia georreferenciada na rede: **encaminha a humano** (não inventa
   ponto de coleta — AGENTS.md regras 1 e 10).
5. Frontend: simulador ganhou envio de localização (demo) e sugestão de
   pergunta. Cadastro de coordenadas na tela de farmácias: evolução (hoje API).

## D-02 — Publicidade das farmácias ou fornecedores no perfil do paciente

Texto original: *"No perfil paciente mostrar publicidade das farmacaias ou fornecedores"*.

Contexto no sistema atual:

- Perfil paciente existe no backend (`patients.Patient`) e na área web do frontend.
- Não há modelo de anúncio/publicidade nem fornecedores cadastrados como entidade.

### Perguntas de domínio (respondidas pelo usuário)

- (preencher conforme decisão)

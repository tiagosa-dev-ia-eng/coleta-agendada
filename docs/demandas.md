# Demandas do alinhamento

Registro das demandas levantadas no alinhamento com o cliente
(fonte original: anotação local `docs/anotacao.txt`, não versionada).
Cada demanda é implementada em **commit separado** que documenta a demanda atendida.

| ID | Demanda | Fonte documental | Status |
|---|---|---|---|
| D-01 | Mandar localização para farmácia/laboratório (local de coleta) mais próxima | Alinhamento com cliente; toca item PENDENTE "geolocalização" (doc 02) | Aguardando definição de regra de domínio |
| D-02 | No perfil paciente, mostrar publicidade das farmácias ou fornecedores | Alinhamento com cliente | Aguardando definição de regra de domínio |

## D-01 — Mandar localização para farmácia/laboratório (local de coleta) mais próxima

Texto original: *"Mandar localização para farmacia/laboratior (local de coleta) mas proxima"*.

Contexto no sistema atual:

- Nenhuma geolocalização implementada (item PENDENTE no doc 02).
- `organizations.Pharmacy` tem `address`, `city`, `state`, `zip_code` (texto) — sem coordenadas.
- `patients.Patient` não possui endereço/localização.
- `requests.CollectionRequest.preferred_location` e `scheduling.Appointment.location_label` são texto livre.

### Perguntas de domínio (respondidas pelo usuário)

- (preencher conforme decisão)

## D-02 — Publicidade das farmácias ou fornecedores no perfil do paciente

Texto original: *"No perfil paciente mostrar publicidade das farmacaias ou fornecedores"*.

Contexto no sistema atual:

- Perfil paciente existe no backend (`patients.Patient`) e na área web do frontend.
- Não há modelo de anúncio/publicidade nem fornecedores cadastrados como entidade.

### Perguntas de domínio (respondidas pelo usuário)

- (preencher conforme decisão)

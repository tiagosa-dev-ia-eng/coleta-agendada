# Demandas do alinhamento

Registro das demandas levantadas no alinhamento com o cliente
(fonte original: anotação local `docs/anotacao.txt`, não versionada).
Cada demanda é implementada em **commit separado** que documenta a demanda atendida.

| ID | Demanda | Fonte documental | Status |
|---|---|---|---|
| D-01 | Mandar localização para farmácia/laboratório (local de coleta) mais próxima | Alinhamento com cliente; toca item PENDENTE "geolocalização" (doc 02) | Implementada (04/09/2026) — chatbot devolve a farmácia mais próxima |
| D-02 | No perfil paciente, mostrar publicidade das farmácias ou fornecedores | Alinhamento com cliente | Aguardando definição de regra de domínio |
| D-03 | Ponto de coleta: farmácia pode ou não ser ponto; ponto recebe agendamento, tem horário de funcionamento, técnico responsável e controle aberto/fechado | Alinhamento com cliente | Definição recebida (04/09/2026) — aguardando detalhes de implementação |
| D-04 | Contatos WhatsApp por perfil (BSUID @<nome> Meta): técnico e revenda com 1 número/nome; farmácia e laboratório com lista de números/nomes de contato | Alinhamento com cliente | Definição recebida (04/09/2026) — implementação em andamento |

## D-01 — Mandar localização para farmácia/laboratório (local de coleta) mais próxima

Texto original: *"Mandar localização para farmacia/laboratior (local de coleta) mas proxima"*.
Definição refinada (usuário, 04/09/2026): o paciente manda a localização e o
chatbot devolve o **local de coleta mais próximo**. **Ponto de coleta pode
ser: (1) uma farmácia ou (2) um laboratório** (decisão do usuário) — o
chatbot compara a distância do laboratório do canal e das farmácias da rede
com coordenadas cadastradas e responde o mais próximo, identificando o tipo
("é a farmácia X…" / "é o laboratório Y…").

Contexto no sistema atual:

- Nenhuma geolocalização implementada (item PENDENTE no doc 02).
- `organizations.Pharmacy` tem `address`, `city`, `state`, `zip_code` (texto) — sem coordenadas.
- `patients.Patient` não possui endereço/localização.
- `requests.CollectionRequest.preferred_location` e `scheduling.Appointment.location_label` são texto livre.

### Perguntas de domínio (respondidas pelo usuário — 04/09/2026)

- **Fluxo:** o paciente manda a localização e **o chatbot devolve o local de
  coleta mais próximo** — resposta direta no chat; interação pelo canal
  WhatsApp + IA / simulador do M8.
- **Cálculo de "mais próximo":** candidatos = **laboratório do canal** (se
  tiver coordenadas) **+ farmácias ativas da rede** ("conv.laboratory") com
  latitude/longitude cadastradas; distância Haversine (km), menor vence;
  resposta identifica o tipo do ponto. Cadastro das coordenadas via
  API/admin: "Pharmacy.latitude/longitude" e "Laboratory.latitude/longitude"
  (novos campos + endereço/cidade/UF/CEP do laboratório). CEP como
  fallback/geocodificação: evolução futura.

### Regra implementada

1. O webhook aceita mensagem de **localização estruturada**
   ("location": {"latitude": ..., "longitude": ...} — como o WhatsApp envia)
   ou texto com par "lat, lon".
2. Com localização válida, o pipeline resolve a farmácia mais próxima de forma
   **determinística (sem LLM)** — sem custo e sem risco de alucinação.
3. Paciente pergunta pela farmácia mais próxima **sem enviar localização**:
   o chatbot pede para compartilhar a localização (não escala a humano).
4. Sem ponto de coleta (farmácia ou laboratório) georreferenciado na rede:
   **encaminha a humano** (não inventa ponto de coleta — AGENTS.md regras 1 e 10).
5. Frontend: simulador ganhou envio de localização (demo) e sugestão de
   pergunta. Cadastro de coordenadas na tela de farmácias: evolução (hoje API).

## D-02 — Publicidade das farmácias ou fornecedores no perfil do paciente

Texto original: *"No perfil paciente mostrar publicidade das farmacaias ou fornecedores"*.

Contexto no sistema atual:

- Perfil paciente existe no backend (`patients.Patient`) e na área web do frontend.
- Não há modelo de anúncio/publicidade nem fornecedores cadastrados como entidade.

### Perguntas de domínio (respondidas pelo usuário)

- (preencher conforme decisão)

## D-03 — Ponto de coleta (definição)

Definição recebida do cliente (04/09/2026):

- **Uma farmácia pode ser ou não ser um ponto de coleta.**
- **Definição de ponto de coleta:**
  1. recebe agendamento;
  2. tem controle de horário de funcionamento (disponibilidade);
  3. tem um técnico responsável pela abertura e fechamento;
  4. tem controle de aberto/fechado controlado pelo técnico.

Contexto atual (pré-implementação):

- `Pharmacy` é a entidade "farmácia/ponto de coleta"; não há flag de ponto,
  nem horário de funcionamento, nem vínculo com técnico, nem estado
  aberto/fechado.
- O "local de coleta mais próximo" (D-01) hoje considera qualquer farmácia
  ativa georreferenciada; com a D-03 deve considerar **apenas pontos de
  coleta** (e a definição do que é ponto).

### Perguntas de domínio (respondidas pelo usuário)

- (preencher: laboratório também usa o mesmo flag? vínculo de técnicos por
  ponto/escala; aplicação da disponibilidade no agendamento; filtro de
  aberto/fechado na resposta D-01; granularidade do horário de funcionamento)

## D-04 — Contatos WhatsApp por perfil (BSUID Meta)

Definição recebida (04/09/2026): incluir nos modelos os contatos de WhatsApp
no padrão da Meta — número + nome de exibição + BSUID ("@<nome usuário>"):

- **Técnico:** número/nome do WhatsApp (obedecendo ao BSUID @<nome usuário>);
- **Farmácia:** lista de números/nomes do WhatsApp de contato;
- **Laboratório:** lista de números/nomes do WhatsApp de contato;
- **Revenda:** número/nome do WhatsApp.

Implementação: entidade compartilhada `WhatsAppContact` (apps.whatsapp) com
vínculo único a um dos perfis (técnico/revenda: no máx. 1; farmácia/laboratório:
vários) — serve de base para notificações/canais (G-05).

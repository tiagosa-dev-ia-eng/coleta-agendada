# Demandas de FRONTEND — handoff para o programador frontend

Este documento é a fonte das tarefas de FRONTEND (outro programador). O backend já está pronto para servir os dados; **o frontend nunca decide regra de negócio** (AGENTS.md §8).

Fonte da verdade: `AGENTS.md`, `docs/demandas.md`, `docs/BACKEND_GUIA_IA.md` e o pacote `docs/Coleta_Agendada_Documentacao_Tecnica_v1.0/`.

## 1. Ambiente e convenções

- Stack: Next.js 16 + React 19 + Tailwind CSS v4; rotas por perfil em `frontend/src/app/<perfil>/page.tsx` (perfis: paciente, farmacia, tecnico, revendedor, laboratorio; simulador em `whatsapp-simulator`).
- API: `NEXT_PUBLIC_API_URL` (default http://localhost:8000), base `/api/v1`; helper `frontend/src/lib/api.ts` (`apiFetch`, `API_URL`, erro em `error.message`).
- Auth: login JWT (`POST /api/v1/auth/login` → access) enviado como `Authorization: Bearer`; RBAC decidido no backend (4xx = sem permissão/regra).
- Estado/regras: sempre no backend; o frontend apenas exibe e dispara ações.
- pnpm com XDG dirs dentro do workspace (ver AGENTS.md §8).

## 2. Lista de tarefas frontend

| ID | Tarefa | Área | Depende de | Endpoints prontos |
|---|---|---|---|---|
| F-01 | **D-02 — Publicidade/parceiros no perfil paciente** (cards) | paciente | Definição de conteúdo (fazer pergunta ao PO) | Endpoint de parceiros será criado no backend após definição |
| F-02 | Gestão de **pontos de coleta** (criar/editar, janelas, designar técnico, abrir/fechar) | laboratorio/tecnico | — | `/api/v1/collection-points…` |
| F-03 | Ações de pagamento (cancelar link, estornar confirmado) | laboratorio | — | `POST /payments/{id}/cancel`, `POST /payments/{id}/refund` |
| F-04 | CRUD de exames (criar/editar/desativar) | laboratorio (admin) | — | `/api/v1/exams`, `/api/v1/exams/{id}` |
| F-05 | Edição de revendedor (status) | laboratorio | — | `GET/PATCH /api/v1/resellers/{id}` |
| F-06 | Visualização da auditoria | superuser | — | `GET /api/v1/audit` (filtros) |
| F-07 | Contatos WhatsApp por perfil (CRUD + edição) | laboratorio/farmacia/… | — | `/api/v1/whatsapp/contacts…` |
| F-08 | Indicador de versão da aplicação | global | — | `GET /api/v1/version` |
| F-09 | Botão de localização no simulador já existe; adequar copy do ponto mais próximo (horário/estado) | whatsapp-simulator | — | webhook |

## 3. Endpoints prontos (resumo para as telas)

### Pontos de coleta — `/api/v1/collection-points`
```
POST/PATCH /collection-points  {kind:"pharmacy|laboratory", pharmacy?, name, address, city, state, zip_code, latitude, longitude, status}
POST /collection-points/{id}/windows        {weekday:0-6, open_time:"HH:MM", close_time:"HH:MM"}
POST /collection-points/{id}/technicians    {technician_id}   (somente laboratório)
POST /collection-points/{id}/open | /close  (técnico designado)
GET  /collection-points                      (escopo por perfil)
```
Resposta inclui `is_open`, `windows[]`, `technicians[]`.

### Pagamentos — `/api/v1/payments`
```
GET  /requests/{id}/payments
POST /requests/{id}/payments/link {amount}      (laboratório)
POST /requests/{id}/payments      {amount}      (presencial; laboratório/farmácia)
POST /payments/{id}/confirm | /cancel | /refund (laboratório)
```

### Catálogo — `/api/v1/exams`
```
GET /exams                 (catálogo ativo + price do laboratório)
POST /exams {code,name}    (gestor)
PATCH/DELETE /exams/{id}   (name/active; delete = desativa)
POST /exams/{id}/price {price, active} (preço manual do laboratório)
```

### Auditoria — `GET /api/v1/audit` (superusuário: tudo; laboratório: o próprio; filtros action/entity_type/user_id/start/end)

### Contatos — `/api/v1/whatsapp/contacts` (POST/GET; PATCH/DELETE {id}; dono imutável; `meta_bsuid` "@nome.usuario")

### Versão — `GET /api/v1/version` → {"name","version"}

## 4. Próximos passos
1. Confirmar definição da D-02 com o PO (conteúdo/fonte/regra).
2. Implementar F-02 (maior valor operacional) usando os endpoints acima.
3. Manter o padrão: commit separado por demanda/tarefa + bump de versão (perguntar ao dono do backend sobre bump de frontend, pois VERSION é compartilhado).

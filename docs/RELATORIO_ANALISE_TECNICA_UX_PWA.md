# Relatório Consolidado de Análise Técnica, Demandas, UX e PWA
**Projeto:** Coleta Agendada  
**Versão Atual da Base de Código:** `v1.1.12` (commit `9a33684`)  
**Data da Sincronização:** 04/09/2026  
**Documentos de Referência Sincronizados:**  
- `AGENTS.md` (Regras de Governança e Arquitetura)  
- `docs/demandas.md` (Demandas de Negócio e Gates do Backend)  
- `docs/demandas-frontend.md` (Handoff e Tarefas F-01 a F-09)  
- `docs/BACKEND_GUIA_IA.md` (Catálogo Vivo de Endpoints e Modelos)  
- `PLANO_DE_IMPLEMENTACAO.md` (Marcos M0 a M11)

---

## 1. Matriz Unificada de Demandas e Sincronização Técnica

Esta seção cruza as **Demandas do Cliente (D-01 a D-04)** e as **Tarefas de Frontend (F-01 a F-09)** com o estado do **Backend na versão `v1.1.12`** e as especificações de **UX/PWA**.

| Demanda / ID | Escopo & Descrição | Status Backend (`v1.1.12`) | Status Frontend Atual | Solução de UX & Arquitetura Sincronizada |
|---|---|---|---|---|
| **D-01 / F-09** | **Local de Coleta mais Próximo (Geolocalização)**<br>Paciente envia localização e chatbot/web indica ponto mais próximo com horários. | ✅ **100% Concluído**<br>Cálculo Haversine determinístico (sem LLM); resposta formatada com nome, endereço, distância e janelas de funcionamento. | ⚠️ **Parcial (Simulador)**<br>Simulador possui campos de lat/lon, mas formulário web do paciente ainda usa texto livre. | • Botão *"Usar minha localização atual"* via `navigator.geolocation` no `/paciente` e `/whatsapp-simulator`.<br>• Card de indicação de distância em km e atalho direto de rota para Google Maps/Waze. |
| **D-02 / F-01** | **Publicidade / Parceiros no Perfil do Paciente**<br>Exibição de farmácias ou laboratórios parceiros da rede. | ⏳ **Aguardando Definição do PO**<br>Recomendação técnica: listar pontos de coleta ativos associados ao laboratório da última coleta do paciente. | ❌ **0%**<br>Nenhum componente na tela do paciente. | • Seção no `/paciente` com grid de cards informativos de unidades parceiras, endereço, horários de atendimento e benefícios locais. |
| **D-03 / F-02** | **Gestão de Pontos de Coleta (Entidade Própria)**<br>Ponto tem horários de funcionamento, técnico responsável, agenda e controle de aberto/fechado. | ✅ **100% Concluído**<br>App `collection_points` completo com endpoints de abertura/fechamento, janelas (`CollectionPointOperatingWindow`) e validação de disponibilidade e conflito (`v1.1.10`). | ❌ **0%**<br>Nenhuma tela web expõe a abertura/fechamento ou gestão de janelas. | • **Painel do Técnico:** Card fixo no topo com status (🟢/🔴) e botões de 48px para `[ Abrir Ponto ]` e `[ Fechar Ponto ]`.<br>• **Painel do Laboratório:** Aba de gerenciamento de pontos, grade semanal de horários e designação de técnicos.<br>• **Painel da Farmácia:** Visualização do estado do ponto e horários da semana. |
| **D-04 / F-07** | **Contatos WhatsApp por Perfil (BSUID Meta)**<br>Registro de telefones e identificadores `@<nome_usuario>` da Meta por organização/técnico. | ✅ **100% Concluído**<br>Modelo `WhatsAppContact` (`apps.whatsapp`) com regras estritas: 1 contato p/ técnico/revenda; múltiplos p/ laboratório/farmácia. | ❌ **0%**<br>Nenhum formulário web para gerenciar contatos de WhatsApp. | • Modal ou seção de "Configurações de Contato" no `/laboratorio`, `/farmacia`, `/revendedor` e `/tecnico` para edição de telefone, nome e `@bsuid`. |
| **F-03** | **Ações Financeiras de Pagamento**<br>Cancelamento de links pendentes e estorno de pagamentos confirmados (`v1.1.2`). | ✅ **100% Concluído**<br>`POST /api/v1/payments/{id}/cancel`<br>`POST /api/v1/payments/{id}/refund` | ❌ **0%**<br>Laboratório não possui botões de ação na listagem de pagamentos. | • Botões contextuais no `/laboratorio` ao lado de cada transação com diálogo de confirmação prévia para estorno financeiro. |
| **F-04** | **Catálogo de Exames (CRUD Completo)**<br>Criar novos exames globais, editar nome, código e ativar/desativar (`v1.1.1`). | ✅ **100% Concluído**<br>`POST /api/v1/exams`<br>`PATCH /api/v1/exams/{id}`<br>`DELETE /api/v1/exams/{id}` | ⚠️ **Parcial (20%)**<br>Laboratório só digita o preço manual; não cadastra novos exames. | • Tabela interativa com busca, botão `[ + Novo Exame ]` e modal de edição rápida no `/laboratorio`. |
| **F-05** | **Gestão de Revendedores**<br>Consulta e ativação/desativação de revendedores (`v1.1.5`). | ✅ **100% Concluído**<br>`GET/PATCH /api/v1/resellers/{id}` | ❌ **0%**<br>Laboratório não tem gestão de revendedores em tela. | • Seção de parceiros comerciais no `/laboratorio` com listagem e alternador de status (ativo/inativo). |
| **F-06** | **Trilha de Auditoria por Laboratório**<br>Consulta e inspeção de logs de eventos com isolamento por laboratório (`v1.1.9`). | ✅ **100% Concluído**<br>`GET /api/v1/audit` com filtros de ação, entidade, data e laboratório. | ❌ **0%**<br>Inexistente no frontend. | • Painel de conformidade e auditoria no `/laboratorio` e superusuário com filtros rápidos e visualizador de diff JSON. |
| **F-08** | **Indicador Dinâmico de Versão**<br>Rastreabilidade da versão interna da aplicação na interface (`v1.1.0`). | ✅ **100% Concluído**<br>`GET /api/v1/version` retornando `{"name": "coleta-agendada", "version": "1.1.12"}`. | ⚠️ **Estático**<br>Rodapé possui texto fixo sem consulta à API. | • Componente global no rodapé do `Shell.tsx` que consome `/api/v1/version` e exibe badge discreto `v1.1.12` com status da API. |

---

## 2. Auditoria Ergonômica & Diretrizes de UX (Mobile & Desktop)

### 2.1. Painel do Técnico (`/tecnico`) — Operação Crítica de Campo
1. **Padrão Touch-First (48px):**
   * Todos os botões primários (`Check-in`, `Concluir coleta`, `Abrir Ponto`, `Fechar Ponto`) devem ter altura mínima de **48px** e largura total em telas móveis (`w-full sm:w-auto`).
2. **Card de Turno / Ponto de Coleta (Demanda D-03):**
   * Fixo no topo do `/tecnico`:
     * Nome da unidade vinculada (ex.: *Ponto Central — Farmácia São Paulo*);
     * Horário da janela do dia (ex.: *07:00 às 13:00*);
     * Badge de estado em tempo real: 🟢 *Ponto Aberto* ou 🔴 *Ponto Fechado*;
     * Botão de ação: `[ Abrir Ponto de Coleta ]` ou `[ Encerrar Turno / Fechar Ponto ]`.
3. **Atalhos Operacionais Integrados:**
   * Atalho de rota GPS: botão `[ 🗺️ Rota ]` acionando `https://maps.google.com/?q={latitude},{longitude}` ou endereço codificado;
   * Atalho de contato: botão `[ 💬 WhatsApp ]` acionando `https://wa.me/{telefone}` com mensagem contextual pronta (*"Olá {nome}, sou o técnico de coleta..."*).
4. **Segurança contra Ações Involuntárias:**
   * Diálogo modal de confirmação antes de concluir a coleta para evitar toques acidentais durante o transporte de amostras.

---

### 2.2. Portal do Paciente (`/paciente`)
1. **Linha do Tempo Visual do Atendimento (Stepper):**
   * Substituir badges isolados por um indicador sequencial em 4 etapas:
     * `1. Solicitado` ➔ `2. Orçamento em Análise` ➔ `3. Agendado` ➔ `4. Coleta Realizada`.
2. **Geolocalização Assistida (Demanda D-01):**
   * No formulário de nova solicitação, ao escolher "Farmácia/Ponto", incluir botão `[ 📍 Usar meu local ]` que consulta a API de geolocalização do navegador e seleciona automaticamente o ponto mais próximo.
3. **Upload Acessível de Receita Médica:**
   * Área de arrastar e soltar (drag-and-drop), prévia visual da foto e botão específico para captura direta com a câmera do celular (`capture="environment"`).

---

### 2.3. Painel do Laboratório (`/laboratorio`)
1. **Interface Split View para Validação Humana (ADR-007):**
   * Coluna esquerda: visualizador do pedido médico anexado (imagem/PDF com zoom);
   * Coluna direita: lista de exames identificados pela IA, permitindo ajuste de quantidades, códigos e geração segura do orçamento final.
2. **Versionamento Visível de Orçamentos (v1.1.12 / RN-ORC-004 e RN-ORC-005):**
   * O laboratório visualiza claramente a evolução das versões do orçamento (`v1`, `v2`, `v3`). Quando um orçamento é aprovado pelo paciente, a interface desabilita edições e exibe o selo de imutabilidade.

---

## 3. Arquitetura PWA (Progressive Web App)

A implementação de PWA é indispensável para a usabilidade do técnico em locais sem cobertura celular (subsolos de clínicas ou residências isoladas) e para instalação instantânea no Android e iOS.

### 3.1. Especificação Técnica dos Arquivos:
* **`frontend/src/app/manifest.ts`:**
  * Manifesto nativo Next.js 16 declarando `display: "standalone"`, `theme_color: "#059669"`, `start_url: "/login"` e ícones em `public/icons/` (192px, 512px e maskable para Android).
* **`frontend/src/app/layout.tsx`:**
  * Metadados de `viewport` com `viewportFit: "cover"` e tratamento de Safe Areas do iOS (`env(safe-area-inset-top)` e `env(safe-area-inset-bottom)`).
* **Cache Offline com IndexedDB:**
  * A lista de coletas do dia atribuída ao técnico é sincronizada localmente no carregamento. Ao perder sinal de rede, o aplicativo permanece 100% operável para visualização de endereços, contatos e preparos dos exames.

---

## 4. Plano Diretor de Execução Sincronizada

| Fase | Prioridade | Tarefas Contempladas | Entregáveis de Código |
|---|---|---|---|
| **Fase 1** | **Imediata** | **F-02, D-03, UX Técnico** | • Card de abertura/fechamento do ponto de coleta no `/tecnico`.<br>• Alvos de toque de 48px e botões de atalho (Rota GPS e WhatsApp).<br>• Diálogo de confirmação para conclusão de coleta. |
| **Fase 2** | **Curto Prazo** | **PWA & F-08** | • Criação de `app/manifest.ts` e ícones PWA em `public/icons/`.<br>• Consumo dinâmico de `GET /api/v1/version` no rodapé (`Shell.tsx`).<br>• Redirecionamento da página inicial `/` para `/login` ou dashboard. |
| **Fase 3** | **Curto Prazo** | **F-09, D-01, UX Paciente** | • Botão de GPS no simulador e no formulário de solicitação (`/paciente`).<br>• Stepper visual de acompanhamento das 4 etapas no paciente.<br>• Área aprimorada de upload de pedidos médicos. |
| **Fase 4** | **Médio Prazo** | **F-03, F-04, F-05, F-06** | • Gestão de exames (CRUD) e ações de estorno financeiro no laboratório.<br>• Visualizador da trilha de auditoria escopada (`/audit`).<br>• Gestão de revendedores parceiros. |
| **Fase 5** | **Médio Prazo** | **F-07, D-04, F-01, D-02** | • Gerenciamento de contatos WhatsApp por perfil (com BSUID Meta).<br>• Componente de parceiros/publicidade no perfil do paciente (conforme alinhamento do PO). |

---
*Relatório consolidado e salvo em `docs/RELATORIO_ANALISE_TECNICA_UX_PWA.md`, sincronizando todas as demandas de negócio com a versão `v1.1.12` da base de código.*

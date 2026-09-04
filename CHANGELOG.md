# Changelog

Controle de versão INTERNO do projeto (REGRA GERAL: incrementar a cada mudança
e manter SEMPRE atualizado/publicado no GitHub — ver AGENTS.md e
docs/BACKEND_GUIA_IA.md).

| Versão | Data | Resumo |
|---|---|---|
| 1.1.29 | 04/09/2026 | fix(header): unificação e correção do header da página (Shell.tsx) com logo CA, breadcrumb de título, dados do usuário e botão de logout, eliminando duplicação visual e conflito sticky no preview. |
| 1.1.28 | 04/09/2026 | feat(auth-nav): botões de logout globais e melhorias na navegação do formulário de login (v1.1.28) + sincronização com backend v1.1.27. |
| 1.1.27 | 04/09/2026 | chore(collection_points): nova linha final em services.py. |
| 1.1.26 | 04/09/2026 | feat(auth-nav): botões de logout explícitos no Shell e na barra de topo, seletor de categorias demo e navegação aperfeiçoada no formulário de login (chips rápidos, toggle de senha, atalhos). |
| 1.1.25 | 04/09/2026 | feat(login-demo): cartões de acesso direto de demonstração com 1 clique para Paciente, Laboratório, Farmácia, Técnico e Revendedor no /login. |
| 1.1.24 | 04/09/2026 | feat(preview-contacts-gps): preview interativo multi-perfil, canais oficiais WhatsApp (F-07) em Laboratório e Farmácia, busca por GPS no simulador (F-09) e sincronização geral. |
| 1.1.23 | 04/09/2026 | docs: parâmetros de IA oficiais (B-07) + .env.example. |
| 1.1.22 | 04/09/2026 | feat(quotations): validade do orçamento de 15 dias (expiração automática após 15 dias). |
| 1.1.21 | 04/09/2026 | chore(lint): ajustes de estilo pós-merge. |
| 1.1.20 | 04/09/2026 | feat(preview-contacts-gps): preview interativo multi-perfil, canais oficiais WhatsApp (F-07) em Laboratório e Farmácia, e busca por GPS no simulador (F-09). |
| 1.1.19 | 04/09/2026 | feat(resellers-audit): gestão completa de revendedores (F-05) e trilha de auditoria e conformidade (F-06). |
| 1.1.18 | 04/09/2026 | feat(calendar-f04): calendário interativo multi-formato (semana/dia/WhatsApp) e CRUD completo de exames no laboratório (F-04). |
| 1.1.17 | 04/09/2026 | feat(laboratorio): gestão de pontos de coleta (F-02/D-03: criação, janelas e técnicos) e pagamentos (F-03: cancel/refund). |
| 1.1.16 | 04/09/2026 | feat(tecnico): gestão de pontos de coleta D-03 (abrir/fechar turno) e atalhos rápidos de campo (GPS/WhatsApp) no /tecnico (F-02). |
| 1.1.15 | 04/09/2026 | feat(pwa-ui): base PWA (manifest.ts, viewport safe-area) e ergonomia de botões 48px + ConfirmModal. |
| 1.1.14 | 04/09/2026 | feat(version): endpoint GET /api/v1/version e indicador dinâmico de versão no rodapé global (F-08). |
| 1.1.13 | 04/09/2026 | docs(ux-pwa): relatório de análise técnica de UX, ergonomia para técnicos de campo e diretrizes PWA (docs/RELATORIO_ANALISE_TECNICA_UX_PWA.md). |
| 1.1.0 | 04/09/2026 | Controle de versão interna (VERSION, scripts/bump-version.sh, targets make version-*, endpoint GET /api/v1/version). REGRA GERAL registrada: toda mudança incrementa a versão; validações de regra de negócio sempre no backend. |
| 1.0.0 | 04/09/2026 | Baseline: M0–M9, D-01 (local de coleta mais próximo), D-03 (entidade CollectionPoint: agendamento/disponibilidade/técnico/aberto-fechado), D-04 (contatos WhatsApp/BSUID) e documentação viva (até commit bdf0e94). |

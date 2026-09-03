# Coleta Agendada — Pacote de Documentação Técnica v1.0

**Data:** 03/08/2026  
**Status:** construído a partir do material fornecido
**Base:** apresentação visual do projeto + documento `para-po.pdf`

## Objetivo

Este pacote reconstrói a documentação necessária para desenvolvimento, manutenção, validação e evolução do projeto **Coleta Agendada**.

## Regra de interpretação do documento

Cada decisão é classificada como:

- **CONFIRMADO** — aparece explicitamente no material fornecido.
- **INFERIDO** — decorre diretamente dos fluxos e telas fornecidos.
- **PROPOSTO** — recomendação técnica para tornar a implementação completa.
- **PENDENTE** — necessita confirmação do Product Owner ou da equipe técnica.

## Documentos

1. `01-visao-produto-e-escopo.md`
2. `02-requisitos-funcionais.md`
3. `03-arquitetura-tecnica.md`
4. `04-perfis-rbac.md`
5. `05-fluxo-agendamento-e-estados.md`
6. `06-modelo-de-dados.md`
7. `07-api-rest.md`
8. `08-whatsapp-e-ia.md`
9. `09-orcamentos-e-validacao-humana.md`
10. `10-pagamentos-e-comissoes.md`
11. `11-seguranca-privacidade-e-auditoria.md`
12. `12-observabilidade-e-logs.md`
13. `13-infraestrutura-e-deploy.md`
14. `14-testes-e-criterios-de-aceite.md`
15. `15-roadmap-riscos-e-pendencias.md`
16. `16-guia-para-ia-de-codificacao.md`
17. `17-user-stories-e-backlog-inicial.md`
18. `18-decisoes-arquiteturais-adr.md`
19. `DOCUMENTACAO_TECNICA_COLETA_AGENDADA_v1.0.md`

## Stack recuperada

- Backend: Django + Django REST Framework
- Frontend: Node + Next.js + Tailwind CSS
- Banco: PostgreSQL (em containers dockers)
- Provisionamento dos micro serviços: Conteiners docker frontend + backend + postgres  com mapemento de volumes externos fontes e dados
- Cache / rate limiting: Redis
- IA: DeepSeek
- WhatsApp: webhook próprio
- Autenticação: JWT com refresh token
- Autorização: RBAC com cinco perfis

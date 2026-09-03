# 04 — Perfis e RBAC

## 1. Perfis confirmados

1. Laboratório
2. Revendedor
3. Farmácia
4. Técnico de enfermagem
5. Paciente

## 2. Matriz funcional recuperada

| Função | Laboratório | Revendedor | Farmácia | Técnico | Paciente |
|---|:---:|:---:|:---:|:---:|:---:|
| Dashboard geral | ✓ |  |  |  |  |
| Relatórios | ✓ |  |  |  |  |
| Acompanhar coletas | ✓ |  | ✓ | ✓ | ✓ |
| Cadastrar farmácias | ✓* | ✓ |  |  |  |
| Cadastrar técnicos | ✓* | ✓ |  |  |  |
| Consultar comissões | ✓ | ✓ | ✓ | ✓ |  |
| Agenda própria |  |  | ✓ | ✓ |  |
| Ponto de coleta |  |  | ✓ |  |  |
| Coleta domiciliar |  |  |  | ✓ |  |
| Check-in/check-out |  |  |  | ✓ |  |
| Solicitar coleta |  |  |  |  | ✓ |
| Aprovar orçamento |  |  |  |  | ✓ |
| Acompanhar status |  |  |  |  | ✓ |
| Atendimento WhatsApp |  |  | ✓* | ✓* | ✓ |

`*` = inferido ou depende de confirmação.

## 3. Política de autorização proposta

Cada usuário deve possuir:

- um `role`;
- escopo organizacional;
- permissões explícitas;
- vínculos com entidades que pode visualizar.

## 4. Princípio de menor privilégio

O material afirma que cada perfil visualiza somente as informações necessárias para sua operação.

Portanto:

- paciente vê apenas seus próprios dados;
- farmácia vê apenas coletas vinculadas à sua operação;
- técnico vê apenas sua agenda e coletas atribuídas;
- revendedor vê apenas sua rede;
- laboratório possui visão administrativa definida pelo escopo da organização.

**Status:** conceito CONFIRMADO; implementação detalhada PROPOSTA.

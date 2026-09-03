# 10 — Pagamentos e Comissões

## 1. Pagamento

O material confirma dois caminhos:

1. link de pagamento opcional;
2. pagamento presencial na coleta.

Também confirma que o pagamento não bloqueia a realização.

## 2. Estados sugeridos

```text
PENDING
LINK_CREATED
AUTHORIZED
CONFIRMED
FAILED
REFUNDED
CANCELED
```

**Status:** PROPOSTO.

## 3. Comissões confirmadas

### Modelo percentual
Exemplo do material:

- orçamento: R$ 100,00;
- farmácia: 10% = R$ 10,00;
- técnico: 15% = R$ 15,00.

### Modelo fixo
Exemplo do material:

- farmácia: R$ 15,00 por coleta;
- técnico: R$ 25,00 por coleta;
- revendedor: R$ 5,00 por agendamento.

## 4. Regra configurável

```text
calculation_type:
- PERCENTAGE
- FIXED
```

## 5. Gatilho

O diagrama indica que comissões são geradas após confirmação do pagamento.

Ao mesmo tempo, outro texto diz que a coleta pode ser realizada sem pagamento prévio.

Portanto:

```text
realização da coleta != geração definitiva da comissão
```

**Status:** INFERIDO.

## 6. Fórmulas

### Percentual

```text
commission = base_amount × percentage / 100
```

### Fixo

```text
commission = fixed_value
```

## 7. Regras recomendadas

- gravar regra usada no lançamento;
- gravar base de cálculo;
- impedir recálculo silencioso;
- permitir estorno;
- permitir período de vigência;
- permitir inativação sem apagar histórico.

## 8. Pendências

- qual evento torna comissão "a pagar";
- estorno após cancelamento;
- pagamento parcial;
- desconto;
- taxa de gateway;
- arredondamento;
- impostos;
- comissão em reagendamento.

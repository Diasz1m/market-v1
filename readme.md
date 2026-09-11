# Analista B3

Bot para analisar acoes da B3.

## O que faz hoje

Coleta os 22 indicadores fundamentalistas de todos os papeis da B3 no Fundamentus,
descarta os deslistados/sem liquidez, salva em CSV e gera graficos com filtros.

## Instalacao

```bash
pip install -r requirements.txt
playwright install chromium
```

## Uso

Primeiro colete os dados:

```bash
python main.py
```

Gera `dados/fundamentus_AAAA-MM-DD.csv` com os papeis negociaveis.

Depois gere os graficos:

```bash
python graficos.py
```

Gera quatro PNGs em `graficos/`:

| Arquivo | Conteudo |
|---|---|
| `dispersao.png` | P/VP x ROE com medianas formando quadrantes |
| `ranking.png` | maiores dividend yields |
| `distribuicao.png` | histogramas de P/L, P/VP, ROE e DY |
| `precos_base100.png` | evolucao dos precos normalizada, via Yahoo |

### Filtros

| Flag | Efeito |
|---|---|
| `--liquidez-minima` | volume minimo negociado em 2 meses, em R$ |
| `--pl-maximo` / `--pvp-maximo` | teto de preco |
| `--roe-minimo` / `--dy-minimo` | piso de rentabilidade / dividendos |
| `--excluir-prejuizo` | descarta empresas com P/L negativo |
| `--tickers` | restringe a papeis especificos |
| `--top` | mantem apenas os N mais liquidos |
| `--periodo` | janela da serie de precos (`6mo`, `1y`, `2y`...) |
| `--prefixo` | prefixo dos arquivos, para nao sobrescrever |

Exemplo, empresas liquidas e rentaveis:

```bash
python graficos.py --liquidez-minima 20000000 --excluir-prejuizo --roe-minimo 15 --prefixo qualidade
```

Comparando papeis especificos:

```bash
python graficos.py --tickers PETR4 VALE3 ITUB4 --periodo 6mo --prefixo blue
```

## Notas

As colunas `div_yield`, `mrg_bruta`, `mrg_ebit`, `mrg_liq`, `roic`, `roe` e
`cresc_rec_5a` estao em pontos percentuais (ex: `27,73` significa 27,73%).

Os graficos cortam os 5% extremos de cada ponta, porque casos isolados
(um ROE de -25.704%) achatam a escala. Com menos de 20 papeis o corte nao
e aplicado.

## Proximos passos

- Camada de analise: ranking fundamentalista (ex: Formula Magica de Greenblatt)
- Persistencia historica para comparar indicadores ao longo do tempo

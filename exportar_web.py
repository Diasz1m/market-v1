"""Exporta os dados coletados como JSON estatico para o SPA em web/.

O dataset inteiro tem ~250 papeis, entao cabe folgado no navegador e permite
filtrar tudo client-side, sem backend.
"""

import json
from pathlib import Path

import pandas as pd
import yfinance as yf

from graficos import carregar_dados, filtrar

PASTA_WEB = Path(__file__).parent.parent / "web" / "public" / "dados"
TICKERS_HISTORICO = 12
PERIODO_HISTORICO = "1y"


def _limpar(valor):
    """JSON nao aceita NaN/Infinity; o Fundamentus produz os dois."""
    if valor is None or not isinstance(valor, (int, float)):
        return valor
    if pd.isna(valor) or valor in (float("inf"), float("-inf")):
        return None
    return round(float(valor), 4)


def exportar_acoes(df):
    registros = [
        {coluna: _limpar(valor) for coluna, valor in linha.items()}
        for linha in df.to_dict(orient="records")
    ]
    return {
        "data": df.attrs.get("origem", ""),
        "total": len(registros),
        "acoes": registros,
    }


def exportar_historico(tickers, periodo=PERIODO_HISTORICO):
    """Series de fechamento em base 100, ja prontas para plotar."""
    cotacoes = yf.download(list(tickers), period=periodo, progress=False, auto_adjust=True)["Close"]
    if isinstance(cotacoes, pd.Series):
        cotacoes = cotacoes.to_frame(name=list(tickers)[0])
    cotacoes = cotacoes.dropna(how="all").ffill().dropna(axis=1, how="any")

    base = cotacoes / cotacoes.iloc[0] * 100
    return {
        "periodo": periodo,
        "datas": [d.strftime("%Y-%m-%d") for d in base.index],
        "series": {
            ticker: {
                "base100": [round(float(v), 2) for v in base[ticker]],
                "preco": [round(float(v), 2) for v in cotacoes[ticker]],
            }
            for ticker in base.columns
        },
    }


def main():
    PASTA_WEB.mkdir(parents=True, exist_ok=True)
    bruto = carregar_dados()

    acoes = exportar_acoes(bruto)
    (PASTA_WEB / "acoes.json").write_text(
        json.dumps(acoes, ensure_ascii=False), encoding="utf-8"
    )
    print(f"acoes.json      {acoes['total']} papeis")

    mais_liquidos = filtrar(bruto, top_n=TICKERS_HISTORICO)["ticker"]
    historico = exportar_historico(mais_liquidos)
    (PASTA_WEB / "historico.json").write_text(
        json.dumps(historico, ensure_ascii=False), encoding="utf-8"
    )
    print(f"historico.json  {len(historico['series'])} series x {len(historico['datas'])} dias")
    print(f"\nDestino: {PASTA_WEB}")


if __name__ == "__main__":
    main()

import asyncio
import re
from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf
from playwright.async_api import async_playwright

URL_FUNDAMENTUS = "https://www.fundamentus.com.br/resultado.php"
PASTA_DADOS = Path(__file__).parent / "dados"

COLUNAS = [
    "papel", "cotacao", "pl", "pvp", "psr", "div_yield", "p_ativo",
    "p_cap_giro", "p_ebit", "p_ativ_circ_liq", "ev_ebit", "ev_ebitda",
    "mrg_bruta", "mrg_ebit", "mrg_liq", "liq_corr", "roic", "roe",
    "liq_2meses", "patrim_liq", "div_liq_patrim", "cresc_rec_5a",
]

COLUNAS_PERCENTUAIS = [
    "div_yield", "mrg_bruta", "mrg_ebit", "mrg_liq", "roic", "roe", "cresc_rec_5a",
]


def para_numero(texto):
    """Converte o formato brasileiro do Fundamentus ('1.234,56', '13,66%') em float."""
    if texto is None:
        return None
    limpo = re.sub(r"[%\s]", "", texto).replace(".", "").replace(",", ".")
    if limpo in ("", "-"):
        return None
    try:
        return float(limpo)
    except ValueError:
        return None


async def _extrair_tabela():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            page = await browser.new_page()
            await page.goto(URL_FUNDAMENTUS, timeout=60_000)
            await page.wait_for_selector("table#resultado")
            return await page.eval_on_selector_all(
                "table#resultado tbody tr",
                "linhas => linhas.map(l => Array.from(l.querySelectorAll('td'))"
                ".map(c => c.textContent.trim()))",
            )
        finally:
            await browser.close()


def coletar_fundamentus():
    """Raspa os 22 indicadores fundamentalistas de todos os papeis listados."""
    linhas = asyncio.run(_extrair_tabela())
    linhas = [l for l in linhas if len(l) == len(COLUNAS)]

    df = pd.DataFrame(linhas, columns=COLUNAS)
    df["ticker"] = df["papel"] + ".SA"
    for coluna in COLUNAS[1:]:
        df[coluna] = df[coluna].map(para_numero)
    return df


def filtrar_negociaveis(df, liquidez_minima=100_000):
    """Descarta papeis deslistados ou sem liquidez relevante nos ultimos 2 meses."""
    return (
        df[(df["liq_2meses"].fillna(0) >= liquidez_minima) & (df["cotacao"].fillna(0) > 0)]
        .sort_values("liq_2meses", ascending=False)
        .reset_index(drop=True)
    )


def salvar_csv(df, nome):
    PASTA_DADOS.mkdir(exist_ok=True)
    caminho = PASTA_DADOS / f"{nome}_{date.today():%Y-%m-%d}.csv"
    df.to_csv(caminho, index=False, encoding="utf-8-sig", decimal=",", sep=";")
    return caminho


def buscar_precos(tickers, lote=100):
    """Cotacoes de fechamento via Yahoo, em lotes para nao esgotar a API."""
    tickers = list(tickers)
    fechamentos = {}
    for inicio in range(0, len(tickers), lote):
        grupo = tickers[inicio:inicio + lote]
        dados = yf.download(grupo, period="5d", progress=False, auto_adjust=True)
        if dados.empty:
            continue
        close = dados["Close"]
        for ticker in grupo:
            if ticker in close and close[ticker].notna().any():
                fechamentos[ticker] = float(close[ticker].dropna().iloc[-1])
    return pd.Series(fechamentos, name="preco_yahoo")


def historico(ticker, periodo="max"):
    return yf.Ticker(ticker).history(period=periodo)


if __name__ == "__main__":
    print("Coletando indicadores do Fundamentus...")
    bruto = coletar_fundamentus()
    print(f"  {len(bruto)} papeis encontrados")

    acoes = filtrar_negociaveis(bruto)
    print(f"  {len(acoes)} papeis com liquidez relevante")

    caminho = salvar_csv(acoes, "fundamentus")
    print(f"Dados salvos em {caminho}")

    print("\nTop 10 por liquidez:")
    print(acoes[["ticker", "cotacao", "pl", "pvp", "roe", "div_yield", "liq_2meses"]].head(10).to_string(index=False))

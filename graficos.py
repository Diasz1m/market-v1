"""Graficos dos indicadores coletados pelo main.py."""

import argparse
from pathlib import Path

import matplotlib
import pandas as pd
import yfinance as yf

# Backend sem janela: o tkagg quebra ao conviver com as threads do yfinance.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PASTA_DADOS = Path(__file__).parent / "dados"
PASTA_GRAFICOS = Path(__file__).parent / "graficos"

COR = "#1f77b4"
COR_DESTAQUE = "#d62728"

ROTULOS = {
    "pl": "P/L",
    "pvp": "P/VP",
    "roe": "ROE (%)",
    "roic": "ROIC (%)",
    "div_yield": "Dividend Yield (%)",
    "ev_ebit": "EV/EBIT",
    "mrg_liq": "Margem líquida (%)",
    "liq_2meses": "Liquidez 2 meses (R$)",
    "cotacao": "Cotação (R$)",
}


def carregar_dados(arquivo=None):
    """Le o CSV mais recente gravado pelo main.py."""
    if arquivo is None:
        disponiveis = sorted(PASTA_DADOS.glob("fundamentus_*.csv"))
        if not disponiveis:
            raise FileNotFoundError("Nenhum CSV em dados/. Rode 'python main.py' primeiro.")
        arquivo = disponiveis[-1]
    df = pd.read_csv(arquivo, sep=";", decimal=",", encoding="utf-8-sig")
    df.attrs["origem"] = Path(arquivo).stem[-10:]
    return df


def sem_extremos(df, colunas, inferior=0.05, superior=0.95, minimo=20):
    """Corta as caudas das colunas indicadas.

    Necessario porque casos isolados (um ROE de -25.704%) achatam qualquer escala.
    Abaixo de `minimo` papeis nada e removido: numa selecao pequena todo ponto foi
    pedido de proposito.
    """
    if len(df) < minimo:
        return df

    recorte = df
    for coluna in colunas:
        limite_baixo, limite_alto = df[coluna].quantile([inferior, superior])
        recorte = recorte[recorte[coluna].between(limite_baixo, limite_alto)]
    return recorte


def filtrar(df, liquidez_minima=None, pl_maximo=None, pvp_maximo=None,
            roe_minimo=None, dy_minimo=None, excluir_prejuizo=False,
            tickers=None, top_n=None):
    """Aplica os filtros informados; parametros deixados em None sao ignorados."""
    recorte = df.copy()

    if liquidez_minima is not None:
        recorte = recorte[recorte["liq_2meses"] >= liquidez_minima]
    if pl_maximo is not None:
        recorte = recorte[recorte["pl"] <= pl_maximo]
    if pvp_maximo is not None:
        recorte = recorte[recorte["pvp"] <= pvp_maximo]
    if roe_minimo is not None:
        recorte = recorte[recorte["roe"] >= roe_minimo]
    if dy_minimo is not None:
        recorte = recorte[recorte["div_yield"] >= dy_minimo]
    if excluir_prejuizo:
        recorte = recorte[recorte["pl"] > 0]
    if tickers:
        alvos = {t.replace(".SA", "").upper() for t in tickers}
        recorte = recorte[recorte["papel"].isin(alvos)]

    recorte = recorte.sort_values("liq_2meses", ascending=False)
    if top_n is not None:
        recorte = recorte.head(top_n)

    recorte.attrs = df.attrs
    return recorte.reset_index(drop=True)


def _salvar(fig, nome):
    PASTA_GRAFICOS.mkdir(exist_ok=True)
    destino = PASTA_GRAFICOS / f"{nome}.png"
    fig.savefig(destino, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return destino


def dispersao(df, eixo_x="pvp", eixo_y="roe", nome="dispersao"):
    """Dispersao com medianas dividindo o plano em quadrantes.

    O tamanho do ponto representa a liquidez, entao cada bolha carrega 3 variaveis.
    """
    dados = sem_extremos(df, [eixo_x, eixo_y])
    fig, ax = plt.subplots(figsize=(11, 7))

    ax.scatter(
        dados[eixo_x], dados[eixo_y],
        s=dados["liq_2meses"] / dados["liq_2meses"].max() * 400 + 15,
        alpha=0.5, color=COR, edgecolors="white",
    )
    ax.axvline(dados[eixo_x].median(), color="gray", linestyle="--", linewidth=1)
    ax.axhline(dados[eixo_y].median(), color="gray", linestyle="--", linewidth=1)

    for _, linha in dados.nlargest(8, "liq_2meses").iterrows():
        ax.annotate(linha["papel"], (linha[eixo_x], linha[eixo_y]), fontsize=9, weight="bold")

    ax.set_xlabel(ROTULOS.get(eixo_x, eixo_x))
    ax.set_ylabel(ROTULOS.get(eixo_y, eixo_y))
    ax.set_title(f"{ROTULOS.get(eixo_x, eixo_x)} x {ROTULOS.get(eixo_y, eixo_y)} "
                 f"— {len(dados)} papéis — {df.attrs.get('origem', '')}")
    ax.grid(alpha=0.2)
    return _salvar(fig, nome)


def ranking(df, coluna="div_yield", n=15, nome="ranking"):
    """Barras horizontais com os n maiores valores da coluna."""
    dados = sem_extremos(df, [coluna], superior=0.98).nlargest(n, coluna).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, max(4, n * 0.38)))

    barras = ax.barh(dados["papel"], dados[coluna], color=COR, alpha=0.85)
    ax.bar_label(barras, fmt="%.1f", padding=3, fontsize=9)

    ax.set_xlabel(ROTULOS.get(coluna, coluna))
    ax.set_title(f"Maiores {ROTULOS.get(coluna, coluna)} — {df.attrs.get('origem', '')}")
    ax.margins(x=0.12)
    ax.grid(axis="x", alpha=0.2)
    return _salvar(fig, nome)


def distribuicao(df, colunas=("pl", "pvp", "roe", "div_yield"), nome="distribuicao"):
    """Histogramas lado a lado para situar um papel em relacao ao mercado."""
    fig, eixos = plt.subplots(2, 2, figsize=(12, 8))

    for ax, coluna in zip(eixos.flat, colunas):
        dados = sem_extremos(df, [coluna])[coluna]
        ax.hist(dados, bins=30, color=COR, alpha=0.75, edgecolor="white")
        ax.axvline(dados.median(), color=COR_DESTAQUE, linestyle="--", linewidth=1.5,
                   label=f"mediana {dados.median():.2f}")
        ax.set_xlabel(ROTULOS.get(coluna, coluna))
        ax.set_ylabel("nº de papéis")
        ax.legend(fontsize=9)
        ax.grid(alpha=0.2)

    fig.suptitle(f"Distribuição dos indicadores — {df.attrs.get('origem', '')}", fontsize=13)
    fig.tight_layout()
    return _salvar(fig, nome)


def series_precos(tickers, periodo="1y", nome="precos_base100"):
    """Evolucao dos precos normalizada em base 100, para comparar papeis de precos diferentes."""
    cotacoes = yf.download(list(tickers), period=periodo, progress=False, auto_adjust=True)["Close"]
    if isinstance(cotacoes, pd.Series):
        cotacoes = cotacoes.to_frame(name=list(tickers)[0])
    cotacoes = cotacoes.dropna(how="all").ffill().dropna(axis=1, how="any")

    base = cotacoes / cotacoes.iloc[0] * 100
    fig, ax = plt.subplots(figsize=(12, 7))

    for ticker in base.columns:
        ax.plot(base.index, base[ticker], linewidth=1.6, label=ticker)
        ax.annotate(f"{base[ticker].iloc[-1]:.0f}", (base.index[-1], base[ticker].iloc[-1]),
                    fontsize=9, weight="bold")

    ax.axhline(100, color="gray", linestyle="--", linewidth=1)
    ax.set_ylabel("Base 100 no início do período")
    ax.set_title(f"Evolução relativa — período de {periodo}")
    ax.legend(ncol=2, fontsize=9)
    ax.grid(alpha=0.2)
    return _salvar(fig, nome)


def _cli():
    parser = argparse.ArgumentParser(description="Gera os graficos dos dados do Fundamentus.")
    parser.add_argument("--liquidez-minima", type=float, help="volume minimo em 2 meses, em R$")
    parser.add_argument("--pl-maximo", type=float, help="P/L maximo")
    parser.add_argument("--pvp-maximo", type=float, help="P/VP maximo")
    parser.add_argument("--roe-minimo", type=float, help="ROE minimo em %%")
    parser.add_argument("--dy-minimo", type=float, help="dividend yield minimo em %%")
    parser.add_argument("--excluir-prejuizo", action="store_true", help="descarta P/L negativo")
    parser.add_argument("--tickers", nargs="+", help="restringe a papeis especificos")
    parser.add_argument("--top", type=int, dest="top_n", help="mantem os N mais liquidos")
    parser.add_argument("--periodo", default="1y", help="janela da serie de precos (ex: 6mo, 2y)")
    parser.add_argument("--prefixo", default="", help="prefixo dos arquivos, para nao sobrescrever")
    return parser.parse_args()


if __name__ == "__main__":
    args = _cli()
    bruto = carregar_dados()
    acoes = filtrar(
        bruto,
        liquidez_minima=args.liquidez_minima,
        pl_maximo=args.pl_maximo,
        pvp_maximo=args.pvp_maximo,
        roe_minimo=args.roe_minimo,
        dy_minimo=args.dy_minimo,
        excluir_prejuizo=args.excluir_prejuizo,
        tickers=args.tickers,
        top_n=args.top_n,
    )
    print(f"{len(acoes)} papeis apos os filtros (de {len(bruto)})")

    if acoes.empty:
        raise SystemExit("Nenhum papel sobrou. Afrouxe os filtros.")

    p = f"{args.prefixo}_" if args.prefixo else ""
    for caminho in (
        dispersao(acoes, nome=f"{p}dispersao"),
        ranking(acoes, nome=f"{p}ranking"),
        distribuicao(acoes, nome=f"{p}distribuicao"),
        series_precos(acoes["ticker"].head(6), periodo=args.periodo, nome=f"{p}precos_base100"),
    ):
        print(f"  {caminho}")

import yfinance as yf
from playwright.async_api import async_playwright
import asyncio
import pandas as pd
acoes = [];
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="max")

##ESSA FUNCAO PEGA AS ACOES DA B3 POR WEB SCRAPING
async def get_stock_info():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://www.fundamentus.com.br/resultado.php")
        
        await page.wait_for_selector('table#resultado')
        
        rows = await page.query_selector_all('table#resultado tbody tr')
        
        for row in rows[:1000]: 
            columns = await row.query_selector_all('td')
            if columns:
                papel = await columns[0].text_content()
                cotacao = await columns[1].text_content()
                pl = await columns[2].text_content()
                pvp = await columns[3].text_content()
                acoes.append(papel + ".SA");
                
        await browser.close()

def print_acoes(acoes):
    for acao in acoes:
        print(acao)

def listar_acoes_por_webscraping():
    asyncio.run(get_stock_info())
    return acoes;


def get_info_market(market):
    return yf.Market(market)

def print_info_market(info_market):
    print(pd.DataFrame(info_market.summary))

def listar_acoes_b3():
    # Lista de algumas das principais ações da B3
    for acao in acoes:
        try:
            stock = yf.Ticker(acao)
            info = stock.info
            if info.get('longName') is None:
                continue
            if info.get('market') != "br_market":
                continue
            print(f"\nAção: {acao}")
            print(f"Nome: {info.get('longName', 'N/A')}")
            print(f"Preço Atual: R$ {info.get('currentPrice', 'N/A')}")
            print(f"Variação 24h: {info.get('regularMarketChangePercent', 'N/A')}%")
        except Exception as e:
            print(f"Erro ao obter dados para {acao}: {str(e)}")

if __name__ == "__main__":
    print("Listando principais ações da B3:")
    # asyncio.run(get_stock_info())
    info_market = get_info_market("GB")
    # listar_acoes_b3()
    print_info_market(info_market)


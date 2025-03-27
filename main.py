"import yfinance as yf" 

import yfinance as yf

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="max")

##TODO aqui fazer uma função para listar as ações da b3
## vou tentar fazer um webscraping para pegar as ações da b3
## https://www.fundamentus.com.br/resultado.php
def listar_acoes_b3():
    # Lista de algumas das principais ações da B3
    acoes_b3 = [
        "PETR4.SA",  # Petrobras
        "VALE3.SA",  # Vale
        "ITUB4.SA",  # Itaú
        "BBDC4.SA",  # Bradesco
        "ABEV3.SA",  # Ambev
        "MGLU3.SA",  # Magazine Luiza
        "BBAS3.SA",  # Banco do Brasil
        "B3SA3.SA",  # B3
        "WEGE3.SA",  # WEG
        "RENT3.SA"   # Localiza
    ]
    
    for acao in acoes_b3:
        try:
            stock = yf.Ticker(acao)
            info = stock.info
            print(f"\nAção: {acao}")
            print(f"Nome: {info.get('longName', 'N/A')}")
            print(f"Preço Atual: R$ {info.get('currentPrice', 'N/A')}")
            print(f"Variação 24h: {info.get('regularMarketChangePercent', 'N/A')}%")
        except Exception as e:
            print(f"Erro ao obter dados para {acao}: {str(e)}")

if __name__ == "__main__":
    print("Listando principais ações da B3:")
    listar_acoes_b3()



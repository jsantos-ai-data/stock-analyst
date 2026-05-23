import json
import yfinance as yf

def get_stock_market_data(ticker: str) -> str:
    """Busca cotações e métricas financeiras REAIS de uma ação listada na B3 via Yahoo Finance."""
    print(f"\n   [EXECUÇÃO TOOL] -> yfinance consultando: {ticker}")
    try:
        formatted_ticker = ticker.upper().strip()
        if not formatted_ticker.endswith(".SA"):
            formatted_ticker = f"{formatted_ticker}.SA"
            
        stock = yf.Ticker(formatted_ticker)
        info = stock.info
        
        if not info or ("regularMarketPrice" not in info and "currentPrice" not in info):
            return f"Dados indisponíveis para o ticker {ticker}."
            
        metrics = {
            "preco_atual": info.get("currentPrice") or info.get("regularMarketPrice"),
            "trailing_PL": info.get("trailingPE"),
            "dividend_yield": f"{round(info.get('dividendYield', 0), 2)}%" if info.get('dividendYield') else "N/A",
            "market_cap": info.get("marketCap")
        }
        return json.dumps(metrics, ensure_ascii=False)
    except Exception as e:
        return f"Erro na API de cotações: {str(e)}"

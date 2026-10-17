# import os, requests
# from dotenv import load_dotenv
#
# load_dotenv()
# key = os.getenv("FINNHUB_API_KEY")
# print("Finnhub key:", bool(key))
# resp = requests.get(f"https://finnhub.io/api/v1/quote?symbol=TCS&token={key}")
# print(resp.json())
#
#
# infoway_key=os.getenv("INFOWAY_API_KEY")
#
# api_url = (
#     f"https://data.infoway.io/stock/batch_trade/TCS.IN"
# )
#
# headers = {
#     "Accept": "application/json",
#     "apiKey": infoway_key,
# }
#
# response = requests.get(
#     api_url,
#     headers=headers,
#     timeout=10
# )
#
# response.raise_for_status()
#
# data = response.json()
#
# if data.get("data"):
#     print(data)
# else:print("Infoway failed")
#
# # Y‑Finance test (no key needed)
# import yfinance as yf
# print(yf.Ticker("TCS.NS").fast_info.get("last_price"))
#
#
#
#
#
#
#












import yfinance as yf


def get_stock_data(symbol: str):
    stock = yf.Ticker(symbol)

    info = stock.info

    return {
        "symbol": symbol,
        "company_name": info.get("longName"),
        "current_price": info.get("currentPrice"),
        "open_price": info.get("open"),
        "previous_close": info.get("previousClose"),
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "volume": info.get("volume"),
        "market_cap": info.get("marketCap"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "currency": info.get("currency"),
        "exchange": info.get("exchange")
    }


data = get_stock_data("AAPL")

for key, value in data.items():
    print(f"{key}: {value}")



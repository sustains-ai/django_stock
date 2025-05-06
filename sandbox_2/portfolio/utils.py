import yfinance as yf
import pandas as pd
from .models import HistoricalStockData, Portfolio
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Uncomment and use if needed
# def fetch_and_store_historical_data(portfolio_id, symbol):
#     try:
#         portfolio = Portfolio.objects.get(id=portfolio_id)
#
#         # Fetch 5 years of daily adjusted close data
#         stock = yf.Ticker(symbol)
#         df = stock.history(period="5y")  # Get 5 years of data
#
#         if df.empty:
#             print(f"No data found for {symbol} in Portfolio {portfolio.name}")
#             return
#
#         df.reset_index(inplace=True)
#         df = df[['Date', 'Close']].dropna()  # Keep Date & Adjusted Close, remove NaN
#         df.rename(columns={'Close': 'adjusted_close'}, inplace=True)
#
#         # Save historical data per portfolio
#         for _, row in df.iterrows():
#             HistoricalStockData.objects.update_or_create(
#                 portfolio=portfolio,
#                 symbol=symbol,
#                 date=row['Date'].date(),
#                 defaults={'adjusted_close': row['adjusted_close']}
#             )
#         print(f"Stored {len(df)} records for {symbol} in Portfolio {portfolio.name}")
#
#     except Exception as e:
#         print(f"Error fetching data for {symbol} in Portfolio {portfolio_id}: {e}")

def fetch_news_sentiment(symbol="AAPL", limit=10):
    """Fetch news sentiment data from Alpha Vantage."""
    try:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&limit={limit}&sort=LATEST&apikey={api_key}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Alpha Vantage News API error: {response.status_code}")
            return []

        data = response.json()
        return data.get("feed", [])
    except Exception as e:
        print(f"Error fetching news sentiment for {symbol}: {e}")
        return []

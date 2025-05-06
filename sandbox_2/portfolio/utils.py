import yfinance as yf
import pandas as pd
from .models import HistoricalStockData, Portfolio
import os
import requests
from dotenv import load_dotenv

load_dotenv()



def fetch_news_sentiment():
    """Fetch the latest news sentiment data from Alpha Vantage."""
    try:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&sort=LATEST&limit=10&apikey={api_key}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Alpha Vantage News API error: {response.status_code}")
            return []

        news_sentiment_data = response.json()
        return news_sentiment_data.get("feed", [])
    except Exception as e:
        print(f"Error fetching news sentiment: {e}")
        return []

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


def global_open_closed_status():
    try:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            raise ValueError("Missing ALPHA_VANTAGE_API_KEY in environment variables.")

        url = f"https://www.alphavantage.co/query?function=MARKET_STATUS&apikey={api_key}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"❌ Failed request. Status Code: {response.status_code}")
            return None

        global_open_close_data = response.json()
        if "markets" not in global_open_close_data:
            print("❌ Unexpected response format or missing 'markets' key.")
            return None

        # ✅ Wrap the list inside a dict with "markets" key
        return global_open_close_data

    except requests.exceptions.Timeout:
        print("⏱️ Request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return None










# utils.py

import yfinance as yf  # Not used in the functions we're caching, but keep if used elsewhere
import pandas as pd  # Not used in the functions we're caching, but keep if used elsewhere
# from .models import HistoricalStockData, Portfolio # Not directly used here, consider if needed
import os
import requests
from dotenv import load_dotenv
import numpy as np
from datetime import datetime  # Ensure datetime is imported

from django.core.cache import cache  # <<<--- IMPORT REDIS CACHE

load_dotenv()


def fetch_news_sentiment(symbol="AAPL", limit=10):  # Added symbol and limit params to make it more generic
    """Fetch the latest news sentiment data from Alpha Vantage, with Redis caching."""
    # 1. Define Cache Key
    cache_key = f"news_sentiment_av_{symbol}_limit{limit}"

    # 2. Check Cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        print(f"Cache HIT for {cache_key} (news_sentiment)")
        return cached_data

    print(f"Cache MISS for {cache_key} (news_sentiment). Fetching from Alpha Vantage...")
    # 3. API Call on Cache Miss
    try:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            print("Error: ALPHA_VANTAGE_API_KEY not set.")
            return []

        # Added tickers parameter based on the function in your models.py
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&sort=LATEST&limit={limit}&apikey={api_key}"
        response = requests.get(url, headers={"User-Agent": "python-requests"})  # Added User-Agent
        response.raise_for_status()  # Check for HTTP errors

        news_sentiment_data = response.json()
        feed_data = news_sentiment_data.get("feed", [])

        # 4. Store in Cache
        # News sentiment can change, but API limits are strict. Cache for ~30 mins.
        cache_timeout_seconds = 60 * 30  # 30 minutes
        cache.set(cache_key, feed_data, timeout=cache_timeout_seconds)
        print(f"Set cache for {cache_key} (news_sentiment) for {cache_timeout_seconds}s")

        return feed_data
    except requests.exceptions.HTTPError as http_err:
        print(
            f"HTTP error (fetch_news_sentiment for {symbol}): {http_err} - Response: {response.text if 'response' in locals() else 'N/A'}")
        return []
    except requests.exceptions.RequestException as req_err:
        print(f"Request error (fetch_news_sentiment for {symbol}): {req_err}")
        return []
    except (KeyError, ValueError, TypeError) as e:
        print(
            f"Data processing error (fetch_news_sentiment for {symbol}): {e} - Data: {news_sentiment_data if 'news_sentiment_data' in locals() else 'N/A'}")
        return []
    except Exception as e:
        print(f"Unexpected error (fetch_news_sentiment for {symbol}): {e}")
        return []


def global_open_closed_status():
    """Fetch global market open/closed status from Alpha Vantage, with Redis caching."""
    # 1. Define Cache Key
    cache_key = "market_status_av_global"  # This data is global and doesn't depend on params

    # 2. Check Cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        print(f"Cache HIT for {cache_key} (global_market_status)")
        return cached_data

    print(f"Cache MISS for {cache_key} (global_market_status). Fetching from Alpha Vantage...")
    # 3. API Call on Cache Miss
    try:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            print("Error: ALPHA_VANTAGE_API_KEY not set.")  # Changed from raise to print for consistency
            return None

        url = f"https://www.alphavantage.co/query?function=MARKET_STATUS&apikey={api_key}"
        response = requests.get(url, timeout=10, headers={"User-Agent": "python-requests"})
        response.raise_for_status()

        global_open_close_data = response.json()
        if "markets" not in global_open_close_data:
            print("❌ Unexpected response format or missing 'markets' key (global_market_status).")
            return None

        # 4. Store in Cache
        # Market status changes, but not every second for all markets. Cache for 5-15 mins.
        cache_timeout_seconds = 60 * 10  # 10 minutes
        cache.set(cache_key, global_open_close_data, timeout=cache_timeout_seconds)
        print(f"Set cache for {cache_key} (global_market_status) for {cache_timeout_seconds}s")

        return global_open_close_data

    except requests.exceptions.Timeout:
        print("⏱️ Request timed out (global_market_status).")
        return None
    except requests.exceptions.HTTPError as http_err:
        print(
            f"HTTP error (global_market_status): {http_err} - Response: {response.text if 'response' in locals() else 'N/A'}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed (global_market_status): {e}")
        return None
    except (KeyError, ValueError, TypeError) as e:
        print(
            f"Data processing error (global_market_status): {e} - Data: {global_open_close_data if 'global_open_close_data' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred (global_market_status): {e}")
        return None


def fetch_currency_exchange_rates():
    """
    Fetch specific currency exchange rates from Alpha Vantage, with Redis caching for each pair.
    - BTC to USD
    - ETH to USD
    - USD to INR
    - USD to EUR
    - USD to AED
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("Error: ALPHA_VANTAGE_API_KEY not set.")  # Changed from raise
        return []  # Return empty list if API key is missing

    base_url = "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE"
    currency_pairs = [
        ("BTC", "USD"),
        ("ETH", "USD"),
        ("USD", "INR"),
        ("USD", "EUR"),
        ("USD", "AED"),
    ]
    results = []

    for from_currency, to_currency in currency_pairs:
        # 1. Define Cache Key per currency pair
        cache_key = f"currency_exchange_rate_av_{from_currency}_{to_currency}"

        # 2. Check Cache
        cached_rate_info = cache.get(cache_key)
        if cached_rate_info is not None:
            print(f"Cache HIT for {cache_key} (currency_exchange)")
            results.append(cached_rate_info)  # cached_rate_info should be the dict we store
            continue  # Move to the next currency pair

        print(f"Cache MISS for {cache_key} (currency_exchange). Fetching for {from_currency}->{to_currency}...")
        # 3. API Call on Cache Miss
        current_pair_result = {
            "from": from_currency,
            "to": to_currency,
            "rate": None,
            "timestamp": None,
            "error": None  # Optional: to store error message if any
        }
        try:
            url = f"{base_url}&from_currency={from_currency}&to_currency={to_currency}&apikey={api_key}"
            response = requests.get(url, timeout=10, headers={"User-Agent": "python-requests"})
            response.raise_for_status()
            data = response.json()

            rate_info = data.get("Realtime Currency Exchange Rate", {})
            exchange_rate_str = rate_info.get("5. Exchange Rate")
            timestamp = rate_info.get("6. Last Refreshed")

            if exchange_rate_str:
                current_pair_result["rate"] = float(exchange_rate_str)
            current_pair_result["timestamp"] = timestamp

            # 4. Store in Cache if successful
            if current_pair_result["rate"] is not None:
                # Exchange rates can be volatile. Cache for 5-30 mins.
                cache_timeout_seconds = 60 * 15  # 15 minutes
                cache.set(cache_key, current_pair_result, timeout=cache_timeout_seconds)  # Store the whole dict
                print(f"Set cache for {cache_key} (currency_exchange) for {cache_timeout_seconds}s")

        except requests.exceptions.HTTPError as http_err:
            error_msg = f"HTTP error: {http_err}"
            print(f"{error_msg} fetching exchange rate {from_currency}->{to_currency}")
            current_pair_result["error"] = error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {e}"
            print(f"{error_msg} fetching exchange rate {from_currency}->{to_currency}")
            current_pair_result["error"] = error_msg
        except (KeyError, ValueError, TypeError) as e:
            error_msg = f"Data processing error: {e}"
            print(
                f"{error_msg} for exchange rate {from_currency}->{to_currency} - Data: {data if 'data' in locals() else 'N/A'}")
            current_pair_result["error"] = error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(f"{error_msg} fetching exchange rate {from_currency}->{to_currency}")
            current_pair_result["error"] = error_msg

        results.append(current_pair_result)

    return results


def fetch_treasury_yield(interval="monthly", maturity="10year"):  # Made params explicit
    """
    Fetch historical US Treasury Yield data from Alpha Vantage, with Redis caching.
    """
    # 1. Define Cache Key
    cache_key = f"treasury_yield_av_{maturity}_{interval}"

    # 2. Check Cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        print(f"Cache HIT for {cache_key} (treasury_yield)")
        return cached_data

    print(f"Cache MISS for {cache_key} (treasury_yield). Fetching from Alpha Vantage...")
    # 3. API Call on Cache Miss
    try:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            print("Error: ALPHA_VANTAGE_API_KEY not set.")
            return None

        url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval={interval}&maturity={maturity}&apikey={api_key}"
        response = requests.get(url, headers={"User-Agent": "python-requests"})
        response.raise_for_status()

        data = response.json()
        # Check if 'data' key exists and is not empty, common for treasury yields
        if "data" not in data or not data["data"]:
            print(f"No 'data' found or empty for treasury yield {maturity} {interval}: {data}")
            # Cache this "no data" response for a shorter period to avoid repeated failed lookups
            cache.set(cache_key, {"name": data.get("name"), "interval": data.get("interval"), "unit": data.get("unit"),
                                  "data": []}, timeout=60 * 60)  # Cache empty for 1hr
            return data  # Return the structure Alpha Vantage gives for no data

        # 4. Store in Cache
        # Treasury yields update daily/monthly. Cache for a long period.
        cache_timeout_seconds = 60 * 60 * 12  # 12 hours for monthly, maybe shorter for daily if used
        if interval == "daily":
            cache_timeout_seconds = 60 * 60 * 4  # 4 hours for daily
        cache.set(cache_key, data, timeout=cache_timeout_seconds)
        print(f"Set cache for {cache_key} (treasury_yield) for {cache_timeout_seconds}s")

        return data
    except requests.exceptions.HTTPError as http_err:
        print(
            f"HTTP error (fetch_treasury_yield for {maturity} {interval}): {http_err} - Response: {response.text if 'response' in locals() else 'N/A'}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error (fetch_treasury_yield for {maturity} {interval}): {req_err}")
        return None
    except (KeyError, ValueError, TypeError) as e:
        print(
            f"Data processing error (fetch_treasury_yield for {maturity} {interval}): {e} - Data: {data if 'data' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"Unexpected error (fetch_treasury_yield for {maturity} {interval}): {e}")
        return None


# --- Monte Carlo functions remain unchanged as they are computational ---
def monte_carlo_var_cvar(yields, num_simulations=10000, confidence_level=0.95):
    log_returns = np.diff(np.log(yields))
    mu = np.mean(log_returns)
    sigma = np.std(log_returns)
    simulated_returns = np.random.normal(mu, sigma, num_simulations)
    sorted_returns = np.sort(simulated_returns)
    var_index = int((1 - confidence_level) * num_simulations)
    var = sorted_returns[var_index]
    cvar = sorted_returns[:var_index].mean()
    return round(var, 5), round(cvar, 5)


def monte_carlo_portfolio_var_cvar(log_returns, num_simulations=10000, confidence_level=0.95):
    mu = np.mean(log_returns)
    sigma = np.std(log_returns)
    simulated_returns = np.random.normal(mu, sigma, num_simulations)
    sorted_returns = np.sort(simulated_returns)
    var_index = int((1 - confidence_level) * num_simulations)
    var = sorted_returns[var_index]
    cvar = sorted_returns[:var_index].mean()
    return round(var, 5), round(cvar, 5)


def get_market_returns(symbol="SPY", outputsize="compact"):  # Added outputsize for flexibility
    """Fetch daily returns of an ETF (e.g., SPY) from Alpha Vantage, with Redis caching."""
    # 1. Define Cache Key
    cache_key = f"market_returns_av_{symbol}_{outputsize}"

    # 2. Check Cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        print(f"Cache HIT for {cache_key} (market_returns)")
        return cached_data  # This will be the list of (datetime, return_value) tuples

    print(f"Cache MISS for {cache_key} (market_returns). Fetching for {symbol} from Alpha Vantage...")
    # 3. API Call on Cache Miss
    try:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            print("Error: ALPHA_VANTAGE_API_KEY not set.")
            return []

        # Using TIME_SERIES_DAILY_ADJUSTED for better historical accuracy
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize={outputsize}&apikey={api_key}"
        response = requests.get(url, headers={"User-Agent": "python-requests"})
        response.raise_for_status()

        data = response.json()
        time_series_data = data.get("Time Series (Daily)")  # Key is "Time Series (Daily)"

        if not time_series_data:
            print(f"No 'Time Series (Daily)' data found for {symbol} (market_returns): {data}")
            cache.set(cache_key, [], timeout=60 * 60)  # Cache empty list for 1hr for bad symbol
            return []

        # Sort dates ensuring they are actual date strings
        valid_dates = [date_str for date_str in time_series_data.keys() if isinstance(date_str, str)]
        try:
            # Attempt to sort dates, assuming YYYY-MM-DD format
            sorted_dates = sorted(valid_dates, key=lambda d: datetime.strptime(d, "%Y-%m-%d"))
        except ValueError:
            print(f"Error sorting dates for {symbol}, unexpected date format found. Dates: {valid_dates[:5]}")
            return []  # Or handle more gracefully

        # Use '5. adjusted close' for returns calculation
        prices = [float(time_series_data[date]["5. adjusted close"]) for date in sorted_dates if
                  "5. adjusted close" in time_series_data[date]]

        if len(prices) < 2:
            print(f"Not enough price points to calculate returns for {symbol}.")
            cache.set(cache_key, [], timeout=60 * 60)  # Cache empty list for 1hr
            return []

        returns_data = []
        # Iterate from the second date string in sorted_dates to align with prices
        for i in range(1, len(prices)):
            # The date for the return is the date of prices[i]
            current_date_str = sorted_dates[
                i + (len(valid_dates) - len(prices))]  # Adjust index if prices list is shorter due to missing data
            daily_return = (prices[i] - prices[i - 1]) / prices[i - 1]
            returns_data.append(
                (datetime.strptime(current_date_str, "%Y-%m-%d").date(), daily_return))  # Store date object

        # 4. Store in Cache
        # Market returns can be cached daily.
        cache_timeout_seconds = 60 * 60 * 6  # 6 hours
        cache.set(cache_key, returns_data, timeout=cache_timeout_seconds)  # Store the list of tuples
        print(f"Set cache for {cache_key} (market_returns) for {cache_timeout_seconds}s")

        return returns_data  # Original was [::-1], if you need most recent first, apply it here or in calling code
        # For consistency, usually time series data is oldest to newest.

    except requests.exceptions.HTTPError as http_err:
        print(
            f"HTTP error (get_market_returns for {symbol}): {http_err} - Response: {response.text if 'response' in locals() else 'N/A'}")
        return []
    except requests.exceptions.RequestException as req_err:
        print(f"Request error (get_market_returns for {symbol}): {req_err}")
        return []
    except (KeyError, ValueError, TypeError) as e:
        print(
            f"Data processing error (get_market_returns for {symbol}): {e} - Data: {data if 'data' in locals() else 'N/A'}")
        return []
    except Exception as e:
        print(f"Unexpected error (get_market_returns for {symbol}): {e}")
        return []


def get_treasury_yields():  # Renamed from fetch_treasury_yields for consistency with previous usage
    """Fetch latest daily Treasury yields (3m to 30y) from Alpha Vantage, with Redis caching for each maturity."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("Error: ALPHA_VANTAGE_API_KEY not set.")
        return {"date": None, "3m": 0.0, "2y": 0.0, "5y": 0.0, "7y": 0.0, "10y": 0.0,
                "30y": 0.0}  # Return default structure

    maturities_map = {
        "3m": "3month", "2y": "2year", "5y": "5year",
        "7y": "7year", "10y": "10year", "30y": "30year"
    }
    # This will store the final dict: {"date": ..., "3m": ..., "2y": ...}
    # We can cache the whole dict once all individual yields are fetched or fail.
    overall_cache_key = "treasury_yields_av_latest_daily_set"

    cached_overall_yields = cache.get(overall_cache_key)
    if cached_overall_yields is not None:
        print(f"Cache HIT for {overall_cache_key} (overall_treasury_yields)")
        return cached_overall_yields

    print(f"Cache MISS for {overall_cache_key} (overall_treasury_yields). Fetching individual maturities...")

    # Initialize results with default values
    yields_result = {"date": None}
    for short_name in maturities_map.keys():
        yields_result[short_name] = 0.0  # Default to float

    # Fetch each maturity, potentially using individual caches if desired,
    # but for one combined call, we'll just fetch all then cache the combined result.
    # For simplicity, this example will refetch all if the combined cache is missed.
    # A more advanced version could cache each maturity's latest value individually.

    all_maturities_fetched_successfully = True

    for short_name, api_maturity_name in maturities_map.items():
        # Individual cache key for each maturity's latest daily value
        individual_cache_key = f"treasury_yield_av_latest_daily_{api_maturity_name}"

        cached_individual_yield = cache.get(individual_cache_key)
        if cached_individual_yield is not None:
            print(f"Cache HIT for individual maturity {individual_cache_key}")
            if not yields_result["date"] and cached_individual_yield.get("date"):
                yields_result["date"] = cached_individual_yield["date"]  # Use date from first valid cached entry
            yields_result[short_name] = cached_individual_yield.get("value", 0.0)
            continue  # Next maturity

        print(f"Cache MISS for individual maturity {individual_cache_key}. Fetching {api_maturity_name}...")
        try:
            url = f"https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=daily&maturity={api_maturity_name}&apikey={api_key}"
            response = requests.get(url, headers={"User-Agent": "python-requests"}, timeout=10)
            response.raise_for_status()

            data = response.json()
            api_data_list = data.get("data", [])

            if not api_data_list:
                print(f"No treasury data found for {api_maturity_name} from API.")
                # yields_result[short_name] remains 0.0
                # Cache this "no data" state for the individual maturity
                cache.set(individual_cache_key, {"date": None, "value": 0.0}, timeout=60 * 60)  # Cache no data for 1hr
                all_maturities_fetched_successfully = False  # Mark if any maturity fails
                continue

            latest_entry = api_data_list[0]  # Get the most recent entry
            current_date_str = latest_entry.get("date")
            current_value_str = latest_entry.get("value")

            if current_value_str == ".":  # Alpha Vantage sometimes returns "." for missing data
                print(f"Missing value ('.') for treasury yield {api_maturity_name} on {current_date_str}")
                current_value_float = 0.0  # Default to 0.0 or handle as error
            else:
                current_value_float = float(current_value_str)

            if not yields_result["date"] and current_date_str:
                try:
                    yields_result["date"] = datetime.strptime(current_date_str, "%Y-%m-%d").date()
                except ValueError:
                    print(f"Invalid date format for {api_maturity_name}: {current_date_str}")
                    yields_result["date"] = None  # Or keep it None

            yields_result[short_name] = current_value_float

            # Cache the individual successful fetch
            individual_data_to_cache = {"date": yields_result["date"], "value": current_value_float}
            cache.set(individual_cache_key, individual_data_to_cache, timeout=60 * 60 * 4)  # Cache individual for 4hrs

        except Exception as e:
            print(f"Error fetching Treasury yield for {api_maturity_name}: {e}")
            # yields_result[short_name] remains 0.0
            all_maturities_fetched_successfully = False  # Mark if any maturity fails

    # After attempting to fetch all maturities, cache the combined result
    # Cache duration depends on success. If all successful, cache longer.
    overall_cache_timeout = 60 * 60 * 4  # Default 4 hours
    if not all_maturities_fetched_successfully:
        overall_cache_timeout = 60 * 30  # Shorter cache if some parts failed, e.g., 30 mins

    cache.set(overall_cache_key, yields_result, timeout=overall_cache_timeout)
    print(
        f"Set cache for {overall_cache_key} (overall_treasury_yields) for {overall_cache_timeout}s. Data: {yields_result}")

    return yields_result


# ============================================================================
# PERFORMANCE OPTIMIZATION UTILITIES
# ============================================================================

class PortfolioDataOptimizer:
    """Optimized data fetching and processing for portfolios"""

    @staticmethod
    def get_optimized_portfolio(portfolio_id, user):
        """Fetch portfolio with optimized queries using select_related and prefetch_related"""
        from portfolio.models import Portfolio, Stock

        return Portfolio.objects.select_related(
            'fund_manager',
            'fund_manager__user',
            'fund_manager__institute'
        ).prefetch_related(
            Prefetch('stocks', queryset=Stock.objects.order_by('-added_at'))
        ).get(id=portfolio_id, fund_manager__user=user)

    @staticmethod
    def get_portfolio_stocks_data(portfolio):
        """Calculate stock data with optimized queries"""
        from decimal import Decimal

        stocks = portfolio.stocks.select_related('portfolio').all()
        stock_data = []
        total_value = Decimal('0.00')

        for stock in stocks:
            manual_price = stock.price
            live_price = stock.get_live_price()
            price = manual_price if manual_price else (Decimal(str(live_price)) if live_price else None)

            if price:
                stock_total = price * stock.quantity
                total_value += stock_total
                stock_data.append({
                    'name': stock.name,
                    'symbol': stock.symbol,
                    'quantity': stock.quantity,
                    'manual_price': float(manual_price) if manual_price else None,
                    'live_price': live_price,
                    'total_value': float(stock_total),
                })

        return stock_data, float(total_value)

    @staticmethod
    def get_historical_data_cached(portfolio_id):
        """Get historical data with caching"""
        cache_key = f'historical_data_portfolio_{portfolio_id}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        from portfolio.models import HistoricalStockData

        historical_prices_qs = HistoricalStockData.objects.filter(
            portfolio_id=portfolio_id
        ).values('date', 'symbol', 'adjusted_close').order_by('date')

        if historical_prices_qs.exists():
            df = pd.DataFrame.from_records(historical_prices_qs)
            cache_data = {'dataframe': df, 'exists': True}
        else:
            cache_data = {'dataframe': pd.DataFrame(), 'exists': False}

        cache.set(cache_key, cache_data, timeout=60 * 15)
        return cache_data


class CacheManager:
    """Centralized cache management"""

    TIMEOUTS = {
        'historical_data': 60 * 15,
        'efficient_frontier': 60 * 30,
        'live_price': 60 * 60,
        'portfolio_analysis': 60 * 10,
        'dashboard_data': 60 * 5,
    }

    @staticmethod
    def invalidate_portfolio_cache(portfolio_id):
        """Invalidate all caches related to a portfolio"""
        keys = [
            f'historical_data_portfolio_{portfolio_id}',
            f'efficient_frontier_portfolio_{portfolio_id}',
            f'portfolio_analysis_{portfolio_id}',
        ]
        cache.delete_many(keys)
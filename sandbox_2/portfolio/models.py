# portfolio/models.py

from django.db import models
import requests
import os
from django.contrib.auth.models import User
from django.utils.timezone import now # Not directly used in caching examples here but good for general use
from datetime import datetime
from django.core.cache import cache # <<--- IMPORT THIS AT THE TOP

# --- Model Definitions ---

class Institute(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FundManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, related_name="fund_managers")

    def __str__(self):
        return self.user.username


class Portfolio(models.Model):
    name = models.CharField(max_length=255)
    fund_manager = models.ForeignKey(FundManager, on_delete=models.CASCADE, related_name="portfolios")
    created_at = models.DateTimeField(auto_now_add=True)
    # Optional: Add an updated_at field for easier cache invalidation later if needed for portfolio-level caches
    # updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.fund_manager.user.username})"


class Stock(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="stocks")
    symbol = models.CharField(max_length=10)  # Stock ticker symbol
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # Manual price
    added_at = models.DateTimeField(auto_now_add=True)
    # Optional: Add an updated_at field if needed for fine-grained cache invalidation
    # updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"

    def get_live_price(self):
        """Fetch the live price from Alpha Vantage, with Redis caching."""

        # 1. Define a unique cache key
        cache_key = f"live_price_alphavantage_{self.symbol}"

        # 2. Try to get from cache
        cached_price = cache.get(cache_key)
        if cached_price is not None:
            print(f"Cache HIT for {cache_key}: {cached_price}")
            return float(cached_price)

        print(f"Cache MISS for {cache_key}. Fetching live price from Alpha Vantage...")
        # 3. If not in cache, fetch from API
        try:
            api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
            if not api_key:
                print("Error: ALPHA_VANTAGE_API_KEY not set.")
                return None

            # Using GLOBAL_QUOTE is more efficient for the latest price
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={self.symbol}&apikey={api_key}"
            response = requests.get(url, headers={"User-Agent": "python-requests"})
            response.raise_for_status() # Raises HTTPError for bad responses

            data = response.json()
            global_quote_data = data.get("Global Quote")

            if not global_quote_data:
                print(f"No 'Global Quote' data found for {self.symbol} in API response: {data}")
                return None

            price_str = global_quote_data.get("05. price")
            if price_str is None:
                print(f"No '05. price' field in 'Global Quote' for {self.symbol}: {global_quote_data}")
                return None

            live_price_value = float(price_str)

            # 4. Store in cache
            # Alpha Vantage free tier: 25 calls/day (new limit as of recent changes).
            # Cache for a longer duration, e.g., 1 hour (3600s) or more.
            cache_timeout_seconds = 60 * 60 # Cache for 1 hour
            cache.set(cache_key, live_price_value, timeout=cache_timeout_seconds)
            print(f"Set cache for {cache_key} with value {live_price_value} for {cache_timeout_seconds}s")

            return live_price_value

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error (get_live_price for {self.symbol}): {http_err} - Response: {response.text if 'response' in locals() else 'N/A'}")
            return None
        except requests.exceptions.RequestException as req_err:
            print(f"Request error (get_live_price for {self.symbol}): {req_err}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            print(f"Data processing error (get_live_price for {self.symbol}): {e} - Data: {data if 'data' in locals() else 'N/A'}")
            return None
        except Exception as e:
            print(f"Unexpected error (get_live_price for {self.symbol}): {e}")
            return None

    def fetch_and_store_historical_data(self):
        """
        Fetch and store historical data from Alpha Vantage,
        using Redis to avoid re-fetching too frequently.
        """
        # 1. Define a cache key to track recent successful fetches for this stock
        # (Assuming historical data is global per symbol, not per portfolio for fetching purposes,
        # but stored per portfolio in DB)
        cache_key_fetch_tracker = f"historical_data_api_fetched_{self.symbol}"

        # 2. Check if we've recently fetched this data from API
        if cache.get(cache_key_fetch_tracker):
            print(f"Cache HIT for {cache_key_fetch_tracker}: API call for historical data for {self.symbol} was made recently. Assuming DB is up-to-date or will be updated by another process if necessary.")
            # This doesn't mean data is fully in DB, just that API call was made recently.
            # You might still want to check DB for specific dates if needed by calling code.
            return True # Indicate API call was skipped due to recent fetch

        print(f"Cache MISS for {cache_key_fetch_tracker}: Attempting API call for historical data for {self.symbol}.")
        # 3. If not recently called API, fetch from API
        try:
            api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
            if not api_key:
                print("Error: ALPHA_VANTAGE_API_KEY not set.")
                return False

            # Using TIME_SERIES_DAILY_ADJUSTED is generally better for historical analysis
            # as it accounts for splits and dividends.
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={self.symbol}&outputsize=full&apikey={api_key}"
            response = requests.get(url, headers={"User-Agent": "python-requests"})
            response.raise_for_status()

            data = response.json()
            time_series_data = data.get("Time Series (Daily)") # Key is "Time Series (Daily)" even for ADJUSTED

            if not time_series_data:
                print(f"No 'Time Series (Daily)' data found for {self.symbol} via API: {data}")
                # Cache that this symbol might be problematic or has no data via API
                cache.set(f"historical_data_api_not_found_{self.symbol}", True, timeout=60*60*24) # Cache "not found" for 1 day
                return False

            records_processed_count = 0
            for date_str, values in time_series_data.items():
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                    # Use "5. adjusted close" for TIME_SERIES_DAILY_ADJUSTED
                    adjusted_close_str = values.get("5. adjusted close")
                    if adjusted_close_str is None:
                        print(f"Warning: '5. adjusted close' missing for {self.symbol} on {date_str}. Data: {values}")
                        continue

                    adjusted_close_val = float(adjusted_close_str)

                    HistoricalStockData.objects.update_or_create(
                        portfolio=self.portfolio, # Storing per portfolio
                        symbol=self.symbol,
                        date=date_obj,
                        defaults={"adjusted_close": adjusted_close_val}
                    )
                    records_processed_count += 1
                except (ValueError, TypeError) as ve:
                    print(f"Error processing record (fetch_and_store_historical_data for {self.symbol} on {date_str}): {ve}")
                    continue

            if records_processed_count > 0:
                print(f"Successfully stored/updated {records_processed_count} historical records for {self.symbol} in portfolio {self.portfolio.id}.")
                # 4. If API call and DB store were successful, set the API fetch tracker cache marker
                # Cache for a longer period, e.g., 12-24 hours, as historical data updates less frequently.
                cache_timeout_seconds = 60 * 60 * 12 # Cache for 12 hours
                cache.set(cache_key_fetch_tracker, True, timeout=cache_timeout_seconds)
                print(f"Set API fetch tracker cache for {cache_key_fetch_tracker} for {cache_timeout_seconds}s.")
                return True
            else:
                print(f"No new valid historical records processed from API for {self.symbol}.")
                # If API call was successful but no new data, still mark API as called to avoid immediate refetch
                cache.set(cache_key_fetch_tracker, True, timeout=60 * 60 * 1) # Shorter timeout, e.g. 1 hour
                return False # Or True, depending on desired outcome

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error (fetch_and_store_historical_data for {self.symbol}): {http_err} - Response: {response.text if 'response' in locals() else 'N/A'}")
            return False
        except requests.exceptions.RequestException as req_err:
            print(f"Request error (fetch_and_store_historical_data for {self.symbol}): {req_err}")
            return False
        except (KeyError, ValueError, TypeError) as e:
            print(f"Data processing error (fetch_and_store_historical_data for {self.symbol}): {e} - Data: {data if 'data' in locals() else 'N/A'}")
            return False
        except Exception as e:
            print(f"Unexpected error (fetch_and_store_historical_data for {self.symbol}): {e}")
            return False

    def get_total_value(self):
        """Calculate the total value of the stock. Live price fetching is cached."""
        if self.price:  # Use manually entered price if available
            return self.price * self.quantity
        # get_live_price() now uses Redis cache internally
        live_price = self.get_live_price()
        if live_price is not None: # Check for None, as get_live_price can return None
            return float(live_price) * self.quantity # Ensure live_price is float for multiplication
        return 0 # Or handle as an error/None if price is unavailable


class HistoricalStockData(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="historical_data")
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    adjusted_close = models.FloatField() # Consider DecimalField for precision if needed

    class Meta:
        unique_together = ('portfolio', 'symbol', 'date')
        ordering = ['date'] # Good for fetching ordered data

    def __str__(self):
        return f"{self.portfolio.name} - {self.symbol} - {self.date}: {self.adjusted_close}"


# --- Standalone Function for News Sentiment ---

def fetch_news_sentiment(symbol="AAPL", limit=10):
    """Fetch latest news sentiment data from Alpha Vantage, with Redis caching."""

    # 1. Define a unique cache key based on parameters
    # Using a fixed limit for simplicity here, if limit changes often, include it in key
    cache_key = f"news_sentiment_alphavantage_{symbol}_limit{limit}"

    # 2. Try to get from cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        print(f"Cache HIT for {cache_key}")
        return cached_data # This will be the list of feed items

    print(f"Cache MISS for {cache_key}. Fetching news sentiment for {symbol} from Alpha Vantage...")
    # 3. If not in cache, fetch from API
    try:
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            print("Error: ALPHA_VANTAGE_API_KEY not set.")
            return []

        url = (
            f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
            f"&tickers={symbol}&limit={limit}&sort=LATEST&apikey={api_key}"
        )
        response = requests.get(url, headers={"User-Agent": "python-requests"})
        response.raise_for_status()

        data = response.json()
        feed_data = data.get("feed", []) # Default to empty list if 'feed' key is missing

        # 4. Store in cache
        # News sentiment might update frequently, but API limits are strict.
        # Cache for 30 minutes to 1 hour.
        cache_timeout_seconds = 60 * 30 # Cache for 30 minutes
        cache.set(cache_key, feed_data, timeout=cache_timeout_seconds)
        print(f"Set cache for {cache_key} for {cache_timeout_seconds}s")

        return feed_data

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error (fetch_news_sentiment for {symbol}): {http_err} - Response: {response.text if 'response' in locals() else 'N/A'}")
        return []
    except requests.exceptions.RequestException as req_err:
        print(f"Request error (fetch_news_sentiment for {symbol}): {req_err}")
        return []
    except (KeyError, ValueError, TypeError) as e: # JSON parsing or structure issues
        print(f"Data processing error (fetch_news_sentiment for {symbol}): {e} - Data: {data if 'data' in locals() else 'N/A'}")
        return []
    except Exception as e:
        print(f"Unexpected error (fetch_news_sentiment for {symbol}): {e}")
        return []
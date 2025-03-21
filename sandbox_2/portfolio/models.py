from django.db import models
import requests
import os
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import datetime


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

    def __str__(self):
        return f"{self.name} ({self.fund_manager.user.username})"


class Stock(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="stocks")
    symbol = models.CharField(max_length=10)  # Stock ticker symbol
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)  # Number of shares owned
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Manually entered price
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"

    def get_live_price(self):
        """Fetch the live price from Alpha Vantage."""
        try:
            api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={self.symbol}&outputsize=full&apikey={api_key}"
            response = requests.get(url, headers={"User-Agent": "python-requests"})

            if response.status_code != 200:
                print(f"Alpha Vantage error: {response.status_code}")
                return None

            data = response.json()
            time_series = data.get("Time Series (Daily)")

            if not time_series:
                print(f"No time series data found for {self.symbol}")
                return None

            latest_date = sorted(time_series.keys(), reverse=True)[0]
            stock_data = time_series[latest_date]
            return float(stock_data["4. close"])
        except Exception as e:
            print(f"Error fetching price for {self.symbol}: {e}")
            return None

    def fetch_and_store_historical_data(self):
        """Fetch and store historical data from Alpha Vantage."""
        try:
            api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={self.symbol}&outputsize=full&apikey={api_key}"
            response = requests.get(url, headers={"User-Agent": "python-requests"})
            response.raise_for_status()
            data = response.json().get("Time Series (Daily)", {})

            if not data:
                print(f"No historical data for {self.symbol}")
                return False

            for date_str, values in data.items():
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                adjusted_close = float(values["4. close"])
                HistoricalStockData.objects.update_or_create(
                    portfolio=self.portfolio,
                    symbol=self.symbol,
                    date=date,
                    defaults={"adjusted_close": adjusted_close}
                )
            print(f"Stored historical data for {self.symbol}")
            return True
        except Exception as e:
            print(f"Error fetching historical data for {self.symbol}: {e}")
            return False

    def get_total_value(self):
        """Calculate the total value of the stock."""
        if self.price:  # Use manually entered price if available
            return self.price * self.quantity
        live_price = self.get_live_price()  # Fallback to live price
        if live_price:
            return live_price * self.quantity
        return 0


class HistoricalStockData(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="historical_data")
    symbol = models.CharField(max_length=10)  # Stock ticker
    date = models.DateField()  # Date of the stock price
    adjusted_close = models.FloatField()  # Adjusted closing price

    class Meta:
        unique_together = ('portfolio', 'symbol', 'date')  # Ensure unique data per portfolio

    def __str__(self):
        return f"{self.portfolio.name} - {self.symbol} - {self.date}: {self.adjusted_close}"
from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.db import models
import yfinance as yf
from django.utils.timezone import now

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
        """Fetch the live price from Yahoo Finance."""
        try:
            stock_data = yf.Ticker(self.symbol)
            return stock_data.info.get('regularMarketPrice', None)
        except Exception as e:
            print(f"Error fetching price for {self.symbol}: {e}")
            return None

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
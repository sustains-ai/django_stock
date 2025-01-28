from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.db import models

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

import yfinance as yf

class Stock(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="stocks")
    symbol = models.CharField(max_length=10)  # Stock ticker symbol
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)  # Number of shares owned
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
        """Calculate the total value of the stock based on live price."""
        live_price = self.get_live_price()
        if live_price:
            return live_price * self.quantity
        return 0


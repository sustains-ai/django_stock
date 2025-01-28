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

class Stock(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="stocks")
    symbol = models.CharField(max_length=10)  # Stock ticker symbol
    name = models.CharField(max_length=255)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"
